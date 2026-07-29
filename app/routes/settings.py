from __future__ import annotations

from flask import Blueprint, Response, flash, redirect, render_template, request, url_for

from app.config.timeframes import SUPPORTED_TIMEFRAMES, normalize_timeframe, timeframe_label
from app.config.alerts import email_alerts_enabled
from app.exchanges.registry import list_supported_exchanges
from app.services.config_backup_service import ConfigBackupService
from app.services.email_service import EmailService
from app.services.settings_service import SettingsService

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/")
def index():
    service = SettingsService()
    smtp_row = service.get_smtp()
    smtp_configured = email_alerts_enabled() and bool(
        smtp_row.smtp_server
        and smtp_row.receiver_email
        and smtp_row.sender_email
    )
    return render_template(
        "settings/index.html",
        smtp=smtp_row,
        smtp_configured=smtp_configured,
        email_alerts_enabled=email_alerts_enabled(),
    )


@settings_bp.route("/general", methods=["GET", "POST"])
def general():
    service = SettingsService()
    if request.method == "POST":
        service.set_many(
            {
                "timezone": request.form.get("timezone", "UTC").strip(),
                "exchange": request.form.get("exchange", "binance").strip(),
                "scanner_interval_seconds": request.form.get("scanner_interval_seconds", "60").strip(),
                "default_timeframe": normalize_timeframe(
                    request.form.get("default_timeframe", "1H")
                ),
                "theme": request.form.get("theme", "light").strip(),
                "debug_mode": "true" if request.form.get("debug_mode") == "on" else "false",
            }
        )
        flash("General settings saved.", "success")
        return redirect(url_for("settings.general"))

    settings = service.get_all()
    exchanges = list_supported_exchanges()
    return render_template(
        "settings/general.html",
        settings=settings,
        exchanges=exchanges,
        timeframes=SUPPORTED_TIMEFRAMES,
        timeframe_labels=timeframe_label,
    )


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
                "sender_name": request.form.get("sender_name", "").strip(),
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

    return render_template(
        "settings/smtp.html",
        smtp=smtp_row,
        email_alerts_enabled=email_alerts_enabled(),
    )


@settings_bp.route("/smtp/test", methods=["POST"])
def smtp_test():
    if not email_alerts_enabled():
        flash("Email alerts are disabled on the server (ENABLE_EMAIL_ALERTS=false).", "warning")
        return redirect(url_for("settings.smtp"))
    service = SettingsService()
    smtp_row = service.get_smtp()
    try:
        EmailService().send_test_email(smtp_row)
        flash("Test email sent successfully.", "success")
    except Exception as exc:
        flash(f"Test email failed: {exc}", "danger")
    return redirect(url_for("settings.smtp"))


@settings_bp.route("/backup", methods=["GET", "POST"])
def backup():
    service = ConfigBackupService()
    if request.method == "POST" and request.form.get("action") == "import":
        raw = request.form.get("backup_json", "").strip()
        if not raw and "backup_file" in request.files:
            file = request.files["backup_file"]
            raw = file.read().decode("utf-8", errors="replace").strip()
        smtp_password = request.form.get("smtp_password", "").strip() or None
        try:
            stats = service.import_json(raw, smtp_password=smtp_password)
            flash(
                f"Import complete: {stats['settings']} settings, "
                f"{stats['strategies']} strategies, {stats['coins']} coins.",
                "success",
            )
        except Exception as exc:
            flash(f"Import failed: {exc}", "danger")
        return redirect(url_for("settings.backup"))

    preview = service.export_payload()
    return render_template("settings/backup.html", preview=preview)


@settings_bp.route("/backup/download")
def backup_download():
    payload = ConfigBackupService().export_json()
    return Response(
        payload,
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=cryptosignals-backup.json"},
    )
