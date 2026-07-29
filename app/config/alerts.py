"""Alert channel toggles."""

from __future__ import annotations

import os


def _enabled(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def email_alerts_enabled() -> bool:
    return _enabled("ENABLE_EMAIL_ALERTS", False)


def push_alerts_enabled() -> bool:
    return _enabled("ENABLE_PUSH_ALERTS", True)
