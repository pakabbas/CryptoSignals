from app.risk.levels import format_risk_lines, levels_from_entry


def test_long_buy_levels():
    levels = levels_from_entry("BUY", 100.0)
    assert levels.side == "long"
    assert abs(levels.stop_loss - 98.5) < 1e-9
    assert abs(levels.take_profit - 103.0) < 1e-9


def test_short_sell_levels():
    levels = levels_from_entry("SELL", 100.0)
    assert levels.side == "short"
    assert abs(levels.stop_loss - 101.5) < 1e-9
    assert abs(levels.take_profit - 97.0) < 1e-9


def test_format_includes_sl_tp():
    text = format_risk_lines(levels_from_entry("BUY", 0.07))
    assert "Entry" in text and "SL" in text and "TP" in text
