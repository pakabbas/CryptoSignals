from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.scanner.candle_utils import TIMEFRAME_SECONDS, to_ccxt_timeframe
from app.services.candle_service import CandleService
from app.services.exchange_service import OhlcvBar, exchange_service_for_settings
from app.utils.logging_setup import get_logger

logger = get_logger("scanner")

BACKTEST_PERIODS_DAYS = [7, 30, 90, 180, 365]
WARMUP_BARS = 250


class HistoricalDownloadService:
    def __init__(self) -> None:
        from app.services.exchange_service import exchange_service_for_settings

        self.exchange = exchange_service_for_settings()
        self.candles = CandleService()

    def download_and_store(
        self,
        coin_id: int,
        symbol: str,
        timeframe: str,
        period_days: int,
    ) -> int:
        bars = self.fetch_history(symbol, timeframe, period_days)
        return self.candles.upsert_bars(coin_id, timeframe, bars)

    def fetch_history(self, symbol: str, timeframe: str, period_days: int) -> list[OhlcvBar]:
        ccxt_tf = to_ccxt_timeframe(timeframe)
        tf_seconds = TIMEFRAME_SECONDS[timeframe]
        total_bars = int((period_days * 86400) / tf_seconds) + WARMUP_BARS
        since = datetime.now(timezone.utc) - timedelta(seconds=total_bars * tf_seconds)
        since_ms = int(since.timestamp() * 1000)
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

        all_rows: list[list] = []
        while since_ms < now_ms:
            batch = self.exchange.exchange.fetch_ohlcv(
                symbol,
                timeframe=ccxt_tf,
                since=since_ms,
                limit=1000,
            )
            if not batch:
                break
            all_rows.extend(batch)
            since_ms = batch[-1][0] + 1
            if len(batch) < 1000:
                break

        bars: list[OhlcvBar] = []
        seen: set[int] = set()
        for row in all_rows:
            ts_ms = row[0]
            if ts_ms in seen:
                continue
            seen.add(ts_ms)
            o, h, l, c, v = row[1], row[2], row[3], row[4], row[5]
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
        bars.sort(key=lambda b: b.open_time)
        logger.info("Downloaded %s candles for %s %s (%sd)", len(bars), symbol, timeframe, period_days)
        return bars

    def dataframe_from_db(self, coin_id: int, timeframe: str, period_days: int):
        import pandas as pd

        tf_seconds = TIMEFRAME_SECONDS[timeframe]
        limit = int((period_days * 86400) / tf_seconds) + WARMUP_BARS
        rows = self.candles.list_bars(coin_id, timeframe, limit=limit)
        if not rows:
            return pd.DataFrame()
        data = {
            "open": [float(r.open) for r in rows],
            "high": [float(r.high) for r in rows],
            "low": [float(r.low) for r in rows],
            "close": [float(r.close) for r in rows],
            "volume": [float(r.volume) for r in rows],
        }
        index = pd.DatetimeIndex([r.open_time for r in rows], tz="UTC")
        return pd.DataFrame(data, index=index)
