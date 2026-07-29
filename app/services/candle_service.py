from __future__ import annotations

from datetime import datetime

from app.database import db
from app.models import HistoricalCandle
from app.services.base import BaseService
from app.services.exchange_service import OhlcvBar
from app.utils.logging_setup import get_logger

logger = get_logger("scanner")


class CandleService(BaseService[HistoricalCandle]):
    def upsert_bars(self, coin_id: int, timeframe: str, bars: list[OhlcvBar]) -> int:
        stored = 0
        for bar in bars:
            row = HistoricalCandle.query.filter_by(
                coin_id=coin_id,
                timeframe=timeframe,
                open_time=bar.open_time,
            ).first()
            if row is None:
                row = HistoricalCandle(
                    coin_id=coin_id,
                    timeframe=timeframe,
                    open_time=bar.open_time,
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    volume=bar.volume,
                )
                db.session.add(row)
                stored += 1
            else:
                row.open = bar.open
                row.high = bar.high
                row.low = bar.low
                row.close = bar.close
                row.volume = bar.volume
        db.session.commit()
        if stored:
            logger.info("Stored %s new candles for coin_id=%s %s", stored, coin_id, timeframe)
        return stored

    def list_bars(self, coin_id: int, timeframe: str, limit: int = 300) -> list[HistoricalCandle]:
        rows = (
            HistoricalCandle.query.filter_by(coin_id=coin_id, timeframe=timeframe)
            .order_by(HistoricalCandle.open_time.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(rows))

    def count_bars_since(self, coin_id: int, timeframe: str, since: datetime) -> int:
        return (
            HistoricalCandle.query.filter_by(coin_id=coin_id, timeframe=timeframe)
            .filter(HistoricalCandle.open_time >= since)
            .count()
        )

    def latest_open_time(self, coin_id: int, timeframe: str) -> datetime | None:
        row = (
            HistoricalCandle.query.filter_by(coin_id=coin_id, timeframe=timeframe)
            .order_by(HistoricalCandle.open_time.desc())
            .first()
        )
        return row.open_time if row else None
