from datetime import datetime, timezone
from decimal import Decimal

from app.models import Coin, Signal, Strategy
from app.database import db
from app.services.signal_service import SignalService


def test_last_closed_bar_index_when_last_candle_open():
    from app.scanner.candle_utils import last_closed_bar_index

    now = datetime(2026, 1, 1, 12, 30, tzinfo=timezone.utc)
    times = [
        datetime(2026, 1, 1, 11, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
    ]
    idx = last_closed_bar_index(times, "1H", now=now)
    assert idx == 0


def test_signal_duplicate_detection(app):
    with app.app_context():
        coin = Coin.query.filter_by(symbol="BTC/USDT").first()
        strategy = Strategy(name="Test Dup", definition_json={}, enabled=True, timeframe="1H")
        db.session.add(strategy)
        db.session.commit()

        candle_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        svc = SignalService()
        assert not svc.exists_for_candle(coin.id, strategy.id, "1H", "BUY", candle_time)

        db.session.add(
            Signal(
                coin_id=coin.id,
                strategy_id=strategy.id,
                signal_type="BUY",
                timeframe="1H",
                price=Decimal("100"),
                candle_time=candle_time,
            )
        )
        db.session.commit()
        assert svc.exists_for_candle(coin.id, strategy.id, "1H", "BUY", candle_time)
