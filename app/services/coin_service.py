from __future__ import annotations

from flask import current_app

from sqlalchemy import func

from app.database import db
from app.models import Coin
from app.services.base import BaseService
from app.utils.logging_setup import get_logger

logger = get_logger("app")


class CoinService(BaseService[Coin]):
    def ensure_primary_coin(self) -> Coin:
        symbol = current_app.config.get("PRIMARY_SYMBOL", "BTC/USDT")
        coin = Coin.query.filter_by(symbol=symbol).first()
        if coin is None:
            coin = Coin(symbol=symbol, exchange="binance", enabled=True, group_name="primary")
            db.session.add(coin)
            db.session.commit()
            logger.info("Seeded primary coin %s", symbol)
        return coin

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
