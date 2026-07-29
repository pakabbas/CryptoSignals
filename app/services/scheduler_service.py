from __future__ import annotations

from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from flask import Flask

from app.database import db
from app.services.settings_service import SettingsService
from app.utils.logging_setup import get_logger

logger = get_logger("scanner")


class SchedulerService:
    """Background job infrastructure for the live scanner (Step 2)."""

    def __init__(self) -> None:
        self.scheduler = BackgroundScheduler(timezone="UTC")
        self.started = False

    def init_app(self, app: Flask) -> None:
        self.app = app

        @app.teardown_appcontext
        def shutdown_scheduler(exception: Exception | None) -> None:  # noqa: ARG001
            if exception:
                logger.warning("App context ended with exception")

    def start(self) -> None:
        if self.started:
            return
        interval = self.app.config.get("SCANNER_INTERVAL_SECONDS", 60)
        self.scheduler.add_job(
            self._heartbeat,
            trigger=IntervalTrigger(seconds=interval),
            id="scanner_heartbeat",
            replace_existing=True,
            max_instances=1,
        )
        self.scheduler.start()
        self.started = True
        logger.info("APScheduler started (interval=%ss)", interval)

    def stop(self) -> None:
        if self.started:
            self.scheduler.shutdown(wait=False)
            self.started = False
            logger.info("APScheduler stopped")

    def _heartbeat(self) -> None:
        with self.app.app_context():
            settings = SettingsService()
            now = datetime.now(timezone.utc).isoformat()
            settings.set_many(
                {
                    "last_scan_time": now,
                    "scanner_status": "idle (Step 1 — scanner not active yet)",
                }
            )
            logger.debug("Scanner heartbeat at %s", now)
