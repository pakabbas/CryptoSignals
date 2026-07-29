from __future__ import annotations

import json

from flask import (
    Blueprint,
    Response,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from app.models import Coin
from app.services.coin_service import CoinService
from app.services.exchange_service import ExchangeService
from app.services.strategy_service import StrategyService
from app.strategies.builder_catalog import (
    DEFAULT_DEFINITION,
    INDICATORS,
    LOGIC_OPS,
    OPERATORS,
    RULE_TYPES,
    TIMEFRAMES,
)
from app.strategies.evaluator import StrategyEvaluator
from app.strategies.validator import StrategyValidationError, validate_definition

strategies_bp = Blueprint("strategies", __name__, url_prefix="/strategies")


def _parse_definition_from_form() -> dict:
    raw = request.form.get("definition_json", "").strip()
    if not raw:
        raise StrategyValidationError("Strategy rules JSON is missing")
    try:
        definition = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise StrategyValidationError(f"Invalid rules JSON: {exc}") from exc
    validate_definition(definition)
    return definition


def _coin_ids_from_form() -> list[int]:
    return [int(value) for value in request.form.getlist("coin_ids") if value.isdigit()]


@strategies_bp.route("/")
def index():
    strategies = StrategyService().list_all()
    return render_template("strategies/index.html", strategies=strategies)


@strategies_bp.route("/new", methods=["GET", "POST"])
def create():
    service = StrategyService()
    coins = CoinService().list_coins()

    if request.method == "POST":
        try:
            definition = _parse_definition_from_form()
            service.create(
                name=request.form.get("name", "").strip(),
                description=request.form.get("description", "").strip() or None,
                timeframe=request.form.get("timeframe", "1H"),
                definition_json=definition,
                enabled=request.form.get("enabled") == "on",
                coin_ids=_coin_ids_from_form(),
            )
            flash("Strategy created.", "success")
            return redirect(url_for("strategies.index"))
        except StrategyValidationError as exc:
            flash(str(exc), "danger")

    return render_template(
        "strategies/form.html",
        strategy=None,
        definition=DEFAULT_DEFINITION,
        coins=coins,
        selected_coin_ids=[],
        form_action=url_for("strategies.create"),
        page_title="Create strategy",
        indicators=INDICATORS,
        rule_types=RULE_TYPES,
        operators=OPERATORS,
        logic_ops=LOGIC_OPS,
        timeframes=TIMEFRAMES,
    )


@strategies_bp.route("/<int:strategy_id>/edit", methods=["GET", "POST"])
def edit(strategy_id: int):
    service = StrategyService()
    strategy = service.get(strategy_id)
    coins = CoinService().list_coins()
    selected_coin_ids = [coin.id for coin in strategy.coins]

    if request.method == "POST":
        try:
            definition = _parse_definition_from_form()
            service.update(
                strategy_id,
                name=request.form.get("name", "").strip(),
                description=request.form.get("description", "").strip() or None,
                timeframe=request.form.get("timeframe", "1H"),
                definition_json=definition,
                enabled=request.form.get("enabled") == "on",
                coin_ids=_coin_ids_from_form(),
            )
            flash("Strategy updated.", "success")
            return redirect(url_for("strategies.index"))
        except StrategyValidationError as exc:
            flash(str(exc), "danger")

    return render_template(
        "strategies/form.html",
        strategy=strategy,
        definition=strategy.definition_json,
        coins=coins,
        selected_coin_ids=selected_coin_ids,
        form_action=url_for("strategies.edit", strategy_id=strategy.id),
        page_title=f"Edit: {strategy.name}",
        indicators=INDICATORS,
        rule_types=RULE_TYPES,
        operators=OPERATORS,
        logic_ops=LOGIC_OPS,
        timeframes=TIMEFRAMES,
    )


@strategies_bp.route("/<int:strategy_id>/delete", methods=["POST"])
def delete(strategy_id: int):
    StrategyService().delete(strategy_id)
    flash("Strategy deleted.", "success")
    return redirect(url_for("strategies.index"))


@strategies_bp.route("/<int:strategy_id>/clone", methods=["POST"])
def clone(strategy_id: int):
    clone_row = StrategyService().clone(strategy_id)
    flash(f"Cloned as '{clone_row.name}'.", "success")
    return redirect(url_for("strategies.edit", strategy_id=clone_row.id))


@strategies_bp.route("/<int:strategy_id>/toggle", methods=["POST"])
def toggle(strategy_id: int):
    service = StrategyService()
    strategy = service.get(strategy_id)
    service.set_enabled(strategy_id, not strategy.enabled)
    flash("Strategy status updated.", "success")
    return redirect(url_for("strategies.index"))


@strategies_bp.route("/<int:strategy_id>/export")
def export(strategy_id: int):
    payload = StrategyService().export_json(strategy_id)
    strategy = StrategyService().get(strategy_id)
    filename = f"{strategy.name.replace(' ', '_').lower()}.json"
    return Response(
        payload,
        mimetype="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@strategies_bp.route("/import", methods=["GET", "POST"])
def import_strategy():
    if request.method == "POST":
        raw = request.form.get("import_json", "").strip()
        if not raw and "import_file" in request.files:
            file = request.files["import_file"]
            raw = file.read().decode("utf-8") if file else ""
        try:
            imported = StrategyService().import_json(
                raw,
                replace_name=request.form.get("import_name", "").strip() or None,
            )
            flash(f"Imported strategy '{imported.name}'.", "success")
            return redirect(url_for("strategies.edit", strategy_id=imported.id))
        except StrategyValidationError as exc:
            flash(str(exc), "danger")

    return render_template("strategies/import.html")


@strategies_bp.route("/preview", methods=["POST"])
def preview():
    try:
        definition = _parse_definition_from_form()
        symbol = request.form.get("preview_symbol", "BTC/USDT")
        timeframe = request.form.get("timeframe", "1H")
        df = ExchangeService().fetch_ohlcv_dataframe(symbol, timeframe, limit=300)
        result = StrategyEvaluator().evaluate(df, definition, timeframe)
        message = (
            f"Preview on {symbol} {timeframe}: "
            f"{result.signal_type or 'NO SIGNAL'} @ {result.price:.2f} "
            f"(candle {result.candle_time})"
        )
        flash(message, "info" if result.signal_type else "secondary")
    except Exception as exc:
        flash(f"Preview failed: {exc}", "danger")

    if request.form.get("strategy_id"):
        return redirect(url_for("strategies.edit", strategy_id=int(request.form["strategy_id"])))
    return redirect(url_for("strategies.create"))
