from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.risk.levels import stop_loss_pct, take_profit_pct
from app.services.signal_service import SignalService

signals_bp = Blueprint("signals", __name__, url_prefix="/signals")


@signals_bp.route("/")
def index():
    limit = request.args.get("limit", 100, type=int)
    limit = max(10, min(limit, 500))
    service = SignalService()
    entries = service.recent(limit)
    stats = service.summary_stats()
    return render_template(
        "signals/index.html",
        signals=entries,
        limit=limit,
        stats=stats,
        format_price=service.format_signal_price,
        stop_loss_pct=stop_loss_pct(),
        take_profit_pct=take_profit_pct(),
    )


@signals_bp.route("/check-status", methods=["POST"])
def check_status():
    service = SignalService()
    result = service.check_open_statuses()
    flash(
        (
            f"Checked {result['checked']} open signal(s): "
            f"{result['profit']} profit, {result['loss']} loss, "
            f"{result['still_open']} still open"
            + (f", {result['errors']} error(s)" if result["errors"] else "")
            + "."
        ),
        "success" if not result["errors"] else "warning",
    )
    return redirect(url_for("signals.index"))
