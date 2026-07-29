from __future__ import annotations

from app.database import db
from app.models import Strategy
from app.services.base import BaseService
from app.strategies.defaults import DEFAULT_STRATEGIES
from app.utils.logging_setup import get_logger

logger = get_logger("app")


class StrategyService(BaseService[Strategy]):
    def ensure_default_strategies(self) -> None:
        for item in DEFAULT_STRATEGIES:
            existing = Strategy.query.filter_by(name=item["name"]).first()
            if existing:
                continue
            strategy = Strategy(
                name=item["name"],
                description=item.get("description"),
                definition_json=item["definition_json"],
                enabled=bool(item.get("enabled", False)),
                timeframe=item.get("timeframe", "1H"),
            )
            db.session.add(strategy)
            logger.info("Seeded strategy %s", item["name"])
        db.session.commit()

    def list_enabled(self) -> list[Strategy]:
        return Strategy.query.filter_by(enabled=True).order_by(Strategy.name.asc()).all()

    def list_all(self) -> list[Strategy]:
        return Strategy.query.order_by(Strategy.name.asc()).all()
