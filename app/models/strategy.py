from __future__ import annotations

from app.database import db
from app.models.mixins import TimestampMixin


class Strategy(TimestampMixin, db.Model):
    __tablename__ = "strategies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    definition_json = db.Column(db.JSON, nullable=False, default=dict)
    enabled = db.Column(db.Boolean, nullable=False, default=False)
    timeframe = db.Column(db.String(8), nullable=False, default="1H")

    def __repr__(self) -> str:
        return f"<Strategy {self.name} enabled={self.enabled}>"
