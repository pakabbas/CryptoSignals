from datetime import datetime, timezone

from app.risk.levels import levels_from_entry
from app.risk.outcome import evaluate_candles, resolve_bar, unrealized_pnl_pct


def test_long_hits_tp():
    levels = levels_from_entry("BUY", 100.0)
    t0 = datetime(2026, 7, 1, tzinfo=timezone.utc)
    hit = evaluate_candles(
        levels,
        [
            (t0, 100.5, 104.0, 100.0, 103.5),
        ],
    )
    assert hit is not None
    assert hit.status == "profit"
    assert abs(hit.exit_price - 103.0) < 1e-9


def test_long_hits_sl():
    levels = levels_from_entry("BUY", 100.0)
    t0 = datetime(2026, 7, 1, tzinfo=timezone.utc)
    hit = evaluate_candles(
        levels,
        [
            (t0, 99.5, 100.0, 98.0, 98.2),
        ],
    )
    assert hit is not None
    assert hit.status == "loss"


def test_same_bar_prefers_closer_level():
    result = resolve_bar(side="long", open_=98.6, high=104.0, low=98.0, stop_loss=98.5, take_profit=103.0)
    assert result is not None
    assert result[0] == "loss"


def test_unrealized():
    assert unrealized_pnl_pct("BUY", 100, 102) == 2.0
    assert unrealized_pnl_pct("SELL", 100, 98) == 2.0
