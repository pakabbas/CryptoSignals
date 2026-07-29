from __future__ import annotations

from flask import Blueprint, render_template, request

from app.services.signal_service import SignalService

signals_bp = Blueprint("signals", __name__, url_prefix="/signals")


@signals_bp.route("/")
def index():
    limit = request.args.get("limit", 100, type=int)
    limit = max(10, min(limit, 500))
    entries = SignalService().recent(limit)
    return render_template("signals/index.html", signals=entries, limit=limit)
