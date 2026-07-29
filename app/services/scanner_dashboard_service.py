from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from app.models import Coin, Strategy
from app.scanner.candle_utils import (
    last_closed_bar_index,
    next_candle_close_utc,
)
from app.utils.cache import scanner_dashboard_cache
from app.services.coin_service import CoinService
from app.services.exchange_service import exchange_service_for_settings
from app.services.settings_service import SettingsService
from app.services.strategy_service import StrategyService
from app.strategies.evaluator import DetailedEvaluation, SideStatus, StrategyEvaluator
from app.utils.logging_setup import get_logger

logger = get_logger("scanner")


@dataclass
class CoinTicker:
    coin_id: int
    symbol: str
    price: float | None
    change_pct: float | None
    volume: float | None
    timeframe: str
    last_candle: datetime | None
    sparkline: list[float] = field(default_factory=list)
    sparkline_points: str = ""
    error: str | None = None


@dataclass
class StrategyLiveView:
    strategy_id: int
    strategy_name: str
    coin_symbol: str
    timeframe: str
    enabled: bool
    price: float | None
    signal_type: str | None
    long: SideStatus | None
    short: SideStatus | None
    next_close_at: datetime | None
    evaluated_at: datetime | None
    indicator_values: dict[str, float]
    error: str | None = None


