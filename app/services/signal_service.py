from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.config.alerts import email_alerts_enabled
from app.database import db
from app.models import Signal
from app.risk.levels import format_price, levels_from_entry
from app.risk.outcome import evaluate_candles, levels_for_signal, unrealized_pnl_pct
from app.services.base import BaseService
from app.services.email_service import EmailService
from app.services.exchange_service import exchange_service_for_coin
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

        levels = levels_from_entry(signal_type, price)
        signal = Signal(
            coin_id=coin_id,
            strategy_id=strategy_id,
            signal_type=signal_type,
            timeframe=timeframe,
            price=Decimal(str(price)),
            candle_time=candle_time,
            notified=False,
            status="open",
            stop_loss=Decimal(str(levels.stop_loss)),
            take_profit=Decimal(str(levels.take_profit)),
        )
        db.session.add(signal)
        db.session.flush()

        notified = False
        # Email alerts are off by default (ENABLE_EMAIL_ALERTS); FCM push is the active channel.
        if email_alerts_enabled():
            smtp = SettingsService().get_smtp()
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
            logger.warning("Signal saved; no push delivery succeeded")

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

    def summary_stats(self) -> dict[str, Any]:
        rows = Signal.query.with_entities(Signal.status, func.count(Signal.id)).group_by(Signal.status).all()
        counts = {status: int(count) for status, count in rows}
        open_n = counts.get("open", 0)
        wins = counts.get("profit", 0)
        losses = counts.get("loss", 0)
        closed = wins + losses
        win_rate = (wins / closed * 100) if closed else 0.0

        avg_row = (
            Signal.query.with_entities(func.avg(Signal.pnl_pct))
            .filter(Signal.status.in_(("profit", "loss")))
            .scalar()
        )
        return {
            "total": open_n + closed,
            "open": open_n,
            "wins": wins,
            "losses": losses,
            "closed": closed,
            "win_rate": round(float(win_rate), 2),
            "avg_pnl_pct": round(float(avg_row or 0), 2),
        }

    def check_open_statuses(self, *, limit: int = 200) -> dict[str, int]:
        """Re-check open signals against live/historical OHLCV for TP/SL hits."""
        opens = (
            Signal.query.options(joinedload(Signal.coin))
            .filter(Signal.status == "open")
            .order_by(Signal.candle_time.asc())
            .limit(limit)
            .all()
        )
        stats = {"checked": 0, "still_open": 0, "profit": 0, "loss": 0, "errors": 0}
        now = datetime.now(timezone.utc)

        for signal in opens:
            stats["checked"] += 1
            try:
                changed = self._check_one(signal, now=now)
                if changed == "profit":
                    stats["profit"] += 1
                elif changed == "loss":
                    stats["loss"] += 1
                else:
                    stats["still_open"] += 1
            except Exception as exc:
                stats["errors"] += 1
                logger.exception("Status check failed signal=%s: %s", signal.id, exc)

        db.session.commit()
        logger.info("Signal status check: %s", stats)
        return stats

    def _ensure_levels(self, signal: Signal) -> None:
        if signal.stop_loss is not None and signal.take_profit is not None:
            return
        levels = levels_from_entry(signal.signal_type, float(signal.price))
        signal.stop_loss = Decimal(str(levels.stop_loss))
        signal.take_profit = Decimal(str(levels.take_profit))

    def _check_one(self, signal: Signal, *, now: datetime) -> str:
        if not signal.coin:
            raise ValueError("Signal has no coin")
        self._ensure_levels(signal)
        levels = levels_for_signal(
            signal.signal_type,
            float(signal.price),
            float(signal.stop_loss) if signal.stop_loss is not None else None,
            float(signal.take_profit) if signal.take_profit is not None else None,
        )

        market = exchange_service_for_coin(signal.coin)
        candle_time = signal.candle_time
        if candle_time.tzinfo is None:
            candle_time = candle_time.replace(tzinfo=timezone.utc)
        since_ms = int(candle_time.timestamp() * 1000)

        bars = market.fetch_ohlcv(
            signal.coin.symbol,
            signal.timeframe,
            limit=500,
            since_ms=since_ms,
            use_cache=False,
        )
        candles = [
            (bar.open_time, float(bar.open), float(bar.high), float(bar.low), float(bar.close))
            for bar in bars
            if bar.open_time > candle_time
        ]
        hit = evaluate_candles(levels, candles)
        signal.checked_at = now
        if hit is None:
            if candles:
                last_close = candles[-1][4]
                signal.pnl_pct = Decimal(str(unrealized_pnl_pct(signal.signal_type, levels.entry, last_close)))
            return "open"

        signal.status = hit.status
        signal.exit_price = Decimal(str(hit.exit_price))
        signal.exit_time = hit.exit_time
        signal.pnl_pct = Decimal(str(hit.pnl_pct))
        return hit.status

    @staticmethod
    def status_label(signal: Signal) -> str:
        status = (signal.status or "open").lower()
        if status == "profit":
            return "Profit"
        if status == "loss":
            return "Loss"
        return "Open"

    @staticmethod
    def format_signal_price(value: Any) -> str:
        if value is None:
            return "—"
        return format_price(float(value))
