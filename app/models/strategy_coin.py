from __future__ import annotations

from app.database import db

strategy_coins = db.Table(
    "strategy_coins",
    db.Column("strategy_id", db.Integer, db.ForeignKey("strategies.id"), primary_key=True),
    db.Column("coin_id", db.Integer, db.ForeignKey("coins.id"), primary_key=True),
)
