from __future__ import annotations

from app.database import db
from app.models.mixins import TimestampMixin


class PushDevice(TimestampMixin, db.Model):
    __tablename__ = "push_devices"

    id = db.Column(db.Integer, primary_key=True)
    fcm_token = db.Column(db.String(512), nullable=False, unique=True, index=True)
    label = db.Column(db.String(128), nullable=True)
    user_agent = db.Column(db.String(512), nullable=True)
    enabled = db.Column(db.Boolean, nullable=False, default=True)
