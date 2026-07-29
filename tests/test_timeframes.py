from app.config.timeframes import SUPPORTED_TIMEFRAMES, normalize_timeframe, timeframe_label


def test_supported_timeframes():
    assert SUPPORTED_TIMEFRAMES == ("15m", "30m", "1H", "4H")


def test_normalize_timeframe_aliases():
    assert normalize_timeframe("1h") == "1H"
    assert normalize_timeframe("4h") == "4H"
    assert normalize_timeframe("15m") == "15m"


def test_timeframe_labels():
    assert timeframe_label("1H") == "1h"
    assert timeframe_label("4H") == "4h"
