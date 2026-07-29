"""Fixed-percent stop-loss / take-profit levels from entry price."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _pct_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        value = float(str(raw).strip())
    except ValueError:
        return default
    return value if value > 0 else default


def stop_loss_pct() -> float:
    return _pct_env("STOP_LOSS_PCT", 1.5)


def take_profit_pct() -> float:
    return _pct_env("TAKE_PROFIT_PCT", 3.0)


@dataclass(frozen=True)
class RiskLevels:
    entry: float
    stop_loss: float
    take_profit: float
    stop_loss_pct: float
    take_profit_pct: float
    side: str  # long | short


def levels_from_entry(signal_type: str, entry: float) -> RiskLevels:
    """BUY → long (SL below, TP above). SELL → short (SL above, TP below)."""
    sl_pct = stop_loss_pct()
    tp_pct = take_profit_pct()
    entry = float(entry)
    side = "long" if str(signal_type).upper() == "BUY" else "short"
    if side == "long":
        stop = entry * (1 - sl_pct / 100)
        take = entry * (1 + tp_pct / 100)
    else:
        stop = entry * (1 + sl_pct / 100)
        take = entry * (1 - tp_pct / 100)
    return RiskLevels(
        entry=entry,
        stop_loss=stop,
        take_profit=take,
        stop_loss_pct=sl_pct,
        take_profit_pct=tp_pct,
        side=side,
    )


def format_price(value: float) -> str:
    v = float(value)
    if v >= 1000:
        return f"{v:,.2f}"
    if v >= 1:
        return f"{v:,.4f}"
    text = f"{v:.8f}".rstrip("0").rstrip(".")
    return text or "0"


def format_risk_lines(levels: RiskLevels) -> str:
    return (
        f"Entry ${format_price(levels.entry)} · "
        f"SL ${format_price(levels.stop_loss)} (−{levels.stop_loss_pct:g}%) · "
        f"TP ${format_price(levels.take_profit)} (+{levels.take_profit_pct:g}%)"
        if levels.side == "long"
        else (
            f"Entry ${format_price(levels.entry)} · "
            f"SL ${format_price(levels.stop_loss)} (+{levels.stop_loss_pct:g}%) · "
            f"TP ${format_price(levels.take_profit)} (−{levels.take_profit_pct:g}%)"
        )
    )
