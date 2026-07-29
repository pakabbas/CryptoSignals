from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import ccxt
import pandas as pd

from app.scanner.candle_utils import to_ccxt_timeframe
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


class ExchangeService:
    """Binance market data via CCXT (read-only, no API keys required for OHLCV)."""

    def __init__(self, exchange_id: str = "binance") -> None:
        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class({"enableRateLimit": True})

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 300,
    ) -> list[OhlcvBar]:
        ccxt_tf = to_ccxt_timeframe(timeframe)
        raw = self.exchange.fetch_ohlcv(symbol, timeframe=ccxt_tf, limit=limit)
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
        logger.debug("Fetched %s bars for %s %s", len(bars), symbol, timeframe)
        return bars

    def fetch_ohlcv_dataframe(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 300,
    ) -> pd.DataFrame:
        bars = self.fetch_ohlcv(symbol, timeframe, limit=limit)
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
