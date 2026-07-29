from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.services.settings_service import SettingsService

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/general", methods=["GET", "POST"])
def general():
    service = SettingsService()
    if request.method == "POST":
        service.set_many(
            {
                "timezone": request.form.get("timezone", "UTC").strip(),
                "exchange": request.form.get("exchange", "binance").strip(),
                "scanner_interval_seconds": request.form.get("scanner_interval_seconds", "60").strip(),
                "default_timeframe": request.form.get("default_timeframe", "1H").strip(),
                "theme": request.form.get("theme", "light").strip(),
                "debug_mode": "true" if request.form.get("debug_mode") == "on" else "false",
            }
        )
        flash("General settings saved.", "success")
        return redirect(url_for("settings.general"))

    settings = service.get_all()
    return render_template("settings/general.html", settings=settings)


@settings_bp.route("/smtp", methods=["GET", "POST"])
def smtp():
    service = SettingsService()
    smtp_row = service.get_smtp()

    if request.method == "POST":
        service.update_smtp(
            {
                "smtp_server": request.form.get("smtp_server", "").strip(),
                "smtp_port": request.form.get("smtp_port", 587, type=int),
                "username": request.form.get("username", "").strip(),
                "password": request.form.get("password", ""),
                "use_tls": request.form.get("use_tls") == "on",
                "use_ssl": request.form.get("use_ssl") == "on",
                "sender_email": request.form.get("sender_email", "").strip(),
                "receiver_email": request.form.get("receiver_email", "").strip(),
                "subject_template": request.form.get(
                    "subject_template",
                    "Crypto Signal: {signal_type} {symbol}",
                ).strip(),
            }
        )
        flash("SMTP settings saved.", "success")
        return redirect(url_for("settings.smtp"))

    return render_template("settings/smtp.html", smtp=smtp_row)


@settings_bp.route("/smtp/test", methods=["POST"])
def smtp_test():
    flash("Test email will be implemented in Step 2.", "info")
    return redirect(url_for("settings.smtp"))
