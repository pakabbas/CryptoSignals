from __future__ import annotations

from app.database import db
from app.models.mixins import TimestampMixin


class Coin(TimestampMixin, db.Model):
    __tablename__ = "coins"

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(32), nullable=False, unique=True, index=True)
    exchange = db.Column(db.String(32), nullable=False, default="binance")
    enabled = db.Column(db.Boolean, nullable=False, default=True)
    group_name = db.Column(db.String(64), nullable=True)

    def __repr__(self) -> str:
        return f"<Coin {self.symbol} enabled={self.enabled}>"
