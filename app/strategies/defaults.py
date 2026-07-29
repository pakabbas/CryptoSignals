"""Default BTC/USDT strategies until Step 3 builder UI."""

from __future__ import annotations

DEFAULT_BUY_STRATEGY = {
    "name": "EMA + RSI + MACD",
    "description": "Trend + momentum long (Requirements example)",
    "timeframe": "1H",
    "enabled": True,
    "definition_json": {
        "version": 1,
        "long": {
            "logic": "AND",
            "rules": [
                {
                    "type": "indicator_compare",
                    "left": {"name": "EMA", "length": 50},
                    "operator": "gt",
                    "right": {"name": "EMA", "length": 200},
                },
                {"type": "macd_cross", "direction": "up"},
                {
                    "type": "indicator_compare",
                    "left": {"name": "RSI", "length": 14},
                    "operator": "gt",
                    "right": {"value": 55},
                },
                {
                    "type": "indicator_compare",
                    "left": {"name": "volume"},
                    "operator": "gt",
                    "right": {"name": "SMA", "length": 20, "source": "volume"},
                },
            ],
        },
        "short": {
            "logic": "AND",
            "rules": [
                {
                    "type": "indicator_compare",
                    "left": {"name": "EMA", "length": 50},
                    "operator": "lt",
                    "right": {"name": "EMA", "length": 200},
                },
                {"type": "macd_cross", "direction": "down"},
                {
                    "type": "indicator_compare",
                    "left": {"name": "RSI", "length": 14},
                    "operator": "lt",
                    "right": {"value": 45},
                },
            ],
        },
    },
}

DEFAULT_MEAN_REVERSION_BUY = {
    "name": "BB Lower + RSI Oversold",
    "description": "Mean reversion long (Requirements example)",
    "timeframe": "1H",
    "enabled": False,
    "definition_json": {
        "version": 1,
        "long": {
            "logic": "AND",
            "rules": [
                {
                    "type": "price_at_bb",
                    "band": "lower",
                },
                {
                    "type": "indicator_compare",
                    "left": {"name": "RSI", "length": 14},
                    "operator": "lt",
                    "right": {"value": 30},
                },
            ],
        },
        "short": {
            "logic": "AND",
            "rules": [
                {
                    "type": "price_at_bb",
                    "band": "upper",
                },
                {
                    "type": "indicator_compare",
                    "left": {"name": "RSI", "length": 14},
                    "operator": "gt",
                    "right": {"value": 70},
                },
            ],
        },
    },
}

DEFAULT_STRATEGIES = [DEFAULT_BUY_STRATEGY, DEFAULT_MEAN_REVERSION_BUY]
