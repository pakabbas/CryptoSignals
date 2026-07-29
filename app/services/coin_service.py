from __future__ import annotations

from flask import current_app

from sqlalchemy import func

from app.database import db
from app.models import Coin
from app.services.base import BaseService
from app.services.settings_service import SettingsService
from app.utils.logging_setup import get_logger

logger = get_logger("app")

# Active monitored pairs (others stay seeded but disabled).
ACTIVE_COIN_SYMBOLS: tuple[str, ...] = ("BTC/USDT", "SOL/USDT")

# Per-pair market data source (matches Coins UI on production).
DEFAULT_COIN_EXCHANGES: dict[str, str] = {
    "BTC/USDT": "kraken",
    "ETH/USDT": "kraken",
    "SOL/USDT": "kraken",
    "DOGE/USDT": "kraken",
}


class CoinService(BaseService[Coin]):
    def _default_symbols(self) -> tuple[str, ...]:
        raw = current_app.config.get("DEFAULT_SYMBOLS")
        if raw:
            return tuple(raw)
        return ("BTC/USDT", "ETH/USDT", "SOL/USDT", "DOGE/USDT")

    def _default_exchange(self) -> str:
        try:
            return SettingsService().get("exchange", "kraken").strip().lower() or "kraken"
        except Exception:
            return current_app.config.get("EXCHANGE", "kraken")

    def ensure_primary_coin(self) -> Coin:
        """Backward-compatible entry: ensure all default pairs exist."""
        coins = self.ensure_default_coins()
        primary = self.get_primary()
        return primary or coins[0]

    def ensure_default_coins(self) -> list[Coin]:
        exchange = self._default_exchange()
        created_any = False
        updated_any = False
        result: list[Coin] = []
        primary_symbol = current_app.config.get("PRIMARY_SYMBOL", "BTC/USDT")

        for symbol in self._default_symbols():
            desired_exchange = DEFAULT_COIN_EXCHANGES.get(symbol, exchange)
            should_enable = symbol in ACTIVE_COIN_SYMBOLS
            coin = Coin.query.filter_by(symbol=symbol).first()
            if coin is None:
                group = "primary" if symbol == primary_symbol else "alt"
                coin = Coin(
                    symbol=symbol,
                    exchange=desired_exchange,
                    enabled=should_enable,
                    group_name=group,
                )
                db.session.add(coin)
                created_any = True
                logger.info("Seeded coin %s (%s) enabled=%s", symbol, desired_exchange, should_enable)
            else:
                if symbol in DEFAULT_COIN_EXCHANGES and coin.exchange != desired_exchange:
                    coin.exchange = desired_exchange
                    updated_any = True
                    logger.info("Updated coin %s exchange -> %s", symbol, desired_exchange)
                if coin.enabled != should_enable:
                    coin.enabled = should_enable
                    updated_any = True
                    logger.info("Updated coin %s enabled -> %s", symbol, should_enable)
            result.append(coin)

        if created_any or updated_any:
            db.session.commit()
        if created_any or updated_any:
            from app.services.strategy_service import StrategyService

            StrategyService().attach_new_enabled_coins_to_active_strategies()

        return result

    def list_coins(self, search: str | None = None) -> list[Coin]:
        query = Coin.query.order_by(Coin.symbol.asc())
        if search:
            term = f"%{search.strip()}%"
            query = query.filter(func.lower(Coin.symbol).like(term.lower()))
        return query.all()

    def get_primary(self) -> Coin | None:
        symbol = current_app.config.get("PRIMARY_SYMBOL", "BTC/USDT")
        return Coin.query.filter_by(symbol=symbol).first()

    def set_enabled(self, coin_id: int, enabled: bool) -> Coin:
        coin = Coin.query.get_or_404(coin_id)
        coin.enabled = enabled
        db.session.commit()
        logger.info("Coin %s enabled=%s", coin.symbol, enabled)
        return coin

    def update_group(self, coin_id: int, group_name: str | None) -> Coin:
        coin = Coin.query.get_or_404(coin_id)
        coin.group_name = group_name or None
        db.session.commit()
        return coin
