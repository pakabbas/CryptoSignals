from __future__ import annotations

from flask import Blueprint, flash, jsonify, redirect, render_template, url_for

from app.scanner.scanner_service import ScannerService
from app.services.coin_service import CoinService
from app.services.scanner_dashboard_service import ScannerDashboardService
from app.services.settings_service import SettingsService
from app.services.signal_service import SignalService
from app.services.strategy_service import StrategyService

scanner_bp = Blueprint("scanner", __name__, url_prefix="/scanner")


def _scanner_context():
    settings = SettingsService().get_all()
    runtime = SettingsService().runtime_config()
    runtime["scanner_status"] = settings.get("scanner_status", "unknown")
    runtime["last_scan_time"] = settings.get("last_scan_time", "—")
    dashboard = ScannerDashboardService()
    tickers, live_views = dashboard.build()
    return {
        "runtime": runtime,
        "coins": [c for c in CoinService().list_coins() if c.enabled],
        "strategies": StrategyService().list_all(),
        "recent_signals": SignalService().recent(15),
        "tickers": tickers,
        "live_views": live_views,
        "side_progress": ScannerDashboardService.side_progress,
    }


@scanner_bp.route("/")
def index():
    return render_template("scanner/index.html", **_scanner_context())


@scanner_bp.route("/live.json")
def live_json():
    dashboard = ScannerDashboardService()
    tickers, live_views = dashboard.build()
    progress = ScannerDashboardService.side_progress

    def side_payload(side):
        if not side:
            return None
        p = progress(side)
        return {
            **p,
            "rules": [{"label": r.label, "met": r.met, "detail": r.detail} for r in side.rules],
        }

    return jsonify(
        {
            "tickers": [
                {
                    "symbol": t.symbol,
                    "price": t.price,
                    "change_pct": t.change_pct,
                    "volume": t.volume,
                    "error": t.error,
                }
                for t in tickers
            ],
            "views": [
                {
                    "strategy_id": v.strategy_id,
                    "strategy_name": v.strategy_name,
                    "coin_symbol": v.coin_symbol,
                    "timeframe": v.timeframe,
                    "enabled": v.enabled,
                    "price": v.price,
                    "signal_type": v.signal_type,
                    "long": side_payload(v.long),
                    "short": side_payload(v.short),
                    "next_close_at": v.next_close_at.isoformat() if v.next_close_at else None,
                    "error": v.error,
                }
                for v in live_views
            ],
        }
    )


@scanner_bp.route("/run", methods=["POST"])
def run_now():
    stats = ScannerService().run_scan()
    flash(
        f"Scan complete: {stats['signals']} new signal(s), {stats['errors']} error(s).",
        "success" if stats["errors"] == 0 else "warning",
    )
    return redirect(url_for("scanner.index"))
