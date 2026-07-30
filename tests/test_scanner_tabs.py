from app.routes.scanner import _build_coin_panels
from app.services.scanner_dashboard_service import CoinTicker, StrategyLiveView


class _Coin:
    def __init__(self, coin_id: int, symbol: str):
        self.id = coin_id
        self.symbol = symbol


def test_build_coin_panels_groups_by_coin():
    coins = [_Coin(1, "BTC/USDT"), _Coin(3, "SOL/USDT")]
    tickers = [
        CoinTicker(
            coin_id=1,
            symbol="BTC/USDT",
            price=64000.0,
            change_pct=0.1,
            volume=10.0,
            timeframe="1H",
            last_candle=None,
        ),
        CoinTicker(
            coin_id=3,
            symbol="SOL/USDT",
            price=73.0,
            change_pct=-0.2,
            volume=5.0,
            timeframe="1H",
            last_candle=None,
        ),
    ]
    views = [
        StrategyLiveView(
            strategy_id=1,
            strategy_name="EMA",
            coin_symbol="BTC/USDT",
            timeframe="1H",
            enabled=True,
            price=64000.0,
            signal_type="BUY",
            long=None,
            short=None,
            next_close_at=None,
            evaluated_at=None,
            indicator_values={},
        ),
        StrategyLiveView(
            strategy_id=2,
            strategy_name="BB",
            coin_symbol="BTC/USDT",
            timeframe="1H",
            enabled=True,
            price=64000.0,
            signal_type=None,
            long=None,
            short=None,
            next_close_at=None,
            evaluated_at=None,
            indicator_values={},
        ),
        StrategyLiveView(
            strategy_id=1,
            strategy_name="EMA",
            coin_symbol="SOL/USDT",
            timeframe="1H",
            enabled=True,
            price=73.0,
            signal_type=None,
            long=None,
            short=None,
            next_close_at=None,
            evaluated_at=None,
            indicator_values={},
        ),
    ]

    panels = _build_coin_panels(coins, tickers, views, [])
    assert len(panels) == 2
    assert panels[0]["short"] == "BTC"
    assert len(panels[0]["views"]) == 2
    assert panels[0]["ready_count"] == 1
    assert panels[1]["short"] == "SOL"
    assert len(panels[1]["views"]) == 1
    assert panels[1]["ready_count"] == 0
