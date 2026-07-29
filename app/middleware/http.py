from __future__ import annotations

import uuid

from flask import Flask, g, jsonify, render_template, request

from app.utils.logging_setup import get_logger

logger = get_logger("app")


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Not found", "path": request.path}), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        logger.exception("Unhandled error: %s", error)
        if request.path.startswith("/api/"):
            return jsonify({"error": "Internal server error"}), 500
        return render_template("errors/500.html"), 500

    @app.errorhandler(400)
    def bad_request(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Bad request", "message": str(error)}), 400
        return render_template("errors/500.html", message=str(error)), 400


def register_request_hooks(app: Flask) -> None:
    @app.before_request
    def assign_request_id():
        g.request_id = uuid.uuid4().hex[:12]

    @app.after_request
    def log_request(response):
        if app.config.get("TESTING"):
            return response
        logger.info(
            "%s %s -> %s [%s]",
            request.method,
            request.path,
            response.status_code,
            getattr(g, "request_id", "-"),
        )
        response.headers["X-Request-Id"] = getattr(g, "request_id", "")
        return response
