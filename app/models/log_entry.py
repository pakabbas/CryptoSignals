from __future__ import annotations

from app.database import db
from app.models.mixins import TimestampMixin


class LogEntry(TimestampMixin, db.Model):
    __tablename__ = "logs"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(32), nullable=False, index=True)
    level = db.Column(db.String(16), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    context_json = db.Column(db.JSON, nullable=True)
