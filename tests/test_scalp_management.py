import pandas as pd

from app.backtester.engine import BacktestEngine
from app.indicators.engine import IndicatorRegistry
from app.strategies.scalp_management import check_intrabar_exit, management_from_definition
from app.strategies.scalping_templates import SCALPING_TEMPLATES
from app.strategies.validator import validate_definition


def test_scalping_templates_have_mandatory_management():
    for template in SCALPING_TEMPLATES:
        definition = template["definition_json"]
        validate_definition(definition)
        mgmt = management_from_definition(definition)
        assert "max_hold_bars" in mgmt
        assert "cooldown_bars" in mgmt
        assert "risk" in definition


def test_template_a_short_requires_all_emas():
    short_rules = SCALPING_TEMPLATES[0]["definition_json"]["short"]["rules"]
    assert len(short_rules) == 5  # cross + rsi + close<ema5/8/13


def test_template_b_skips_optional_rsi():
    long_rules = SCALPING_TEMPLATES[1]["definition_json"]["long"]["rules"]
    assert len(long_rules) == 2  # vwap + macd only


def test_daily_vwap_resets():
    idx = pd.date_range("2026-07-01", periods=10, freq="5min", tz="UTC")
    # Second UTC day starts at index where date changes — build two days
    idx = pd.DatetimeIndex(
        list(pd.date_range("2026-07-01 23:00", periods=5, freq="5min", tz="UTC"))
        + list(pd.date_range("2026-07-02 00:00", periods=5, freq="5min", tz="UTC"))
    )
    close = pd.Series([100.0] * 5 + [200.0] * 5, index=idx)
    df = pd.DataFrame(
        {
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 10.0,
        },
        index=idx,
    )
    out = IndicatorRegistry().compute("VWAP", df, {})
    # First bar of new day should not equal prior cumulative vwap path
    assert out["VWAP"].iloc[5] != out["VWAP"].iloc[4]
    # New-day VWAP near day-2 prices (~200), not blended with ~100
    assert out["VWAP"].iloc[5] > 150


def test_intrabar_prefers_stop_when_both_hit():
    reason, px = check_intrabar_exit("long", high=110, low=90, stop=95, take=105)
    assert reason == "sl"
    assert px == 95


def test_backtest_runs_scalp_template_a():
    idx = pd.date_range("2026-01-01", periods=400, freq="5min", tz="UTC")
    close = pd.Series([100.0 + i for i in range(400)], index=idx)
    df = pd.DataFrame(
        {
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 1000.0,
        },
        index=idx,
    )
    definition = SCALPING_TEMPLATES[0]["definition_json"]
    out = BacktestEngine().run(df, definition, "5m")
    assert "total_trades" in out.metrics
    assert out.metrics["buy_signals"] + out.metrics["sell_signals"] >= 0
