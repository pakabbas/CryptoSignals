from __future__ import annotations

from flask import Blueprint, current_app, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "CryptoSignals",
            "db_ready": bool(current_app.config.get("DB_READY", True)),
        }
    ), 200
