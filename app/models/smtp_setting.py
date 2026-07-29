from __future__ import annotations

from app.database import db
from app.models.mixins import TimestampMixin


class SmtpSetting(TimestampMixin, db.Model):
    __tablename__ = "smtp_settings"

    id = db.Column(db.Integer, primary_key=True)
    smtp_server = db.Column(db.String(255), nullable=False, default="")
    smtp_port = db.Column(db.Integer, nullable=False, default=587)
    username = db.Column(db.String(255), nullable=False, default="")
    password = db.Column(db.String(255), nullable=False, default="")
    use_tls = db.Column(db.Boolean, nullable=False, default=True)
    use_ssl = db.Column(db.Boolean, nullable=False, default=False)
    sender_email = db.Column(db.String(255), nullable=False, default="")
    receiver_email = db.Column(db.String(255), nullable=False, default="")
    subject_template = db.Column(
        db.String(255),
        nullable=False,
        default="Crypto Signal: {signal_type} {symbol}",
    )
