import pandas as pd

from app.indicators.engine import IndicatorRegistry, _rsi_series
from app.risk.levels import RiskSpec, levels_from_atr, levels_from_entry
from app.strategies.evaluator import StrategyEvaluator
from app.strategies.research_templates import RESEARCH_TEMPLATES
from app.strategies.validator import validate_definition


def test_all_indicator_templates_validate():
    for template in RESEARCH_TEMPLATES:
        validate_definition(template["definition_json"])
        assert "risk" in template["definition_json"]


def test_rsi_stays_float64_for_rolling():
    """pd.NA in RSI used to make object dtype → StochRSI rolling 'No numeric types to aggregate'."""
    close = pd.Series([100.0] * 5 + [101.0, 99.0, 102.0, 98.0, 103.0, 97.0] * 40)
    rsi = _rsi_series(close, 14)
    assert str(rsi.dtype) == "float64"
    # Must not raise DataError
    assert rsi.rolling(14).min().notna().any()

    df = pd.DataFrame(
        {
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": close * 10,
        }
    )
    out = IndicatorRegistry().compute(
        "STOCHRSI", df, {"length": 14, "stoch_length": 14, "smooth_k": 3, "smooth_d": 3}
    )
    assert out["STOCHRSIk_14"].notna().any()


def test_stochrsi_cross_resolves_after_upper():
    """name.upper() made STOCHRSIk → STOCHRSIK miss the resolver; crosses never fired."""
    close = pd.Series([100.0, 101, 99, 102, 98, 103, 97, 104, 96, 105] * 40)
    df = pd.DataFrame(
        {
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": close * 10,
        }
    )
    definition = next(t for t in RESEARCH_TEMPLATES if t["timeframe"] == "15m")["definition_json"]
    ev = StrategyEvaluator()
    enriched = ev._enrich_dataframe(df, definition)
    node = {"name": "STOCHRSIk", "length": 10, "stoch_length": 10, "smooth_k": 3, "smooth_d": 3}
    assert ev._resolve_value(enriched, node, 250) is not None


def test_atr_levels_long():
    levels = levels_from_atr("BUY", 100.0, 2.0, RiskSpec(stop_atr_mult=1.0, target_atr_mult=2.0))
    assert abs(levels.stop_loss - 98.0) < 1e-9
    assert abs(levels.take_profit - 104.0) < 1e-9


def test_atr_levels_short_rr():
    levels = levels_from_atr("SELL", 100.0, 2.0, RiskSpec(stop_atr_mult=1.5, target_rr=2.0))
    assert abs(levels.stop_loss - 103.0) < 1e-9
    assert abs(levels.take_profit - 94.0) < 1e-9


def test_fixed_pct_still_works():
    levels = levels_from_entry("BUY", 100.0)
    assert levels.stop_loss < 100
    assert levels.take_profit > 100
