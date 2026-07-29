from __future__ import annotations

from typing import Generic, TypeVar

from app.database import db

T = TypeVar("T")


class BaseService(Generic[T]):
    """Shared database helpers for service classes."""

    def __init__(self) -> None:
        self.db = db

    def commit(self) -> None:
        self.db.session.commit()

    def rollback(self) -> None:
        self.db.session.rollback()

    def flush(self) -> None:
        self.db.session.flush()
