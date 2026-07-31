from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from app.backtester.metrics import SimTrade, build_metrics
from app.services.historical_download_service import WARMUP_BARS
from app.strategies.evaluator import StrategyEvaluator
from app.strategies.scalp_management import (
    build_risk_levels,
    check_intrabar_exit,
    check_management_exit,
    is_fresh_bb_touch,
    management_from_definition,
)


@dataclass
class BacktestOutput:
    metrics: dict[str, Any]
    markers: list[dict[str, Any]]
    candles: list[dict[str, Any]]


class BacktestEngine:
    """Simulate long/short trades from strategy signals on historical OHLCV."""

    def __init__(self) -> None:
        self.evaluator = StrategyEvaluator()

    def run(self, df: pd.DataFrame, definition: dict[str, Any], timeframe: str) -> BacktestOutput:
        if len(df) < WARMUP_BARS + 5:
            raise ValueError("Not enough historical candles for backtest warmup")

        work = df.copy()
        for col in ("open", "high", "low", "close", "volume"):
            if col in work.columns:
                work[col] = pd.to_numeric(work[col], errors="coerce")
        work = work.dropna(subset=["open", "high", "low", "close"])
        if len(work) < WARMUP_BARS + 5:
            raise ValueError("Not enough numeric candles for backtest warmup")

        enriched = self.evaluator._enrich_dataframe(work, definition)
        mgmt = management_from_definition(definition)
        entry_fill = str(mgmt.get("entry_fill", "close")).lower()
        cooldown_bars = int(mgmt.get("cooldown_bars") or 0)
        cooldown_after = str(mgmt.get("cooldown_after", "loss")).lower()
        fresh_bb = bool(mgmt.get("fresh_bb_touch"))

        position: str | None = None
        entry_price = 0.0
        entry_index = 0
        entry_time = ""
        stop_price: float | None = None
        take_price: float | None = None
        pending_signal: str | None = None
        pending_signal_index = -1
        cooldown_until = -1

        trades: list[SimTrade] = []
        markers: list[dict[str, Any]] = []
        buy_signals = 0
        sell_signals = 0

        equity = 10_000.0
        equity_curve: list[dict[str, Any]] = []
        drawdown_curve: list[dict[str, Any]] = []
        peak = equity

        start_idx = WARMUP_BARS
        end_idx = len(enriched) - 1

        def close_position(exit_i: int, exit_price: float) -> None:
            nonlocal position, equity, peak, cooldown_until, stop_price, take_price
            if position is None:
                return
            exit_time = enriched.index[exit_i].isoformat()
            trade = self._close_trade(
                position, entry_time, exit_time, entry_price, exit_price, entry_index, exit_i
            )
            trades.append(trade)
            if cooldown_bars > 0:
                if cooldown_after == "any" or trade.pnl_pct <= 0:
                    cooldown_until = exit_i + cooldown_bars
            position = None
            stop_price = None
            take_price = None

        def open_position(side: str, fill_i: int, fill_price: float, signal_i: int) -> None:
            nonlocal position, entry_price, entry_index, entry_time, stop_price, take_price
            position = side
            entry_price = fill_price
            entry_index = fill_i
            entry_time = enriched.index[fill_i].isoformat()
            signal_type = "BUY" if side == "long" else "SELL"
            stop_price, take_price = build_risk_levels(
                signal_type, fill_price, enriched, definition, signal_i
            )

        for i in range(start_idx, end_idx):
            ts = enriched.index[i]
            price = float(enriched["close"].iloc[i])
            high = float(enriched["high"].iloc[i])
            low = float(enriched["low"].iloc[i])
            open_px = float(enriched["open"].iloc[i])
            time_str = ts.isoformat()

            # Fill pending next-open entries at this bar's open
            if pending_signal and i == pending_signal_index + 1 and position is None and i > cooldown_until:
                side = "long" if pending_signal == "BUY" else "short"
                open_position(side, i, open_px, pending_signal_index)
                pending_signal = None

            # Manage open trade: SL/TP first (intrabar), then management exits
            if position is not None:
                reason, exit_px = check_intrabar_exit(position, high, low, stop_price, take_price)
                if reason and exit_px is not None:
                    close_position(i, float(exit_px))
                else:
                    reason, exit_px = check_management_exit(
                        side=position,
                        df=enriched,
                        bar_idx=i,
                        entry_index=entry_index,
                        entry_price=entry_price,
                        definition=definition,
                    )
                    if reason and exit_px is not None:
                        close_position(i, float(exit_px))

            result = self.evaluator.evaluate_at_index(enriched, definition, i, pre_enriched=True)
            signal = result.signal_type

            if signal == "BUY":
                buy_signals += 1
                markers.append({"time": time_str, "type": "buy", "price": price})
            elif signal == "SELL":
                sell_signals += 1
                markers.append({"time": time_str, "type": "sell", "price": price})

            if signal and fresh_bb and not is_fresh_bb_touch(
                enriched, i, "long" if signal == "BUY" else "short"
            ):
                signal = None

            # Opposite signal closes current position
            if position == "long" and signal == "SELL":
                close_position(i, price)
            elif position == "short" and signal == "BUY":
                close_position(i, price)

            # New entries only when flat and off cooldown
            if signal and position is None and i > cooldown_until:
                if entry_fill == "next_open":
                    pending_signal = signal
                    pending_signal_index = i
                else:
                    open_position("long" if signal == "BUY" else "short", i, price, i)

            if trades:
                equity = self._equity_from_trades(trades, initial=10_000.0)
            peak = max(peak, equity)
            dd = ((peak - equity) / peak * 100) if peak else 0.0
            equity_curve.append({"time": time_str, "equity": round(equity, 2)})
            drawdown_curve.append({"time": time_str, "drawdown_pct": round(dd, 4)})

        if position is not None:
            last_i = end_idx - 1
            last_price = float(enriched["close"].iloc[last_i])
            close_position(last_i, last_price)

        if trades:
            equity = self._equity_from_trades(trades, initial=10_000.0)
            if equity_curve:
                equity_curve[-1]["equity"] = round(equity, 2)

        metrics = build_metrics(trades, equity_curve, drawdown_curve, buy_signals, sell_signals)
        candles = self._serialize_candles(enriched.iloc[start_idx:end_idx])
        metrics["markers"] = markers
        metrics["candles"] = candles
        return BacktestOutput(metrics=metrics, markers=markers, candles=candles)

    @staticmethod
    def _close_trade(
        side: str,
        entry_time: str,
        exit_time: str,
        entry_price: float,
        exit_price: float,
        entry_index: int,
        exit_index: int,
    ) -> SimTrade:
        if side == "long":
            pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        else:
            pnl_pct = ((entry_price - exit_price) / entry_price) * 100
        return SimTrade(
            side=side,
            entry_time=entry_time,
            exit_time=exit_time,
            entry_price=entry_price,
            exit_price=exit_price,
            pnl_pct=round(pnl_pct, 4),
            duration_bars=max(exit_index - entry_index, 1),
        )

    @staticmethod
    def _equity_from_trades(trades: list[SimTrade], initial: float) -> float:
        equity = initial
        for trade in trades:
            equity *= 1 + (trade.pnl_pct / 100)
        return equity

    @staticmethod
    def _serialize_candles(df: pd.DataFrame) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for ts, row in df.iterrows():
            rows.append(
                {
                    "time": ts.isoformat(),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                }
            )
        return rows
