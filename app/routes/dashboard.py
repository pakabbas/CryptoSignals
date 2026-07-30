from __future__ import annotations

from collections import defaultdict
from typing import Any

from flask import Blueprint, render_template

from app.config.alerts import email_alerts_enabled, push_alerts_enabled
from app.config.firebase_client import firebase_client_config, firebase_vapid_key
from app.models import BacktestResult, LogEntry, Signal
from app.services.coin_service import CoinService
from app.services.settings_service import SettingsService
from app.services.strategy_service import StrategyService

dashboard_bp = Blueprint("dashboard", __name__)


def _symbol_short(symbol: str) -> str:
    return (symbol or "").split("/")[0] or symbol


def _signal_stats(signals: list[Signal]) -> dict[str, Any]:
    open_n = wins = losses = 0
    for s in signals:
        status = (s.status or "open").lower()
        if status == "profit":
            wins += 1
        elif status == "loss":
            losses += 1
        else:
            open_n += 1
    closed = wins + losses
    return {
        "total": len(signals),
        "open": open_n,
        "wins": wins,
        "losses": losses,
        "win_rate": (wins / closed * 100.0) if closed else 0.0,
    }


def _build_coin_panels(enabled_coins, strategies_by_coin) -> list[dict[str, Any]]:
    panels: list[dict[str, Any]] = []
    for coin in enabled_coins:
        strategies = strategies_by_coin.get(coin.id, [])
        recent = (
            Signal.query.filter_by(coin_id=coin.id)
            .order_by(Signal.created_at.desc())
            .limit(12)
            .all()
        )
        # Broader set for mini stats (last 50)
        stats_pool = (
            Signal.query.filter_by(coin_id=coin.id)
            .order_by(Signal.created_at.desc())
            .limit(50)
            .all()
        )
        latest_by_strategy: dict[int, Signal] = {}
        for sig in recent:
            if sig.strategy_id and sig.strategy_id not in latest_by_strategy:
                latest_by_strategy[sig.strategy_id] = sig

        backtests = (
            BacktestResult.query.filter_by(coin_id=coin.id)
            .order_by(BacktestResult.created_at.desc())
            .limit(8)
            .all()
        )
        strategy_rows = []
        for strategy in strategies:
            last = latest_by_strategy.get(strategy.id)
            strategy_signals = [
                sig for sig in recent if sig.strategy_id == strategy.id
            ][:8]
            strategy_backtests = [
                bt for bt in backtests if bt.strategy_id == strategy.id
            ][:3]
            strategy_rows.append(
                {
                    "strategy": strategy,
                    "last_signal": last,
                    "signals": strategy_signals,
                    "backtests": strategy_backtests,
                }
            )

        panels.append(
            {
                "coin": coin,
                "short": _symbol_short(coin.symbol),
                "strategies": strategy_rows,
                "signals": recent,
                "stats": _signal_stats(stats_pool),
                "backtests": backtests,
            }
        )
    return panels


@dashboard_bp.route("/")
def index():
    settings_service = SettingsService()
    coin_service = CoinService()
    strategy_service = StrategyService()
    settings = settings_service.get_all()
    runtime = settings_service.runtime_config()
    runtime["scanner_status"] = settings.get("scanner_status", "idle")
    runtime["last_scan_time"] = settings.get("last_scan_time", "—")
    primary = coin_service.get_primary()
    enabled_coins = [c for c in coin_service.list_coins() if c.enabled]
    all_enabled_strategies = strategy_service.list_enabled()

    strategies_by_coin: dict[int, list] = defaultdict(list)
    for coin in enabled_coins:
        strategies_by_coin[coin.id] = strategy_service.list_enabled_for_coin(coin.id)

    active_strategies = [
        strategy
        for strategy in all_enabled_strategies
        if strategy_service.list_enabled_coins_for_strategy(strategy.id)
    ]

    coin_panels = _build_coin_panels(enabled_coins, strategies_by_coin)
    recent_logs = LogEntry.query.order_by(LogEntry.created_at.desc()).limit(6).all()

    smtp_row = settings_service.get_smtp()
    smtp_configured = email_alerts_enabled() and bool(
        smtp_row.smtp_server and smtp_row.receiver_email
    )

    return render_template(
        "dashboard.html",
        runtime=runtime,
        settings=settings,
        primary_coin=primary,
        enabled_coins=enabled_coins,
        coin_panels=coin_panels,
        running_strategies=active_strategies,
        recent_logs=recent_logs,
        smtp=smtp_row,
        smtp_configured=smtp_configured,
        firebase_config=firebase_client_config(),
        vapid_key=firebase_vapid_key(),
        push_enabled=push_alerts_enabled(),
    )
