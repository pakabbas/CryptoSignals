"""Stop-loss / take-profit levels from entry (fixed % or ATR)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


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


@dataclass(frozen=True)
class RiskSpec:
    atr_length: int = 14
    stop_atr_mult: float = 1.5
    target_atr_mult: float | None = None
    target_rr: float | None = 2.0


def risk_spec_from_definition(definition: dict[str, Any] | None) -> RiskSpec | None:
    if not isinstance(definition, dict):
        return None
    raw = definition.get("risk")
    if not isinstance(raw, dict):
        return None
    return RiskSpec(
        atr_length=int(raw.get("atr_length", 14)),
        stop_atr_mult=float(raw.get("stop_atr_mult", 1.5)),
        target_atr_mult=(
            float(raw["target_atr_mult"]) if raw.get("target_atr_mult") is not None else None
        ),
        target_rr=float(raw["target_rr"]) if raw.get("target_rr") is not None else None,
    )


def levels_from_entry(signal_type: str, entry: float) -> RiskLevels:
    """BUY → long (SL below, TP above). SELL → short (SL above, TP below). Fixed %."""
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


def levels_from_atr(
    signal_type: str,
    entry: float,
    atr: float,
    spec: RiskSpec,
) -> RiskLevels:
    """ATR-scaled SL/TP from indicators.md risk blocks."""
    entry = float(entry)
    atr = abs(float(atr))
    side = "long" if str(signal_type).upper() == "BUY" else "short"
    stop_dist = atr * float(spec.stop_atr_mult)
    if spec.target_atr_mult is not None:
        target_dist = atr * float(spec.target_atr_mult)
    else:
        rr = float(spec.target_rr or 2.0)
        target_dist = stop_dist * rr
    if side == "long":
        stop = entry - stop_dist
        take = entry + target_dist
    else:
        stop = entry + stop_dist
        take = entry - target_dist
    sl_pct = (stop_dist / entry * 100) if entry else 0.0
    tp_pct = (target_dist / entry * 100) if entry else 0.0
    return RiskLevels(
        entry=entry,
        stop_loss=stop,
        take_profit=take,
        stop_loss_pct=round(sl_pct, 4),
        take_profit_pct=round(tp_pct, 4),
        side=side,
    )


def levels_for_signal_alert(
    signal_type: str,
    entry: float,
    *,
    definition: dict[str, Any] | None = None,
    atr: float | None = None,
) -> RiskLevels:
    spec = risk_spec_from_definition(definition)
    if spec is not None and atr is not None and atr > 0:
        return levels_from_atr(signal_type, entry, atr, spec)
    return levels_from_entry(signal_type, entry)


def format_price(value: float) -> str:
    v = float(value)
    if v >= 1000:
        return f"{v:,.2f}"
    if v >= 1:
        return f"{v:,.4f}"
    text = f"{v:.8f}".rstrip("0").rstrip(".")
    return text or "0"


def format_risk_lines(levels: RiskLevels) -> str:
    if levels.side == "long":
        return (
            f"Entry ${format_price(levels.entry)} · "
            f"SL ${format_price(levels.stop_loss)} (−{levels.stop_loss_pct:g}%) · "
            f"TP ${format_price(levels.take_profit)} (+{levels.take_profit_pct:g}%)"
        )
    return (
        f"Entry ${format_price(levels.entry)} · "
        f"SL ${format_price(levels.stop_loss)} (+{levels.stop_loss_pct:g}%) · "
        f"TP ${format_price(levels.take_profit)} (−{levels.take_profit_pct:g}%)"
    )