class ScannerDashboardService:
    """Live market + per-rule strategy progress for the scanner UI."""

    def __init__(self) -> None:
        self.exchange = exchange_service_for_settings()
        self.evaluator = StrategyEvaluator()
        self.coins = CoinService()
        self.strategies = StrategyService()
        self.settings = SettingsService()

    def build(self, market_timeframe: str | None = None) -> tuple[list[CoinTicker], list[StrategyLiveView]]:
        if os.getenv("TESTING", "").lower() in {"1", "true", "yes"}:
            return [], []

        now = datetime.now(timezone.utc)
        from app.config.timeframes import normalize_timeframe

        default_tf = normalize_timeframe(
            market_timeframe or self.settings.get("default_timeframe", "1H")
        )
        cache_key = f"live:{default_tf}"
        cached = scanner_dashboard_cache.get(cache_key)
        if cached is not None:
            return cached

        enabled_coins = [c for c in self.coins.list_coins() if c.enabled]
        ohlcv_cache: dict[tuple[int, str], pd.DataFrame] = {}
        enriched_cache: dict[tuple[int, int], pd.DataFrame] = {}

        tickers: list[CoinTicker] = []
        for coin in enabled_coins:
            tickers.append(self._coin_ticker(coin, default_tf, ohlcv_cache, now))

        views: list[StrategyLiveView] = []
        all_enabled = self.strategies.list_enabled()
        for coin in enabled_coins:
            assigned = self.strategies.list_enabled_for_coin(coin.id)
            coin_strategies = assigned if assigned else all_enabled
            for strategy in coin_strategies:
                views.append(
                    self._strategy_view(coin, strategy, ohlcv_cache, enriched_cache, now)
                )

        views.sort(
            key=lambda v: (
                0 if v.signal_type else 1,
                -(
                    (v.long.met_count if v.long else 0)
                    + (v.short.met_count if v.short else 0)
                ),
                v.strategy_name,
            )
        )
        result = (tickers, views)
        scanner_dashboard_cache.set(cache_key, result)
        return result

    def _get_df(self, coin: Coin, timeframe: str, cache: dict[tuple[int, str], pd.DataFrame]) -> pd.DataFrame:
        key = (coin.id, timeframe)
        if key in cache:
            return cache[key]
        df = self.exchange.fetch_ohlcv_dataframe(coin.symbol, timeframe, limit=300)
        cache[key] = df
        return df

    def _coin_ticker(
        self,
        coin: Coin,
        timeframe: str,
        cache: dict[tuple[int, str], pd.DataFrame],
        now: datetime,
    ) -> CoinTicker:
        try:
            df = self._get_df(coin, timeframe, cache)
            if df.empty or len(df) < 2:
                raise ValueError("Not enough candles")
            last_idx = len(df) - 1
            price = float(df["close"].iloc[last_idx])
            prev = float(df["close"].iloc[last_idx - 1])
            change_pct = ((price - prev) / prev * 100) if prev else None
            vol = float(df["volume"].iloc[last_idx])
            ts = df.index[last_idx].to_pydatetime()
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            spark = [float(v) for v in df["close"].iloc[-24:].tolist()]
            return CoinTicker(
                coin_id=coin.id,
                symbol=coin.symbol,
                price=price,
                change_pct=change_pct,
                volume=vol,
                timeframe=timeframe,
                last_candle=ts,
                sparkline=spark,
                sparkline_points=_sparkline_points(spark),
            )
        except Exception as exc:
            logger.warning("Ticker failed for %s: %s", coin.symbol, exc)
            return CoinTicker(
                coin_id=coin.id,
                symbol=coin.symbol,
                price=None,
                change_pct=None,
                volume=None,
                timeframe=timeframe,
                last_candle=None,
                error=str(exc),
            )

    def _strategy_view(
        self,
        coin: Coin,
        strategy: Strategy,
        cache: dict[tuple[int, str], pd.DataFrame],
        enriched_cache: dict[tuple[int, int], pd.DataFrame],
        now: datetime,
    ) -> StrategyLiveView:
        tf = strategy.timeframe or self.settings.get("default_timeframe", "1H")
        if not strategy.enabled:
            return StrategyLiveView(
                strategy_id=strategy.id,
                strategy_name=strategy.name,
                coin_symbol=coin.symbol,
                timeframe=tf,
                enabled=False,
                price=None,
                signal_type=None,
                long=None,
                short=None,
                next_close_at=None,
                evaluated_at=None,
                indicator_values={},
            )
        try:
            df = self._get_df(coin, tf, cache)
            if df.empty or len(df) < 3:
                raise ValueError("Not enough candle data")
            ekey = (coin.id, strategy.id)
            if ekey not in enriched_cache:
                enriched_cache[ekey] = self.evaluator._enrich_dataframe(
                    df, strategy.definition_json
                )
            enriched = enriched_cache[ekey]
            bar_idx = last_closed_bar_index(list(enriched.index.to_pydatetime()), tf, now)
            detail = self.evaluator.evaluate_detailed_at_index(
                enriched, strategy.definition_json, bar_idx, pre_enriched=True
            )
            last_open = df.index[-1].to_pydatetime()
            if last_open.tzinfo is None:
                last_open = last_open.replace(tzinfo=timezone.utc)
            next_close = next_candle_close_utc(last_open, tf, now)
            eval_ts = detail.candle_time.to_pydatetime()
            if eval_ts.tzinfo is None:
                eval_ts = eval_ts.replace(tzinfo=timezone.utc)
            return StrategyLiveView(
                strategy_id=strategy.id,
                strategy_name=strategy.name,
                coin_symbol=coin.symbol,
                timeframe=tf,
                enabled=True,
                price=detail.price,
                signal_type=detail.signal_type,
                long=detail.long,
                short=detail.short,
                next_close_at=next_close,
                evaluated_at=eval_ts,
                indicator_values=detail.indicator_values,
            )
        except Exception as exc:
            logger.warning(
                "Live view failed coin=%s strategy=%s: %s",
                coin.symbol,
                strategy.name,
                exc,
            )
            return StrategyLiveView(
                strategy_id=strategy.id,
                strategy_name=strategy.name,
                coin_symbol=coin.symbol,
                timeframe=tf,
                enabled=True,
                price=None,
                signal_type=None,
                long=None,
                short=None,
                next_close_at=None,
                evaluated_at=None,
                indicator_values={},
                error=str(exc),
            )

    @staticmethod
    def side_progress(side: SideStatus | None) -> dict[str, Any]:
        if not side or side.total == 0:
            return {"met": 0, "total": 0, "pct": 0, "pending": 0, "triggered": False, "logic": "AND"}
        pending = side.total - side.met_count
        pct = int(round(side.met_count / side.total * 100))
        return {
            "met": side.met_count,
            "total": side.total,
            "pending": pending,
            "pct": pct,
            "triggered": side.triggered,
            "logic": side.logic,
        }


def _sparkline_points(values: list[float]) -> str:
    if len(values) < 2:
        return ""
    mn = min(values)
    mx = max(values)
    span = mx - mn if mx != mn else 1.0
    pts: list[str] = []
    for i, v in enumerate(values):
        x = (i / (len(values) - 1)) * 120
        y = 38 - ((v - mn) / span) * 36
        pts.append(f"{x:.2f},{y:.2f}")
    return " ".join(pts)
