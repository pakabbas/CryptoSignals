from __future__ import annotations

from typing import Any

from flask import current_app

from app.config.settings import Config
from app.database import db
from app.models import AppSetting, SmtpSetting
from app.services.base import BaseService
from app.utils.logging_setup import get_logger

logger = get_logger("app")

DEFAULT_APP_SETTINGS: dict[str, str] = {
    "timezone": Config.TIMEZONE,
    "exchange": Config.EXCHANGE,
    "scanner_interval_seconds": str(Config.SCANNER_INTERVAL_SECONDS),
    "default_timeframe": Config.DEFAULT_TIMEFRAME,
    "theme": Config.THEME,
    "debug_mode": "false",
    "last_scan_time": "",
    "scanner_status": "idle",
}


class SettingsService(BaseService[AppSetting]):
    def ensure_defaults(self) -> None:
        for key, value in DEFAULT_APP_SETTINGS.items():
            if not AppSetting.query.filter_by(key=key).first():
                db.session.add(AppSetting(key=key, value=value))
        if not SmtpSetting.query.first():
            db.session.add(SmtpSetting())
        db.session.commit()
        logger.info("Default application and SMTP settings ensured")

    def get_all(self) -> dict[str, str]:
        settings = {row.key: row.value for row in AppSetting.query.all()}
        for key, value in DEFAULT_APP_SETTINGS.items():
            settings.setdefault(key, value)
        return settings

    def get(self, key: str, default: str = "") -> str:
        row = AppSetting.query.filter_by(key=key).first()
        if row:
            return row.value
        return DEFAULT_APP_SETTINGS.get(key, default)

    def set_many(self, values: dict[str, str]) -> None:
        for key, value in values.items():
            row = AppSetting.query.filter_by(key=key).first()
            if row:
                row.value = value
            else:
                db.session.add(AppSetting(key=key, value=value))
        db.session.commit()
        logger.info("Application settings updated: %s", ", ".join(values.keys()))

    def get_smtp(self) -> SmtpSetting:
        row = SmtpSetting.query.first()
        if row is None:
            row = SmtpSetting()
            db.session.add(row)
            db.session.commit()
        return row

    def update_smtp(self, data: dict[str, Any]) -> SmtpSetting:
        smtp = self.get_smtp()
        payload = dict(data)
        password = payload.get("password", "")
        if password is not None and not str(password).strip():
            payload.pop("password", None)
        for field in (
            "smtp_server",
            "smtp_port",
            "username",
            "password",
            "use_tls",
            "use_ssl",
            "sender_name",
            "sender_email",
            "receiver_email",
            "subject_template",
        ):
            if field in payload:
                value = payload[field]
                if field == "password":
                    value = str(value).replace(" ", "")
                setattr(smtp, field, value)
        if smtp.smtp_port == 587 and smtp.use_ssl:
            smtp.use_ssl = False
            smtp.use_tls = True
        db.session.commit()
        logger.info("SMTP settings updated")
        return smtp

    def runtime_config(self) -> dict[str, Any]:
        settings = self.get_all()
        return {
            "timezone": settings.get("timezone", Config.TIMEZONE),
            "exchange": settings.get("exchange", Config.EXCHANGE),
            "scanner_interval_seconds": int(
                settings.get("scanner_interval_seconds", Config.SCANNER_INTERVAL_SECONDS)
            ),
            "default_timeframe": settings.get("default_timeframe", Config.DEFAULT_TIMEFRAME),
            "theme": settings.get("theme", Config.THEME),
            "debug_mode": settings.get("debug_mode", "false").lower() == "true",
            "primary_symbol": current_app.config.get("PRIMARY_SYMBOL", Config.PRIMARY_SYMBOL),
        }
