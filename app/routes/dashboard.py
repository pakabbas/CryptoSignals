from __future__ import annotations

from flask import Blueprint, render_template

from app.config.firebase_client import firebase_client_config, firebase_vapid_key, push_alerts_enabled
from app.models import LogEntry, Signal
from app.services.coin_service import CoinService
from app.services.settings_service import SettingsService
from app.services.strategy_service import StrategyService

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

    smtp_row = settings_service.get_smtp()
    smtp_configured = bool(smtp_row.smtp_server and smtp_row.receiver_email)

    return render_template(
        "dashboard.html",
        runtime=runtime,
        settings=settings,
        primary_coin=primary,
        enabled_coins=enabled_coins,
        recent_signals=recent_signals,
        recent_logs=recent_logs,
        running_strategies=StrategyService().list_enabled(),
        smtp=smtp_row,
        smtp_configured=smtp_configured,
        firebase_config=firebase_client_config(),
        vapid_key=firebase_vapid_key(),
        push_enabled=push_alerts_enabled(),
    )
