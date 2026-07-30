from __future__ import annotations

from flask import Blueprint, Response, flash, redirect, render_template, request, url_for

from app.models import Coin
from app.services.backtest_service import BacktestService, chart_payload_from_metrics
from app.services.coin_service import CoinService
from app.services.historical_download_service import BACKTEST_PERIODS_DAYS
from app.services.strategy_service import StrategyService

backtest_bp = Blueprint("backtest", __name__, url_prefix="/backtest")


@backtest_bp.route("/")
def index():
    service = BacktestService()
    return render_template(
        "backtest/index.html",
        results=service.list_recent_summaries(30),
        strategies=StrategyService().list_enabled(),
        coins=[c for c in CoinService().list_coins() if c.enabled],
        periods=BACKTEST_PERIODS_DAYS,
    )


@backtest_bp.route("/run", methods=["POST"])
def run():
    strategy_id = request.form.get("strategy_id", type=int)
    coin_id = request.form.get("coin_id", type=int)
    period_days = request.form.get("period_days", 30, type=int)
    if not strategy_id or not coin_id:
        flash("Strategy and coin are required.", "danger")
        return redirect(url_for("backtest.index"))
    try:
        result = BacktestService().run(strategy_id, coin_id, period_days)
        flash("Backtest completed.", "success")
        return redirect(url_for("backtest.show", result_id=result.id))
    except Exception as exc:
        flash(f"Backtest failed: {exc}", "danger")
        return redirect(url_for("backtest.index"))


@backtest_bp.route("/<int:result_id>")
def show(result_id: int):
    result = BacktestService().get(result_id)
    metrics = result.metrics_json or {}
    return render_template(
        "backtest/show.html",
        result=result,
        metrics=metrics,
        chart_json=chart_payload_from_metrics(metrics),
    )


@backtest_bp.route("/<int:result_id>/delete", methods=["POST"])
def delete(result_id: int):
    BacktestService().delete(result_id)
    flash("Backtest deleted.", "success")
    return redirect(url_for("backtest.index"))


@backtest_bp.route("/<int:result_id>/export")
def export(result_id: int):
    payload = BacktestService().export_json(result_id)
    return Response(
        payload,
        mimetype="application/json",
        headers={"Content-Disposition": f'attachment; filename="backtest_{result_id}.json"'},
    )


@backtest_bp.route("/compare", methods=["GET", "POST"])
def compare():
    if request.method == "POST":
        ids = [int(x) for x in request.form.getlist("result_ids") if x.isdigit()]
        results = BacktestService().compare(ids)
    else:
        ids = [int(x) for x in request.args.get("ids", "").split(",") if x.strip().isdigit()]
        results = BacktestService().compare(ids)

    return render_template(
        "backtest/compare.html",
        results=results,
        all_results=BacktestService().list_recent_summaries(100),
    )
