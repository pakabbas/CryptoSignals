from app.backtester.metrics import SimTrade, build_metrics


def test_build_metrics_basic():
    trades = [
        SimTrade("long", "t1", "t2", 100, 110, 10.0, 3),
        SimTrade("long", "t3", "t4", 110, 105, -4.5455, 2),
    ]
    equity = [{"time": "a", "equity": 10000}, {"time": "b", "equity": 10500}]
    dd = [{"time": "a", "drawdown_pct": 0}, {"time": "b", "drawdown_pct": 2.5}]
    metrics = build_metrics(trades, equity, dd, buy_signals=2, sell_signals=1)
    assert metrics["total_trades"] == 2
    assert metrics["winning_trades"] == 1
    assert metrics["buy_signals"] == 2


def test_backtest_pages_load(client):
    response = client.get("/backtest/")
    assert response.status_code == 200
    assert b"Backtesting" in response.data

    response = client.get("/backtest/compare")
    assert response.status_code == 200
