from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, has_app_context

from app.database import db
from app.models import LogEntry


class DatabaseLogHandler(logging.Handler):
    """Persists log records to the logs table."""

    def __init__(self, app: Flask, category: str) -> None:
        super().__init__()
        self.app = app
        self.category = category

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
            entry = LogEntry(
                category=self.category,
                level=record.levelname,
                message=message,
                context_json={
                    "logger": record.name,
                    "module": record.module,
                    "funcName": record.funcName,
                },
            )
            if has_app_context():
                db.session.add(entry)
                db.session.commit()
            else:
                with self.app.app_context():
                    db.session.add(entry)
                    db.session.commit()
        except Exception:
            try:
                if has_app_context():
                    db.session.rollback()
                else:
                    with self.app.app_context():
                        db.session.rollback()
            except Exception:
                pass


def setup_logging(app: Flask) -> None:
    log_dir: Path = app.config["LOG_DIR"]
    log_dir.mkdir(parents=True, exist_ok=True)

    level = getattr(logging, app.config.get("LOG_LEVEL", "INFO"), logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    categories = ("app", "scanner", "strategy", "email")
    for category in categories:
        logger = logging.getLogger(f"crypto.{category}")
        logger.setLevel(level)
        logger.propagate = False
        if logger.handlers:
            continue

        file_handler = RotatingFileHandler(
            log_dir / f"{category}.log",
            maxBytes=2_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        if app.config.get("LOG_TO_DATABASE", True):
            db_handler = DatabaseLogHandler(app=app, category=category)
            db_handler.setLevel(level)
            db_handler.setFormatter(formatter)
            logger.addHandler(db_handler)

    logging.getLogger("crypto.app").info("Logging initialized")


def get_logger(category: str) -> logging.Logger:
    return logging.getLogger(f"crypto.{category}")
