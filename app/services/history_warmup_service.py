from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.config.timeframes import SUPPORTED_TIMEFRAMES
from app.models import Coin
from app.scanner.candle_utils import TIMEFRAME_SECONDS
from app.services.candle_service import CandleService
from app.services.coin_service import CoinService
from app.services.historical_download_service import HistoricalDownloadService
from app.utils.logging_setup import get_logger

logger = get_logger("scanner")

MIN_HISTORY_DAYS = 7
# Allow exchange gaps / partial last candle
COVERAGE_RATIO = 0.92


def expected_bars_for_days(timeframe: str, days: int) -> int:
    seconds = TIMEFRAME_SECONDS[timeframe]
    return max(1, int((days * 86400) / seconds))


class HistoryWarmupService:
    """Ensure stored OHLCV covers at least N days for enabled coins × timeframes."""

    def __init__(self) -> None:
        self.coins = CoinService()
        self.candles = CandleService()
        self.downloader = HistoricalDownloadService()

    def ensure_all(self, days: int = MIN_HISTORY_DAYS) -> dict[str, Any]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        summary: dict[str, Any] = {
            "days": days,
            "pairs": [],
            "downloaded": 0,
            "already_ok": 0,
            "errors": 0,
        }
        enabled = [c for c in self.coins.list_coins() if c.enabled]
        for coin in enabled:
            for timeframe in SUPPORTED_TIMEFRAMES:
                row = self._ensure_one(coin, timeframe, days, since)
                summary["pairs"].append(row)
                if row.get("status") == "downloaded":
                    summary["downloaded"] += 1
                elif row.get("status") == "ok":
                    summary["already_ok"] += 1
                elif row.get("status") in {"error", "partial"}:
                    summary["errors"] += 1
        logger.info(
            "History warmup (%sd): %s ok, %s downloaded, %s errors",
            days,
            summary["already_ok"],
            summary["downloaded"],
            summary["errors"],
        )
        return summary

    def _ensure_one(
        self,
        coin: Coin,
        timeframe: str,
        days: int,
        since: datetime,
    ) -> dict[str, Any]:
        expected = expected_bars_for_days(timeframe, days)
        have = self.candles.count_bars_since(coin.id, timeframe, since)
        label = f"{coin.symbol} {timeframe} ({coin.exchange})"
        if have >= int(expected * COVERAGE_RATIO):
            return {
                "coin": coin.symbol,
                "exchange": coin.exchange,
                "timeframe": timeframe,
                "status": "ok",
                "bars": have,
                "expected": expected,
            }
        try:
            # Skip indicator warmup bars — Kraken only retains ~720 candles (~7.5d of 15m).
            stored = self.downloader.download_and_store(
                coin.id,
                coin.symbol,
                timeframe,
                days,
                exchange_id=coin.exchange,
                include_warmup=False,
            )
            have_after = self.candles.count_bars_since(coin.id, timeframe, since)
            status = "downloaded" if have_after >= int(expected * COVERAGE_RATIO) else "partial"
            return {
                "coin": coin.symbol,
                "exchange": coin.exchange,
                "timeframe": timeframe,
                "status": status,
                "bars": have_after,
                "expected": expected,
                "new_rows": stored,
            }
        except Exception as exc:
            logger.exception("History warmup failed %s: %s", label, exc)
            return {
                "coin": coin.symbol,
                "exchange": coin.exchange,
                "timeframe": timeframe,
                "status": "error",
                "error": str(exc),
                "bars": have,
                "expected": expected,
            }
