"""Metadata for the visual strategy builder."""

from __future__ import annotations

from app.config.timeframes import SUPPORTED_TIMEFRAMES

TIMEFRAMES = list(SUPPORTED_TIMEFRAMES)

LOGIC_OPS = ["AND", "OR", "NOT"]

OPERATORS = [
    {"value": "gt", "label": ">"},
    {"value": "gte", "label": ">="},
    {"value": "lt", "label": "<"},
    {"value": "lte", "label": "<="},
    {"value": "eq", "label": "="},
]

INDICATORS = [
    {"key": "EMA", "label": "EMA", "params": [{"name": "length", "type": "int", "default": 20}]},
    {"key": "SMA", "label": "SMA", "params": [{"name": "length", "type": "int", "default": 20}, {"name": "source", "type": "select", "options": ["close", "volume"], "default": "close"}]},
    {"key": "RSI", "label": "RSI", "params": [{"name": "length", "type": "int", "default": 14}]},
    {"key": "volume", "label": "Volume", "params": []},
]

RULE_TYPES = [
    {
        "key": "indicator_compare",
        "label": "Compare indicators / values",
        "description": "Example: EMA(50) > EMA(200) or RSI > 55",
    },
    {
        "key": "macd_cross",
        "label": "MACD cross",
        "description": "MACD line crosses signal line up or down",
    },
    {
        "key": "price_at_bb",
        "label": "Price at Bollinger Band",
        "description": "Close touches upper or lower band",
    },
]

DEFAULT_DEFINITION = {
    "version": 1,
    "long": {"logic": "AND", "rules": []},
    "short": {"logic": "AND", "rules": []},
}
