from __future__ import annotations

from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from flask import Flask

from app.scanner.scanner_service import ScannerService
from app.services.settings_service import SettingsService
from app.utils.logging_setup import get_logger

logger = get_logger("scanner")


class SchedulerService:
    """Background scanner jobs via APScheduler."""

    def __init__(self) -> None:
        self.scheduler = BackgroundScheduler(timezone="UTC")
        self.started = False
        self.scanner = ScannerService()

    def init_app(self, app: Flask) -> None:
        self.app = app

    def start(self) -> None:
        if self.started:
            return
        interval = self.app.config.get("SCANNER_INTERVAL_SECONDS", 60)
        self.scheduler.add_job(
            self._run_scan,
            trigger=IntervalTrigger(seconds=interval),
            id="live_scanner",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        self.scheduler.start()
        self.started = True
        logger.info("APScheduler scanner started (interval=%ss)", interval)

    def stop(self) -> None:
        if self.started:
            self.scheduler.shutdown(wait=False)
            self.started = False
            logger.info("APScheduler stopped")

    def _run_scan(self) -> None:
        with self.app.app_context():
            stats = self.scanner.run_scan()
            logger.info("Scan finished: %s", stats)

    def run_once(self) -> dict:
        with self.app.app_context():
            return self.scanner.run_scan()
