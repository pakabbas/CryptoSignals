from __future__ import annotations

from app.database import db
from app.models.mixins import TimestampMixin


class IndicatorSetting(TimestampMixin, db.Model):
    __tablename__ = "indicator_settings"

    id = db.Column(db.Integer, primary_key=True)
    strategy_id = db.Column(db.Integer, db.ForeignKey("strategies.id"), nullable=False)
    indicator_key = db.Column(db.String(64), nullable=False)
    parameters_json = db.Column(db.JSON, nullable=False, default=dict)

    strategy = db.relationship("Strategy", backref=db.backref("indicator_settings", lazy=True))
