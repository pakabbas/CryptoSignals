from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.exchanges.registry import list_supported_exchanges
from app.indicators import list_indicator_names
from app.models import Signal
from app.services.backtest_service import BacktestService
from app.services.coin_service import CoinService
from app.services.strategy_service import StrategyService
from app.utils.api_auth import require_api_key

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


@api_bp.before_request
def _guard_api():
    body, status = require_api_key(request)
    if body is not None:
        return body, status


@api_bp.route("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "CryptoSignals",
            "db_ready": bool(current_app.config.get("DB_READY", True)),
        }
    )


@api_bp.route("/exchanges")
def exchanges():
    return jsonify({"exchanges": list_supported_exchanges()})


@api_bp.route("/indicators")
def indicators():
    return jsonify({"indicators": list_indicator_names()})


@api_bp.route("/coins")
def coins():
    rows = CoinService().list_coins()
    return jsonify(
        {
            "coins": [
                {
                    "id": c.id,
                    "symbol": c.symbol,
                    "enabled": c.enabled,
                    "exchange": c.exchange,
                    "group_name": c.group_name,
                }
                for c in rows
            ]
        }
    )


@api_bp.route("/strategies")
def strategies():
    rows = StrategyService().list_all()
    return jsonify(
        {
            "strategies": [
                {
                    "id": s.id,
                    "name": s.name,
                    "enabled": s.enabled,
                    "timeframe": s.timeframe,
                    "coin_symbols": [c.symbol for c in s.coins],
                }
                for s in rows
            ]
        }
    )


@api_bp.route("/signals")
def signals_list():
    limit = min(request.args.get("limit", 50, type=int) or 50, 200)
    rows = Signal.query.order_by(Signal.created_at.desc()).limit(limit).all()
    return jsonify(
        {
            "signals": [
                {
                    "id": s.id,
                    "coin_id": s.coin_id,
                    "symbol": s.coin.symbol if s.coin else None,
                    "strategy_id": s.strategy_id,
                    "strategy_name": s.strategy.name if s.strategy else None,
                    "signal_type": s.signal_type,
                    "timeframe": s.timeframe,
                    "price": str(s.price),
                    "candle_time": s.candle_time.isoformat() if s.candle_time else None,
                    "notified": s.notified,
                }
                for s in rows
            ]
        }
    )


@api_bp.route("/backtests")
def backtests():
    limit = min(request.args.get("limit", 20, type=int) or 20, 100)
    rows = BacktestService().list_recent(limit)
    return jsonify(
        {
            "backtests": [
                {
                    "id": r.id,
                    "strategy_id": r.strategy_id,
                    "coin_id": r.coin_id,
                    "period_days": r.period_days,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]
        }
    )
