from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, url_for

from app.scanner.scanner_service import ScannerService
from app.services.coin_service import CoinService
from app.services.settings_service import SettingsService
from app.services.signal_service import SignalService
from app.services.strategy_service import StrategyService

scanner_bp = Blueprint("scanner", __name__, url_prefix="/scanner")


@scanner_bp.route("/")
def index():
    settings = SettingsService().get_all()
    runtime = SettingsService().runtime_config()
    runtime["scanner_status"] = settings.get("scanner_status", "unknown")
    runtime["last_scan_time"] = settings.get("last_scan_time", "—")

    return render_template(
        "scanner/index.html",
        runtime=runtime,
        coins=[c for c in CoinService().list_coins() if c.enabled],
        strategies=StrategyService().list_all(),
        recent_signals=SignalService().recent(15),
    )


@scanner_bp.route("/run", methods=["POST"])
def run_now():
    stats = ScannerService().run_scan()
    flash(
        f"Scan complete: {stats['signals']} new signal(s), {stats['errors']} error(s).",
        "success" if stats["errors"] == 0 else "warning",
    )
    return redirect(url_for("scanner.index"))
