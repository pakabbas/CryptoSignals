from app.config.timeframes import SUPPORTED_TIMEFRAMES
from app.services.history_warmup_service import expected_bars_for_days


def test_expected_bars_7_days():
    assert expected_bars_for_days("15m", 7) == 7 * 96
    assert expected_bars_for_days("30m", 7) == 7 * 48
    assert expected_bars_for_days("1H", 7) == 7 * 24
    assert expected_bars_for_days("4H", 7) == 7 * 6


def test_supported_timeframes_cover_warmup():
    assert SUPPORTED_TIMEFRAMES == ("15m", "30m", "1H", "4H")
