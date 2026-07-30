from __future__ import annotations

from collections import defaultdict
from typing import Any

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from app.config.timeframes import SUPPORTED_TIMEFRAMES, normalize_timeframe, timeframe_label
from app.scanner.scanner_service import ScannerService
from app.services.coin_service import CoinService
from app.services.scanner_dashboard_service import (
    CoinTicker,
    ScannerDashboardService,
    StrategyLiveView,
)
from app.services.settings_service import SettingsService
from app.services.signal_service import SignalService
from app.services.strategy_service import StrategyService

scanner_bp = Blueprint("scanner", __name__, url_prefix="/scanner")


def _display_timeframe() -> str:
    settings = SettingsService().get_all()
    default = normalize_timeframe(settings.get("default_timeframe", "1H"))
    return normalize_timeframe(request.args.get("tf", default))


def _symbol_short(symbol: str) -> str:
    return (symbol or "").split("/")[0] or symbol


def _build_coin_panels(
    coins: list,
    tickers: list[CoinTicker],
    live_views: list[StrategyLiveView],
    recent_signals: list,
) -> list[dict[str, Any]]:
    ticker_by_id = {t.coin_id: t for t in tickers}
    views_by_symbol: dict[str, list[StrategyLiveView]] = defaultdict(list)
    for view in live_views:
        views_by_symbol[view.coin_symbol].append(view)

    signals_by_coin: dict[int, list] = defaultdict(list)
    for signal in recent_signals:
        if signal.coin_id:
            signals_by_coin[signal.coin_id].append(signal)

    panels: list[dict[str, Any]] = []
    for coin in coins:
        views = views_by_symbol.get(coin.symbol, [])
        panels.append(
            {
                "coin": coin,
                "short": _symbol_short(coin.symbol),
                "ticker": ticker_by_id.get(coin.id),
                "views": views,
                "signals": signals_by_coin.get(coin.id, [])[:10],
                "ready_count": sum(1 for v in views if v.signal_type),
            }
        )
    return panels


def _scanner_context():
    settings = SettingsService().get_all()
    runtime = SettingsService().runtime_config()
    runtime["scanner_status"] = settings.get("scanner_status", "unknown")
    runtime["last_scan_time"] = settings.get("last_scan_time", "—")
    display_tf = _display_timeframe()
    dashboard = ScannerDashboardService()
    tickers, live_views = dashboard.build(market_timeframe=display_tf)
    coins = [c for c in CoinService().list_coins() if c.enabled]
    recent_signals = SignalService().recent(30)
    return {
        "runtime": runtime,
        "coins": coins,
        "coin_panels": _build_coin_panels(coins, tickers, live_views, recent_signals),
        "strategies": StrategyService().list_all(),
        "recent_signals": recent_signals[:15],
        "tickers": tickers,
        "live_views": live_views,
        "side_progress": ScannerDashboardService.side_progress,
        "display_timeframe": display_tf,
        "timeframes": SUPPORTED_TIMEFRAMES,
        "timeframe_label": timeframe_label,
    }


@scanner_bp.route("/")
def index():
    return render_template("scanner/index.html", **_scanner_context())


@scanner_bp.route("/live.json")
def live_json():
    display_tf = _display_timeframe()
    dashboard = ScannerDashboardService()
    tickers, live_views = dashboard.build(market_timeframe=display_tf)
    progress = ScannerDashboardService.side_progress

    def side_payload(side):
        if not side:
            return None
        p = progress(side)
        return {
            **p,
            "rules": [{"label": r.label, "met": r.met, "detail": r.detail} for r in side.rules],
        }

    return jsonify(
        {
            "tickers": [
                {
                    "symbol": t.symbol,
                    "price": t.price,
                    "change_pct": t.change_pct,
                    "volume": t.volume,
                    "error": t.error,
                }
                for t in tickers
            ],
            "views": [
                {
                    "strategy_id": v.strategy_id,
                    "strategy_name": v.strategy_name,
                    "coin_symbol": v.coin_symbol,
                    "timeframe": v.timeframe,
                    "enabled": v.enabled,
                    "price": v.price,
                    "signal_type": v.signal_type,
                    "long": side_payload(v.long),
                    "short": side_payload(v.short),
                    "next_close_at": v.next_close_at.isoformat() if v.next_close_at else None,
                    "error": v.error,
                }
                for v in live_views
            ],
        }
    )


@scanner_bp.route("/run", methods=["POST"])
def run_now():
    stats = ScannerService().run_scan()
    flash(
        f"Scan complete: {stats['signals']} new signal(s), {stats['errors']} error(s).",
        "success" if stats["errors"] == 0 else "warning",
    )
    return redirect(url_for("scanner.index", tf=request.args.get("tf")))
