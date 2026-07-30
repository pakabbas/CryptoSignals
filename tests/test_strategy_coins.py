from app.models import Coin, Strategy
from app.services.coin_service import CoinService
from app.services.strategy_service import StrategyService


def _seed(app):
    with app.app_context():
        CoinService().ensure_default_coins()
        StrategyService().ensure_research_templates()


def test_edit_coins_page_loads(client, app):
    _seed(app)
    strategy = Strategy.query.first()
    response = client.get(f"/strategies/{strategy.id}/coins")
    assert response.status_code == 200
    assert b"Assign coins" in response.data


def test_set_coins_persists(client, app):
    _seed(app)
    service = StrategyService()
    strategy = Strategy.query.filter_by(enabled=True).first()
    btc = Coin.query.filter_by(symbol="BTC/USDT").first()
    sol = Coin.query.filter_by(symbol="SOL/USDT").first()
    assert btc and sol and strategy

    response = client.post(
        f"/strategies/{strategy.id}/coins",
        data={"coin_ids": [str(btc.id)]},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Coin assignment updated" in response.data

    service.get(strategy.id)
    assigned = {coin.symbol for coin in strategy.coins}
    assert assigned == {"BTC/USDT"}


def test_ensure_research_templates_preserves_coin_assignment(app):
    _seed(app)
    service = StrategyService()
    strategy = Strategy.query.filter_by(enabled=True).first()
    btc = Coin.query.filter_by(symbol="BTC/USDT").first()
    service.set_coins(strategy.id, [btc.id])

    service.ensure_research_templates()
    strategy = service.get(strategy.id)
    assert [coin.symbol for coin in strategy.coins] == ["BTC/USDT"]


def test_list_scan_pairs_respects_assignment(app):
    _seed(app)
    service = StrategyService()
    strategy = Strategy.query.filter_by(enabled=True).first()
    btc = Coin.query.filter_by(symbol="BTC/USDT").first()
    service.set_coins(strategy.id, [btc.id])

    pairs = service.list_scan_pairs()
    symbols = {(coin.symbol, strat.id) for coin, strat in pairs}
    assert (btc.symbol, strategy.id) in symbols
    assert all(coin.symbol == "BTC/USDT" for coin, strat in pairs if strat.id == strategy.id)


def test_backtest_rejects_unassigned_pair(client, app):
    _seed(app)
    service = StrategyService()
    strategy = Strategy.query.filter_by(enabled=True).first()
    sol = Coin.query.filter_by(symbol="SOL/USDT").first()
    btc = Coin.query.filter_by(symbol="BTC/USDT").first()
    service.set_coins(strategy.id, [btc.id])

    response = client.post(
        "/backtest/run",
        data={"strategy_id": strategy.id, "coin_id": sol.id, "period_days": 7},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"not assigned" in response.data.lower()


def test_strategies_index_shows_edit_coins(client, app):
    _seed(app)
    response = client.get("/strategies/")
    assert response.status_code == 200
    assert b"Edit coins" in response.data
