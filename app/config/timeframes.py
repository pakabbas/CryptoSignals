"""Supported candle timeframes for UI and scanner."""

from __future__ import annotations

# Internal keys (stored in DB / strategies / settings)
SUPPORTED_TIMEFRAMES: tuple[str, ...] = ("5m", "15m", "30m", "1H", "4H")

# Shown in dropdowns and scanner pills
TIMEFRAME_LABELS: dict[str, str] = {
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1H": "1h",
    "4H": "4h",
}

_ALIASES: dict[str, str] = {
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1H",
    "1H": "1H",
    "4h": "4H",
    "4H": "4H",
}


def normalize_timeframe(value: str, *, default: str = "1H") -> str:
    key = (value or "").strip()
    if not key:
        return default if default in SUPPORTED_TIMEFRAMES else "1H"
    normalized = _ALIASES.get(key) or _ALIASES.get(key.lower())
    if normalized in SUPPORTED_TIMEFRAMES:
        return normalized
    return default if default in SUPPORTED_TIMEFRAMES else "1H"


def timeframe_label(value: str) -> str:
    tf = normalize_timeframe(value)
    return TIMEFRAME_LABELS.get(tf, tf)
