from __future__ import annotations

import json

from flask import Blueprint, Response, flash, jsonify, redirect, render_template, request, url_for

from app.config.firebase_client import firebase_client_config, firebase_vapid_key, push_alerts_enabled
from app.services.push_service import PushNotificationService

push_bp = Blueprint("push", __name__)


@push_bp.route("/firebase-messaging-sw.js")
def service_worker():
    config = firebase_client_config()
    js = f"""importScripts('https://www.gstatic.com/firebasejs/12.16.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/12.16.0/firebase-messaging-compat.js');
firebase.initializeApp({json.dumps(config)});
firebase.messaging();
const messaging = firebase.messaging();
messaging.onBackgroundMessage(function (payload) {{
  const title = payload.notification?.title || "CryptoSignals";
  const options = {{
    body: payload.notification?.body || "",
    data: payload.data || {{}},
  }};
  self.registration.showNotification(title, options);
}});
self.addEventListener("notificationclick", function (event) {{
  event.notification.close();
  const url = event.notification.data?.url || "/signals/";
  event.waitUntil(clients.openWindow("https://cryptosignals.btkdeals.com" + url));
}});
"""
    return Response(js, mimetype="application/javascript; charset=utf-8")


@push_bp.route("/settings/notifications")
def notifications_settings():
    devices = PushNotificationService().list_devices()
    return render_template(
        "settings/notifications.html",
        devices=devices,
        firebase_config=firebase_client_config(),
        vapid_key=firebase_vapid_key(),
        push_enabled=push_alerts_enabled(),
    )


@push_bp.route("/settings/notifications/register", methods=["POST"])
def register():
    payload = request.get_json(silent=True) or {}
    token = payload.get("token") or request.form.get("token", "")
    try:
        PushNotificationService().register_token(
            token,
            user_agent=request.headers.get("User-Agent"),
            label=payload.get("label"),
        )
        return jsonify({"ok": True})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@push_bp.route("/settings/notifications/unregister", methods=["POST"])
def unregister():
    payload = request.get_json(silent=True) or {}
    token = payload.get("token") or ""
    if token:
        PushNotificationService().unregister_token(token)
    return jsonify({"ok": True})


@push_bp.route("/settings/notifications/test", methods=["POST"])
def test_push():
    try:
        count = PushNotificationService().send_test()
        if count:
            flash(f"Test push sent to {count} device(s).", "success")
        else:
            flash(
                "No push sent. Enable notifications in this browser and ensure Firebase service account is on the server.",
                "warning",
            )
    except Exception as exc:
        flash(f"Push test failed: {exc}", "danger")
    return redirect(url_for("push.notifications_settings"))
