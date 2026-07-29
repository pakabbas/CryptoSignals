from app.routes.coins import coins_bp
from app.routes.dashboard import dashboard_bp
from app.routes.health import health_bp
from app.routes.logs import logs_bp
from app.routes.scanner import scanner_bp
from app.routes.settings import settings_bp
from app.routes.signals import signals_bp

__all__ = [
    "coins_bp",
    "dashboard_bp",
    "health_bp",
    "logs_bp",
    "scanner_bp",
    "settings_bp",
    "signals_bp",
]
