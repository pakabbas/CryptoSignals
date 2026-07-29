from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.database import db
from app.models import AppSetting, Coin, SmtpSetting, Strategy
from app.services.base import BaseService
from app.services.strategy_service import StrategyService
from app.utils.logging_setup import get_logger

logger = get_logger("app")

BACKUP_VERSION = 1


class ConfigBackupService(BaseService[AppSetting]):
    def export_payload(self) -> dict[str, Any]:
        smtp = SmtpSetting.query.first()
        smtp_data: dict[str, Any] | None = None
        if smtp:
            smtp_data = {
                "smtp_server": smtp.smtp_server,
                "smtp_port": smtp.smtp_port,
                "username": smtp.username,
                "use_tls": smtp.use_tls,
                "use_ssl": smtp.use_ssl,
                "sender_name": smtp.sender_name,
                "sender_email": smtp.sender_email,
                "receiver_email": smtp.receiver_email,
                "subject_template": smtp.subject_template,
            }

        strategies = []
        for strategy in Strategy.query.order_by(Strategy.name.asc()).all():
            strategies.append(
                {
                    "name": strategy.name,
                    "description": strategy.description,
                    "timeframe": strategy.timeframe,
                    "enabled": strategy.enabled,
                    "definition_json": strategy.definition_json,
                    "coin_symbols": [c.symbol for c in strategy.coins],
                }
            )

        coins = [
            {
                "symbol": coin.symbol,
                "enabled": coin.enabled,
                "exchange": coin.exchange,
                "group_name": coin.group_name,
            }
            for coin in Coin.query.order_by(Coin.symbol.asc()).all()
        ]

        settings = {row.key: row.value for row in AppSetting.query.all()}

        return {
            "version": BACKUP_VERSION,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "app_settings": settings,
            "smtp": smtp_data,
            "strategies": strategies,
            "coins": coins,
        }

    def export_json(self) -> str:
        return json.dumps(self.export_payload(), indent=2)

    def import_payload(self, payload: dict[str, Any], *, include_smtp_password: str | None = None) -> dict[str, int]:
        stats = {"settings": 0, "strategies": 0, "coins": 0, "smtp": 0}
        version = payload.get("version", 1)
        if version != BACKUP_VERSION:
            raise ValueError(f"Unsupported backup version: {version}")

        for key, value in (payload.get("app_settings") or {}).items():
            row = AppSetting.query.filter_by(key=key).first()
            if row:
                row.value = str(value)
            else:
                db.session.add(AppSetting(key=key, value=str(value)))
            stats["settings"] += 1

        for coin_data in payload.get("coins") or []:
            symbol = coin_data.get("symbol")
            if not symbol:
                continue
            coin = Coin.query.filter_by(symbol=symbol).first()
            if coin:
                coin.enabled = bool(coin_data.get("enabled", coin.enabled))
                if coin_data.get("exchange"):
                    coin.exchange = coin_data["exchange"]
                if "group_name" in coin_data:
                    coin.group_name = coin_data.get("group_name")
            else:
                coin = Coin(
                    symbol=symbol,
                    enabled=bool(coin_data.get("enabled", True)),
                    exchange=coin_data.get("exchange", "binance"),
                    group_name=coin_data.get("group_name"),
                )
                db.session.add(coin)
            stats["coins"] += 1

        db.session.commit()

        strategy_service = StrategyService()
        for item in payload.get("strategies") or []:
            name = (item.get("name") or "Imported").strip()
            if Strategy.query.filter_by(name=name).first():
                name = f"{name} (imported {datetime.now(timezone.utc).strftime('%Y%m%d%H%M')})"
            raw = json.dumps(item)
            strategy_service.import_json(raw, replace_name=name)
            stats["strategies"] += 1

        smtp_data = payload.get("smtp")
        if smtp_data:
            smtp = SmtpSetting.query.first()
            if smtp is None:
                smtp = SmtpSetting()
                db.session.add(smtp)
            for field in (
                "smtp_server",
                "smtp_port",
                "username",
                "use_tls",
                "use_ssl",
                "sender_name",
                "sender_email",
                "receiver_email",
                "subject_template",
            ):
                if field in smtp_data:
                    setattr(smtp, field, smtp_data[field])
            if include_smtp_password:
                smtp.password = include_smtp_password
            db.session.commit()
            stats["smtp"] = 1

        logger.info("Configuration import complete: %s", stats)
        return stats

    def import_json(self, raw: str, *, smtp_password: str | None = None) -> dict[str, int]:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError("Backup must be a JSON object")
        return self.import_payload(payload, include_smtp_password=smtp_password)
