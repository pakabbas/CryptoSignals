from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from app.backtester.metrics import SimTrade, build_metrics
from app.services.historical_download_service import WARMUP_BARS
from app.strategies.evaluator import StrategyEvaluator


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
        position: str | None = None
        entry_price = 0.0
        entry_index = 0
        entry_time = ""
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

        for i in range(start_idx, end_idx):
            ts = enriched.index[i]
            price = float(enriched["close"].iloc[i])
            time_str = ts.isoformat()
            result = self.evaluator.evaluate_at_index(enriched, definition, i, pre_enriched=True)

            if result.signal_type == "BUY":
                buy_signals += 1
                markers.append({"time": time_str, "type": "buy", "price": price})
                if position == "short":
                    trades.append(
                        self._close_trade("short", entry_time, time_str, entry_price, price, entry_index, i)
                    )
                    position = None
                if position is None:
                    position = "long"
                    entry_price = price
                    entry_index = i
                    entry_time = time_str

            elif result.signal_type == "SELL":
                sell_signals += 1
                markers.append({"time": time_str, "type": "sell", "price": price})
                if position == "long":
                    trades.append(
                        self._close_trade("long", entry_time, time_str, entry_price, price, entry_index, i)
                    )
                    position = None
                if position is None:
                    position = "short"
                    entry_price = price
                    entry_index = i
                    entry_time = time_str

            if trades:
                equity = self._equity_from_trades(trades, initial=10_000.0)
            peak = max(peak, equity)
            dd = ((peak - equity) / peak * 100) if peak else 0.0
            equity_curve.append({"time": time_str, "equity": round(equity, 2)})
            drawdown_curve.append({"time": time_str, "drawdown_pct": round(dd, 4)})

        if position == "long":
            last_i = end_idx - 1
            last_price = float(enriched["close"].iloc[last_i])
            last_time = enriched.index[last_i].isoformat()
            trades.append(
                self._close_trade("long", entry_time, last_time, entry_price, last_price, entry_index, last_i)
            )
        elif position == "short":
            last_i = end_idx - 1
            last_price = float(enriched["close"].iloc[last_i])
            last_time = enriched.index[last_i].isoformat()
            trades.append(
                self._close_trade("short", entry_time, last_time, entry_price, last_price, entry_index, last_i)
            )

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
