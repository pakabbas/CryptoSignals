from __future__ import annotations

from sqlalchemy import inspect, text

from app.database import db


def apply_schema_patches() -> None:
    """Lightweight column patches when Alembic is not used yet."""
    inspector = inspect(db.engine)
    if "smtp_settings" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("smtp_settings")}
    if "sender_name" not in columns:
        db.session.execute(
            text(
                "ALTER TABLE smtp_settings "
                "ADD COLUMN sender_name VARCHAR(128) NOT NULL DEFAULT ''"
            )
        )
        db.session.commit()
