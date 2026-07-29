from __future__ import annotations

from sqlalchemy import inspect, text

from app.database import db


def apply_schema_patches() -> None:
    """Lightweight column patches when Alembic is not used yet."""
    inspector = inspect(db.engine)
    tables = set(inspector.get_table_names())

    if "smtp_settings" in tables:
        columns = {col["name"] for col in inspector.get_columns("smtp_settings")}
        if "sender_name" not in columns:
            db.session.execute(
                text(
                    "ALTER TABLE smtp_settings "
                    "ADD COLUMN sender_name VARCHAR(128) NOT NULL DEFAULT ''"
                )
            )
            db.session.commit()

    if "signals" in tables:
        columns = {col["name"] for col in inspector.get_columns("signals")}
        patches = [
            ("status", "ALTER TABLE signals ADD COLUMN status VARCHAR(16) NOT NULL DEFAULT 'open'"),
            ("stop_loss", "ALTER TABLE signals ADD COLUMN stop_loss DECIMAL(20,8) NULL"),
            ("take_profit", "ALTER TABLE signals ADD COLUMN take_profit DECIMAL(20,8) NULL"),
            ("exit_price", "ALTER TABLE signals ADD COLUMN exit_price DECIMAL(20,8) NULL"),
            ("exit_time", "ALTER TABLE signals ADD COLUMN exit_time DATETIME NULL"),
            ("pnl_pct", "ALTER TABLE signals ADD COLUMN pnl_pct DECIMAL(12,4) NULL"),
            ("checked_at", "ALTER TABLE signals ADD COLUMN checked_at DATETIME NULL"),
        ]
        for name, sql in patches:
            if name not in columns:
                db.session.execute(text(sql))
        db.session.commit()
