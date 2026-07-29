"""Timeframe helpers for scanner and exchange."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

# App/UI format -> CCXT timeframe
TIMEFRAME_TO_CCXT: dict[str, str] = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1H": "1h",
    "4H": "4h",
    "1D": "1d",
}

TIMEFRAME_SECONDS: dict[str, int] = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1H": 3600,
    "4H": 14400,
    "1D": 86400,
}


def to_ccxt_timeframe(timeframe: str) -> str:
    key = timeframe.strip()
    if key not in TIMEFRAME_TO_CCXT:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    return TIMEFRAME_TO_CCXT[key]


def timeframe_duration(timeframe: str) -> timedelta:
    seconds = TIMEFRAME_SECONDS.get(timeframe)
    if seconds is None:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    return timedelta(seconds=seconds)


def candle_close_time(open_time: datetime, timeframe: str) -> datetime:
    if open_time.tzinfo is None:
        open_time = open_time.replace(tzinfo=timezone.utc)
    return open_time + timeframe_duration(timeframe)


def is_candle_closed(open_time: datetime, timeframe: str, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    if open_time.tzinfo is None:
        open_time = open_time.replace(tzinfo=timezone.utc)
    return candle_close_time(open_time, timeframe) <= now


def last_closed_bar_index(open_times: list[datetime], timeframe: str, now: datetime | None = None) -> int:
    """Return DataFrame row index of the latest fully closed candle."""
    if not open_times:
        raise ValueError("No candles")
    now = now or datetime.now(timezone.utc)
    last_idx = len(open_times) - 1
    if is_candle_closed(open_times[last_idx], timeframe, now):
        return last_idx
    if last_idx == 0:
        raise ValueError("No closed candle available")
    return last_idx - 1


def next_candle_close_utc(
    last_bar_open: datetime,
    timeframe: str,
    now: datetime | None = None,
) -> datetime:
    """When the current forming candle closes (next evaluation moment for signals)."""
    now = now or datetime.now(timezone.utc)
    if last_bar_open.tzinfo is None:
        last_bar_open = last_bar_open.replace(tzinfo=timezone.utc)
    if not is_candle_closed(last_bar_open, timeframe, now):
        return candle_close_time(last_bar_open, timeframe)
    return candle_close_time(last_bar_open, timeframe) + timeframe_duration(timeframe)
