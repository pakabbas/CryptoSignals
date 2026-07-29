from __future__ import annotations

from app.database import db
from app.models.mixins import TimestampMixin


class BacktestResult(TimestampMixin, db.Model):
    __tablename__ = "backtest_results"

    id = db.Column(db.Integer, primary_key=True)
    strategy_id = db.Column(db.Integer, db.ForeignKey("strategies.id"), nullable=False)
    coin_id = db.Column(db.Integer, db.ForeignKey("coins.id"), nullable=False)
    timeframe = db.Column(db.String(8), nullable=False)
    period_days = db.Column(db.Integer, nullable=False)
    metrics_json = db.Column(db.JSON, nullable=False, default=dict)

    strategy = db.relationship("Strategy", backref=db.backref("backtest_results", lazy=True))
    coin = db.relationship("Coin", backref=db.backref("backtest_results", lazy=True))
