from __future__ import annotations

import atexit
import os

from flask import Flask

from app.config.settings import Config
from app.database import db
from app.database.bootstrap import ensure_database_exists
from app.routes import coins_bp, dashboard_bp, logs_bp, settings_bp
from app.services.coin_service import CoinService
from app.services.scheduler_service import SchedulerService
from app.services.settings_service import SettingsService
from app.utils.logging_setup import setup_logging


scheduler_service = SchedulerService()


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config["SQLALCHEMY_DATABASE_URI"] = config_class.database_uri()
    app.config["SCANNER_INTERVAL_SECONDS"] = config_class.SCANNER_INTERVAL_SECONDS
    app.config["PRIMARY_SYMBOL"] = config_class.PRIMARY_SYMBOL
    app.config["LOG_TO_DATABASE"] = True

    db.init_app(app)
    scheduler_service.init_app(app)

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(coins_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(logs_bp)

    testing = app.config.get("TESTING") or os.getenv("TESTING", "").lower() in {
        "1",
        "true",
        "yes",
    }

    with app.app_context():
        if not testing and app.config["SQLALCHEMY_DATABASE_URI"].startswith("mysql"):
            try:
                ensure_database_exists()
            except Exception as exc:
                app.logger.warning("Could not auto-create database: %s", exc)
        db.create_all()
        setup_logging(app)
        SettingsService().ensure_defaults()
        CoinService().ensure_primary_coin()

    if not testing:
        scheduler_service.start()
        atexit.register(scheduler_service.stop)

    return app
