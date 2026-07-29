from __future__ import annotations

import os

from typing import Any

from flask import Request, jsonify


def api_key_configured() -> bool:
    return bool(os.getenv("API_KEY", "").strip())


def require_api_key(request: Request) -> tuple[None, None] | tuple[Any, int]:
    """Return (response, status) when unauthorized; (None, None) when OK or auth disabled."""
    expected = os.getenv("API_KEY", "").strip()
    if not expected:
        return None, None
    provided = request.headers.get("X-API-Key", "").strip()
    if provided != expected:
        return jsonify({"error": "Unauthorized", "message": "Invalid or missing X-API-Key"}), 401
    return None, None
