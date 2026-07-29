from __future__ import annotations

from app.database import db
from app.models.mixins import TimestampMixin


class HistoricalCandle(TimestampMixin, db.Model):
    __tablename__ = "historical_candles"
    __table_args__ = (
        db.UniqueConstraint(
            "coin_id",
            "timeframe",
            "open_time",
            name="uq_candle_coin_tf_time",
        ),
        db.Index("ix_candles_coin_tf_time", "coin_id", "timeframe", "open_time"),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    coin_id = db.Column(db.Integer, db.ForeignKey("coins.id"), nullable=False)
    timeframe = db.Column(db.String(8), nullable=False)
    open_time = db.Column(db.DateTime(timezone=True), nullable=False)
    open = db.Column(db.Numeric(20, 8), nullable=False)
    high = db.Column(db.Numeric(20, 8), nullable=False)
    low = db.Column(db.Numeric(20, 8), nullable=False)
    close = db.Column(db.Numeric(20, 8), nullable=False)
    volume = db.Column(db.Numeric(24, 8), nullable=False)

    coin = db.relationship("Coin", backref=db.backref("historical_candles", lazy=True))
