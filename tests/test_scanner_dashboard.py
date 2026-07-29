import pandas as pd

from datetime import datetime, timezone

from app.scanner.candle_utils import next_candle_close_utc
from app.strategies.evaluator import StrategyEvaluator


def test_evaluate_detailed_counts_rules():
    idx = pd.date_range("2026-01-01", periods=250, freq="h", tz="UTC")
    close = pd.Series(range(250), dtype=float) + 100.0
    df = pd.DataFrame(
        {
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 1000.0,
        },
        index=idx,
    )
    definition = {
        "version": 1,
        "long": {
            "logic": "AND",
            "rules": [
                {
                    "type": "indicator_compare",
                    "left": {"name": "RSI", "length": 14},
                    "operator": "gt",
                    "right": {"value": 10},
                },
                {
                    "type": "indicator_compare",
                    "left": {"name": "EMA", "length": 20},
                    "operator": "gt",
                    "right": {"value": 0},
                },
            ],
        },
    }
    ev = StrategyEvaluator()
    detail = ev.evaluate_detailed_at_index(
        ev._enrich_dataframe(df, definition), definition, 200, pre_enriched=True
    )
    assert detail.long is not None
    assert detail.long.total == 2
    assert len(detail.long.rules) == 2


def test_next_candle_close_while_forming():
    now = datetime(2026, 1, 1, 12, 30, tzinfo=timezone.utc)
    open_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    nxt = next_candle_close_utc(open_time, "1H", now=now)
    assert nxt == datetime(2026, 1, 1, 13, 0, tzinfo=timezone.utc)


def test_dashboard_sort_with_failed_views():
    from app.services.scanner_dashboard_service import ScannerDashboardService, StrategyLiveView

    views = [
        StrategyLiveView(
            strategy_id=1,
            strategy_name="A",
            coin_symbol="BTC/USDT",
            timeframe="1H",
            enabled=True,
            price=None,
            signal_type=None,
            long=None,
            short=None,
            next_close_at=None,
            evaluated_at=None,
            indicator_values={},
            error="fetch failed",
        )
    ]
    views.sort(
        key=lambda v: (
            0 if v.signal_type else 1,
            -(
                (v.long.met_count if v.long else 0)
                + (v.short.met_count if v.short else 0)
            ),
            v.strategy_name,
        )
    )
    assert views[0].strategy_name == "A"

