from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pandas as pd

from app.exchanges.registry import create_ccxt_exchange, normalize_exchange_id
from app.scanner.candle_utils import to_ccxt_timeframe
from app.services.settings_service import SettingsService
from app.utils.cache import ohlcv_cache
from app.utils.logging_setup import get_logger

logger = get_logger("scanner")


@dataclass(frozen=True)
class OhlcvBar:
    open_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


def exchange_service_for_settings() -> "ExchangeService":
    from flask import has_app_context

    from app.config.settings import Config

    exchange_id = Config.EXCHANGE
    if has_app_context():
        try:
            exchange_id = SettingsService().get("exchange", Config.EXCHANGE)
        except Exception:
            pass
    return ExchangeService(exchange_id=exchange_id)


class ExchangeService:
    """Market data via CCXT (read-only OHLCV; multi-exchange ready)."""

    def __init__(self, exchange_id: str = "binance") -> None:
        self.exchange_id = normalize_exchange_id(exchange_id)
        self.exchange = create_ccxt_exchange(self.exchange_id)

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 300,
        *,
        since_ms: int | None = None,
        use_cache: bool = True,
    ) -> list[OhlcvBar]:
        ccxt_tf = to_ccxt_timeframe(timeframe)
        cache_key = f"{self.exchange_id}:{symbol}:{ccxt_tf}:{limit}:{since_ms or 0}"
        if use_cache and since_ms is None:
            cached = ohlcv_cache.get(cache_key)
            if cached is not None:
                return cached

        params: dict[str, Any] = {}
        if since_ms is not None:
            raw = self.exchange.fetch_ohlcv(
                symbol, timeframe=ccxt_tf, since=since_ms, limit=limit
            )
        else:
            raw = self.exchange.fetch_ohlcv(symbol, timeframe=ccxt_tf, limit=limit)

        bars = _rows_to_bars(raw)
        logger.debug("Fetched %s bars for %s %s (%s)", len(bars), symbol, timeframe, self.exchange_id)
        if use_cache and since_ms is None:
            ohlcv_cache.set(cache_key, bars)
        return bars

    def fetch_ohlcv_dataframe(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 300,
        *,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        bars = self.fetch_ohlcv(symbol, timeframe, limit=limit, use_cache=use_cache)
        if not bars:
            return pd.DataFrame()
        data = {
            "open": [float(b.open) for b in bars],
            "high": [float(b.high) for b in bars],
            "low": [float(b.low) for b in bars],
            "close": [float(b.close) for b in bars],
            "volume": [float(b.volume) for b in bars],
        }
        index = pd.DatetimeIndex([b.open_time for b in bars], tz="UTC")
        return pd.DataFrame(data, index=index)


def _rows_to_bars(raw: list[list[Any]]) -> list[OhlcvBar]:
    bars: list[OhlcvBar] = []
    for row in raw:
        ts_ms, o, h, l, c, v = row
        bars.append(
            OhlcvBar(
                open_time=datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc),
                open=Decimal(str(o)),
                high=Decimal(str(h)),
                low=Decimal(str(l)),
                close=Decimal(str(c)),
                volume=Decimal(str(v)),
            )
        )
    return bars
