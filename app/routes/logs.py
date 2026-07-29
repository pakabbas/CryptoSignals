from __future__ import annotations

from flask import Blueprint, render_template, request

from app.models import LogEntry

logs_bp = Blueprint("logs", __name__, url_prefix="/logs")


@logs_bp.route("/")
def index():
    category = request.args.get("category", "").strip()
    query = LogEntry.query.order_by(LogEntry.created_at.desc())
    if category:
        query = query.filter_by(category=category)
    entries = query.limit(200).all()
    return render_template("logs/index.html", entries=entries, category=category)
