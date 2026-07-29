from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import joinedload

from app.database import db
from app.models import Signal
from app.services.base import BaseService
from app.services.email_service import EmailService
from app.services.push_service import PushNotificationService
from app.services.settings_service import SettingsService
from app.utils.logging_setup import get_logger

logger = get_logger("strategy")


class SignalService(BaseService[Signal]):
    def exists_for_candle(
        self,
        coin_id: int,
        strategy_id: int | None,
        timeframe: str,
        signal_type: str,
        candle_time: datetime,
    ) -> bool:
        return (
            Signal.query.filter_by(
                coin_id=coin_id,
                strategy_id=strategy_id,
                timeframe=timeframe,
                signal_type=signal_type,
                candle_time=candle_time,
            ).first()
            is not None
        )

    def create_and_notify(
        self,
        *,
        coin_id: int,
        strategy_id: int,
        strategy_name: str,
        symbol: str,
        signal_type: str,
        timeframe: str,
        price: float,
        candle_time: datetime,
    ) -> Signal | None:
        if candle_time.tzinfo is None:
            candle_time = candle_time.replace(tzinfo=timezone.utc)

        if self.exists_for_candle(coin_id, strategy_id, timeframe, signal_type, candle_time):
            logger.info(
                "Duplicate signal skipped %s %s %s @ %s",
                symbol,
                signal_type,
                timeframe,
                candle_time.isoformat(),
            )
            return None

        signal = Signal(
            coin_id=coin_id,
            strategy_id=strategy_id,
            signal_type=signal_type,
            timeframe=timeframe,
            price=Decimal(str(price)),
            candle_time=candle_time,
            notified=False,
        )
        db.session.add(signal)
        db.session.flush()

        smtp = SettingsService().get_smtp()
        notified = False
        if smtp.receiver_email and smtp.smtp_server:
            try:
                EmailService().send_signal_alert(
                    smtp,
                    signal_type=signal_type,
                    symbol=symbol,
                    timeframe=timeframe,
                    price=price,
                    strategy_name=strategy_name,
                    candle_time_utc=candle_time.strftime("%Y-%m-%d %H:%M UTC"),
                )
                notified = True
            except Exception as exc:
                logger.error("Failed to send alert email: %s", exc)

        try:
            push_count = PushNotificationService().send_signal_alert(
                signal_type=signal_type,
                symbol=symbol,
                timeframe=timeframe,
                price=price,
                strategy_name=strategy_name,
            )
            if push_count:
                notified = True
        except Exception as exc:
            logger.error("Failed to send push alert: %s", exc)

        signal.notified = notified
        if not notified:
            logger.warning("Signal saved; no email or push delivery succeeded")

        db.session.commit()
        logger.info("Signal recorded %s %s %s", symbol, signal_type, timeframe)
        return signal

    def recent(self, limit: int = 50) -> list[Signal]:
        return (
            Signal.query.options(joinedload(Signal.coin), joinedload(Signal.strategy))
            .order_by(Signal.created_at.desc())
            .limit(limit)
            .all()
        )
