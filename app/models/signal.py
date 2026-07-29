from __future__ import annotations

from app.database import db
from app.models.mixins import TimestampMixin


class Signal(TimestampMixin, db.Model):
    __tablename__ = "signals"

    id = db.Column(db.Integer, primary_key=True)
    coin_id = db.Column(db.Integer, db.ForeignKey("coins.id"), nullable=False)
    strategy_id = db.Column(db.Integer, db.ForeignKey("strategies.id"), nullable=True)
    signal_type = db.Column(db.String(16), nullable=False)
    timeframe = db.Column(db.String(8), nullable=False)
    price = db.Column(db.Numeric(20, 8), nullable=False)
    candle_time = db.Column(db.DateTime(timezone=True), nullable=False)
    notified = db.Column(db.Boolean, nullable=False, default=False)

    coin = db.relationship("Coin", backref=db.backref("signals", lazy=True))
    strategy = db.relationship("Strategy", backref=db.backref("signals", lazy=True))
