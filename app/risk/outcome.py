"""Evaluate whether a signal hit take-profit or stop-loss on later candles."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from app.risk.levels import RiskLevels, levels_from_entry


@dataclass(frozen=True)
class OutcomeHit:
    status: str  # profit | loss
    exit_price: float
    exit_time: datetime
    pnl_pct: float


def pnl_pct_for(side: str, entry: float, exit_price: float) -> float:
    if entry == 0:
        return 0.0
    if side == "long":
        return ((exit_price - entry) / entry) * 100
    return ((entry - exit_price) / entry) * 100


def unrealized_pnl_pct(signal_type: str, entry: float, last_price: float) -> float:
    side = "long" if str(signal_type).upper() == "BUY" else "short"
    return round(pnl_pct_for(side, float(entry), float(last_price)), 4)


def resolve_bar(
    *,
    side: str,
    open_: float,
    high: float,
    low: float,
    stop_loss: float,
    take_profit: float,
) -> tuple[str, float] | None:
    """Return (status, exit_price) if TP or SL hit on this bar."""
    if side == "long":
        hit_sl = low <= stop_loss
        hit_tp = high >= take_profit
        if hit_sl and hit_tp:
            # Ambiguous same-bar: assume whichever is closer to the open filled first.
            if abs(open_ - stop_loss) <= abs(open_ - take_profit):
                return "loss", stop_loss
            return "profit", take_profit
        if hit_sl:
            return "loss", stop_loss
        if hit_tp:
            return "profit", take_profit
        return None

    hit_sl = high >= stop_loss
    hit_tp = low <= take_profit
    if hit_sl and hit_tp:
        if abs(open_ - stop_loss) <= abs(open_ - take_profit):
            return "loss", stop_loss
        return "profit", take_profit
    if hit_sl:
        return "loss", stop_loss
    if hit_tp:
        return "profit", take_profit
    return None


def evaluate_candles(
    levels: RiskLevels,
    candles: Iterable[tuple[datetime, float, float, float, float]],
) -> OutcomeHit | None:
    """
    candles: iterable of (open_time, open, high, low, close) after entry.
    Returns first TP/SL hit walking forward in time.
    """
    for open_time, open_, high, low, _close in candles:
        hit = resolve_bar(
            side=levels.side,
            open_=float(open_),
            high=float(high),
            low=float(low),
            stop_loss=levels.stop_loss,
            take_profit=levels.take_profit,
        )
        if hit is None:
            continue
        status, exit_price = hit
        return OutcomeHit(
            status=status,
            exit_price=exit_price,
            exit_time=open_time,
            pnl_pct=round(pnl_pct_for(levels.side, levels.entry, exit_price), 4),
        )
    return None


def levels_for_signal(signal_type: str, entry: float, stop_loss: float | None, take_profit: float | None) -> RiskLevels:
    if stop_loss is not None and take_profit is not None:
        base = levels_from_entry(signal_type, entry)
        return RiskLevels(
            entry=float(entry),
            stop_loss=float(stop_loss),
            take_profit=float(take_profit),
            stop_loss_pct=base.stop_loss_pct,
            take_profit_pct=base.take_profit_pct,
            side=base.side,
        )
    return levels_from_entry(signal_type, entry)
