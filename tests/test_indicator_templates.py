from app.risk.levels import RiskSpec, levels_from_atr, levels_from_entry
from app.strategies.research_templates import RESEARCH_TEMPLATES
from app.strategies.validator import validate_definition


def test_all_indicator_templates_validate():
    for template in RESEARCH_TEMPLATES:
        validate_definition(template["definition_json"])
        assert "risk" in template["definition_json"]


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
