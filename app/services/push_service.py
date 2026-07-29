from __future__ import annotations

import json
import os
from typing import Any

from app.config.alerts import push_alerts_enabled
from app.database import db
from app.models import PushDevice
from app.services.base import BaseService
from app.risk.levels import format_risk_lines, levels_from_entry
from app.utils.logging_setup import get_logger

logger = get_logger("app")

_firebase_ready = False
_firebase_init_attempted = False


def _init_firebase() -> bool:
    global _firebase_ready, _firebase_init_attempted
    if _firebase_init_attempted:
        return _firebase_ready
    _firebase_init_attempted = True
    if not push_alerts_enabled():
        return False
    try:
        import firebase_admin
        from firebase_admin import credentials

        if firebase_admin._apps:
            _firebase_ready = True
            return True

        raw = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
        path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "").strip()
        if raw:
            cred = credentials.Certificate(json.loads(raw))
        elif path and os.path.isfile(path):
            cred = credentials.Certificate(path)
        else:
            logger.warning("Firebase service account not configured; push disabled")
            return False
        firebase_admin.initialize_app(cred)
        _firebase_ready = True
        return True
    except Exception as exc:
        logger.error("Firebase init failed: %s", exc)
        return False


def firebase_server_configured() -> bool:
    """True if service account JSON or path is available (does not init SDK)."""
    if not push_alerts_enabled():
        return False
    raw = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "").strip()
    if raw:
        try:
            json.loads(raw)
            return True
        except json.JSONDecodeError:
            return False
    return bool(path and os.path.isfile(path))


def push_send_readiness() -> tuple[bool, str]:
    """Whether server can send FCM and a short reason if not."""
    if not push_alerts_enabled():
        return False, "Push alerts are disabled on the server."
    if not firebase_server_configured():
        return False, "Firebase service account is missing on the server (GitHub secret FIREBASE_SERVICE_ACCOUNT_JSON)."
    if not _init_firebase():
        return False, "Firebase failed to start — check server logs."
    return True, "OK"


class PushNotificationService(BaseService[PushDevice]):
    def register_token(self, token: str, *, user_agent: str | None = None, label: str | None = None) -> PushDevice:
        token = token.strip()
        if not token:
            raise ValueError("FCM token is required")
        row = PushDevice.query.filter_by(fcm_token=token).first()
        if row:
            row.enabled = True
            if user_agent:
                row.user_agent = user_agent[:512]
            if label:
                row.label = label[:128]
        else:
            row = PushDevice(
                fcm_token=token,
                user_agent=(user_agent or "")[:512] or None,
                label=(label or "")[:128] or None,
                enabled=True,
            )
            db.session.add(row)
        db.session.commit()
        logger.info("Registered FCM device id=%s", row.id)
        return row

    def unregister_token(self, token: str) -> None:
        row = PushDevice.query.filter_by(fcm_token=token.strip()).first()
        if row:
            db.session.delete(row)
            db.session.commit()

    def list_devices(self) -> list[PushDevice]:
        return PushDevice.query.filter_by(enabled=True).order_by(PushDevice.updated_at.desc()).all()

    def send_test(self) -> tuple[int, str | None]:
        ready, reason = push_send_readiness()
        if not ready:
            return 0, reason
        devices = self.list_devices()
        if not devices:
            return 0, "No browser registered yet — click Enable notifications on this page first."
        sent = self._broadcast(
            title="CryptoSignals test",
            body="Browser push is working. You will get alerts here when signals fire.",
        )
        if sent:
            return sent, None
        return 0, "FCM rejected all tokens — enable notifications again on this browser."

    def send_signal_alert(
        self,
        *,
        signal_type: str,
        symbol: str,
        timeframe: str,
        price: float,
        strategy_name: str,
    ) -> int:
        levels = levels_from_entry(signal_type, price)
        title = f"{signal_type} · {symbol}"
        body = (
            f"{strategy_name} · {timeframe}\n"
            f"{format_risk_lines(levels)}"
        )
        return self._broadcast(
            title=title,
            body=body,
            data={
                "url": "/signals/",
                "signal_type": signal_type,
                "symbol": symbol,
                "entry": levels.entry,
                "stop_loss": levels.stop_loss,
                "take_profit": levels.take_profit,
                "stop_loss_pct": levels.stop_loss_pct,
                "take_profit_pct": levels.take_profit_pct,
            },
        )

    def _broadcast(self, *, title: str, body: str, data: dict[str, Any] | None = None) -> int:
        if not _init_firebase():
            return 0
        from firebase_admin import messaging

        devices = self.list_devices()
        if not devices:
            logger.info("No FCM devices registered; skip push")
            return 0

        sent = 0
        for device in devices:
            try:
                message = messaging.Message(
                    notification=messaging.Notification(title=title, body=body),
                    data={k: str(v) for k, v in (data or {}).items()},
                    token=device.fcm_token,
                    webpush=messaging.WebpushConfig(
                        fcm_options=messaging.WebpushFCMOptions(
                            link="https://cryptosignals.btkdeals.com/signals/"
                        )
                    ),
                )
                messaging.send(message)
                sent += 1
            except Exception as exc:
                err = str(exc)
                logger.warning("FCM send failed id=%s: %s", device.id, err)
                if "not-found" in err.lower() or "registration-token" in err.lower():
                    db.session.delete(device)
        db.session.commit()
        logger.info("FCM sent to %s/%s devices", sent, len(devices))
        return sent
