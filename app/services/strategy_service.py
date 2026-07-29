from __future__ import annotations

import copy
import json
from typing import Any

from app.database import db
from app.models import Coin, Strategy
from app.services.base import BaseService
from app.strategies.defaults import DEFAULT_STRATEGIES
from app.strategies.validator import StrategyValidationError, validate_definition
from app.utils.logging_setup import get_logger

logger = get_logger("strategy")


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
        self._assign_all_enabled_coins_to_defaults()

    def attach_new_enabled_coins_to_active_strategies(self) -> None:
        """Add newly seeded enabled coins to strategies that already monitor at least one pair."""
        enabled = Coin.query.filter_by(enabled=True).order_by(Coin.symbol.asc()).all()
        if not enabled:
            return
        for strategy in Strategy.query.filter_by(enabled=True).all():
            linked_ids = {c.id for c in strategy.coins}
            if not linked_ids:
                strategy.coins = list(enabled)
                continue
            for coin in enabled:
                if coin.id not in linked_ids:
                    strategy.coins.append(coin)
        db.session.commit()

    def _assign_all_enabled_coins_to_defaults(self) -> None:
        coins = Coin.query.filter_by(enabled=True).all()
        if not coins:
            return
        for strategy in Strategy.query.all():
            if not strategy.coins:
                strategy.coins = coins
        db.session.commit()

    def get(self, strategy_id: int) -> Strategy:
        return Strategy.query.get_or_404(strategy_id)

    def list_enabled(self) -> list[Strategy]:
        return Strategy.query.filter_by(enabled=True).order_by(Strategy.name.asc()).all()

    def list_enabled_for_coin(self, coin_id: int) -> list[Strategy]:
        return (
            Strategy.query.filter_by(enabled=True)
            .filter(Strategy.coins.any(Coin.id == coin_id))
            .order_by(Strategy.name.asc())
            .all()
        )

    def list_all(self) -> list[Strategy]:
        return Strategy.query.order_by(Strategy.name.asc()).all()

    def create(
        self,
        *,
        name: str,
        description: str | None,
        timeframe: str,
        definition_json: dict[str, Any],
        enabled: bool,
        coin_ids: list[int],
    ) -> Strategy:
        validate_definition(definition_json)
        if Strategy.query.filter_by(name=name.strip()).first():
            raise StrategyValidationError("Strategy name already exists")

        strategy = Strategy(
            name=name.strip(),
            description=description,
            definition_json=definition_json,
            enabled=enabled,
            timeframe=timeframe,
        )
        strategy.coins = self._resolve_coins(coin_ids)
        db.session.add(strategy)
        db.session.commit()
        logger.info("Created strategy %s", strategy.name)
        return strategy

    def update(
        self,
        strategy_id: int,
        *,
        name: str,
        description: str | None,
        timeframe: str,
        definition_json: dict[str, Any],
        enabled: bool,
        coin_ids: list[int],
    ) -> Strategy:
        validate_definition(definition_json)
        strategy = self.get(strategy_id)
        duplicate = Strategy.query.filter(Strategy.name == name.strip(), Strategy.id != strategy_id).first()
        if duplicate:
            raise StrategyValidationError("Strategy name already exists")

        strategy.name = name.strip()
        strategy.description = description
        strategy.timeframe = timeframe
        strategy.definition_json = definition_json
        strategy.enabled = enabled
        strategy.coins = self._resolve_coins(coin_ids)
        db.session.commit()
        logger.info("Updated strategy %s", strategy.name)
        return strategy

    def delete(self, strategy_id: int) -> None:
        strategy = self.get(strategy_id)
        db.session.delete(strategy)
        db.session.commit()
        logger.info("Deleted strategy id=%s", strategy_id)

    def clone(self, strategy_id: int) -> Strategy:
        source = self.get(strategy_id)
        base_name = f"{source.name} (copy)"
        name = base_name
        counter = 2
        while Strategy.query.filter_by(name=name).first():
            name = f"{base_name} {counter}"
            counter += 1

        clone = Strategy(
            name=name,
            description=source.description,
            definition_json=copy.deepcopy(source.definition_json),
            enabled=False,
            timeframe=source.timeframe,
        )
        clone.coins = list(source.coins)
        db.session.add(clone)
        db.session.commit()
        logger.info("Cloned strategy %s -> %s", source.name, clone.name)
        return clone

    def set_enabled(self, strategy_id: int, enabled: bool) -> Strategy:
        strategy = self.get(strategy_id)
        strategy.enabled = enabled
        db.session.commit()
        return strategy

    def export_json(self, strategy_id: int) -> str:
        strategy = self.get(strategy_id)
        payload = {
            "name": strategy.name,
            "description": strategy.description,
            "timeframe": strategy.timeframe,
            "enabled": strategy.enabled,
            "definition_json": strategy.definition_json,
            "coin_symbols": [coin.symbol for coin in strategy.coins],
        }
        return json.dumps(payload, indent=2)

    def import_json(self, raw: str, *, replace_name: str | None = None) -> Strategy:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise StrategyValidationError(f"Invalid JSON: {exc}") from exc

        definition = payload.get("definition_json", payload.get("definition"))
        if not definition:
            raise StrategyValidationError("Import file must include definition_json")

        name = (replace_name or payload.get("name") or "Imported strategy").strip()
        if Strategy.query.filter_by(name=name).first():
            raise StrategyValidationError(f"Strategy name '{name}' already exists")

        coin_ids: list[int] = []
        for symbol in payload.get("coin_symbols", []):
            coin = Coin.query.filter_by(symbol=symbol).first()
            if coin:
                coin_ids.append(coin.id)

        return self.create(
            name=name,
            description=payload.get("description"),
            timeframe=payload.get("timeframe", "1H"),
            definition_json=definition,
            enabled=bool(payload.get("enabled", False)),
            coin_ids=coin_ids or [c.id for c in Coin.query.filter_by(enabled=True).all()],
        )

    def _resolve_coins(self, coin_ids: list[int]) -> list[Coin]:
        if not coin_ids:
            return []
        return Coin.query.filter(Coin.id.in_(coin_ids)).all()
