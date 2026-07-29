"""Public Firebase web client config (safe to expose to browsers)."""

from __future__ import annotations

import os


def firebase_client_config() -> dict[str, str]:
    return {
        "apiKey": os.getenv("FIREBASE_API_KEY", "AIzaSyAmgG-QWPfKICoEYqP4KzxwzA4em_aaq5Q"),
        "authDomain": os.getenv(
            "FIREBASE_AUTH_DOMAIN", "fleettrackingsys-1538422080392.firebaseapp.com"
        ),
        "projectId": os.getenv("FIREBASE_PROJECT_ID", "fleettrackingsys-1538422080392"),
        "storageBucket": os.getenv(
            "FIREBASE_STORAGE_BUCKET", "fleettrackingsys-1538422080392.firebasestorage.app"
        ),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", "454694337980"),
        "appId": os.getenv(
            "FIREBASE_APP_ID", "1:454694337980:web:9e783cbc6801dbeb5fbfb9"
        ),
    }


def firebase_vapid_key() -> str:
    return os.getenv(
        "FIREBASE_VAPID_KEY",
        "BBsDneLMfbyOivSUqe25gSx7vpXwC-CM3VQ8GmBVj6SQLn3ngSz3uDY-ntDXy-IQOKDw5JL5sLJBhBjrHu6wTM0",
    )


def push_alerts_enabled() -> bool:
    return os.getenv("ENABLE_PUSH_ALERTS", "true").lower() in {"1", "true", "yes", "on"}
