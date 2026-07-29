from __future__ import annotations

from flask import Blueprint, render_template

from app.models import LogEntry, Signal
from app.services.coin_service import CoinService
from app.services.settings_service import SettingsService

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    settings_service = SettingsService()
    coin_service = CoinService()
    settings = settings_service.get_all()
    runtime = settings_service.runtime_config()
    runtime["scanner_status"] = settings.get("scanner_status", "idle")
    runtime["last_scan_time"] = settings.get("last_scan_time", "—")
    primary = coin_service.get_primary()
    enabled_coins = [c for c in coin_service.list_coins() if c.enabled]

    recent_signals = Signal.query.order_by(Signal.created_at.desc()).limit(10).all()
    recent_logs = LogEntry.query.order_by(LogEntry.created_at.desc()).limit(10).all()

    return render_template(
        "dashboard.html",
        runtime=runtime,
        settings=settings,
        primary_coin=primary,
        enabled_coins=enabled_coins,
        recent_signals=recent_signals,
        recent_logs=recent_logs,
        running_strategies=[],
    )
