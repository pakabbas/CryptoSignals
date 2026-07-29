from __future__ import annotations

from app.database import db
from app.models.mixins import TimestampMixin


class AppSetting(TimestampMixin, db.Model):
    __tablename__ = "app_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), nullable=False, unique=True, index=True)
    value = db.Column(db.Text, nullable=False, default="")
