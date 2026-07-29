from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.services.coin_service import CoinService

coins_bp = Blueprint("coins", __name__, url_prefix="/coins")


@coins_bp.route("/", methods=["GET", "POST"])
def index():
    coin_service = CoinService()
    coin_service.ensure_primary_coin()

    if request.method == "POST":
        action = request.form.get("action")
        coin_id = request.form.get("coin_id", type=int)
        if action == "toggle" and coin_id:
            enabled = request.form.get("enabled") == "on"
            coin_service.set_enabled(coin_id, enabled)
            flash("BTC/USDT monitoring updated.", "success")
        elif action == "group" and coin_id:
            coin_service.update_group(coin_id, request.form.get("group_name"))
            flash("Coin group updated.", "success")
        return redirect(url_for("coins.index"))

    search = request.args.get("q")
    coins = coin_service.list_coins(search=search)
    primary_symbol = coin_service.get_primary().symbol if coin_service.get_primary() else "BTC/USDT"

    return render_template(
        "coins/index.html",
        coins=coins,
        primary_symbol=primary_symbol,
        search=search or "",
    )
