"""Fixed strategy templates from Research.txt (no custom builder)."""

from __future__ import annotations

from typing import Any

_MACD = {"fast": 12, "slow": 26, "signal": 9}
_MACDH = {"name": "MACDh", **_MACD}
_MACD_LINE = {"name": "MACD", **_MACD}


def _macd_hist_gt_zero() -> dict[str, Any]:
    return {
        "type": "indicator_compare",
        "left": _MACDH,
        "operator": "gt",
        "right": {"value": 0},
    }


def _macd_hist_lt_zero() -> dict[str, Any]:
    return {
        "type": "indicator_compare",
        "left": _MACDH,
        "operator": "lt",
        "right": {"value": 0},
    }


def _macd_line_gt_zero() -> dict[str, Any]:
    return {
        "type": "indicator_compare",
        "left": _MACD_LINE,
        "operator": "gt",
        "right": {"value": 0},
    }


def _macd_line_lt_zero() -> dict[str, Any]:
    return {
        "type": "indicator_compare",
        "left": _MACD_LINE,
        "operator": "lt",
        "right": {"value": 0},
    }


RESEARCH_TEMPLATES: list[dict[str, Any]] = [
    {
        "name": "15m · Bollinger+RSI",
        "description": "Research template — mean reversion (BTC, ETH, DOGE, SOL).",
        "timeframe": "15m",
        "enabled": True,
        "definition_json": {
            "version": 1,
            "template": "research_15m_bb_rsi",
            "long": {
                "logic": "AND",
                "rules": [{"type": "bb_reversion", "side": "long"}],
            },
            "short": {
                "logic": "AND",
                "rules": [{"type": "bb_reversion", "side": "short"}],
            },
        },
    },
    {
        "name": "30m · EMA+RSI+MACD",
        "description": "Research template — trend + momentum (EMA50/200, RSI, MACD histogram).",
        "timeframe": "30m",
        "enabled": True,
        "definition_json": {
            "version": 1,
            "template": "research_30m_ema_rsi_macd",
            "long": {
                "logic": "AND",
                "rules": [
                    {
                        "type": "indicator_compare",
                        "left": {"name": "EMA", "length": 50},
                        "operator": "gt",
                        "right": {"name": "EMA", "length": 200},
                    },
                    {
                        "type": "indicator_compare",
                        "left": {"name": "RSI", "length": 14},
                        "operator": "gt",
                        "right": {"value": 55},
                    },
                    _macd_hist_gt_zero(),
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
                    {
                        "type": "indicator_compare",
                        "left": {"name": "RSI", "length": 14},
                        "operator": "lt",
                        "right": {"value": 45},
                    },
                    _macd_hist_lt_zero(),
                ],
            },
        },
    },
    {
        "name": "1h · Ichimoku+EMA+ADX+RSI",
        "description": "Research template — cloud, conversion/base, EMA50/200, ADX>25, RSI.",
        "timeframe": "1H",
        "enabled": True,
        "definition_json": {
            "version": 1,
            "template": "research_1h_ichimoku",
            "long": {
                "logic": "AND",
                "rules": [
                    {
                        "type": "indicator_compare",
                        "left": {"name": "close"},
                        "operator": "gt",
                        "right": {"name": "ICHI_cloud_top"},
                    },
                    {
                        "type": "indicator_compare",
                        "left": {"name": "ICHI_tenkan"},
                        "operator": "gt",
                        "right": {"name": "ICHI_kijun"},
                    },
                    {
                        "type": "indicator_compare",
                        "left": {"name": "EMA", "length": 50},
                        "operator": "gt",
                        "right": {"name": "EMA", "length": 200},
                    },
                    {
                        "type": "indicator_compare",
                        "left": {"name": "ADX", "length": 14},
                        "operator": "gt",
                        "right": {"value": 25},
                    },
                    {
                        "type": "indicator_compare",
                        "left": {"name": "RSI", "length": 14},
                        "operator": "gt",
                        "right": {"value": 50},
                    },
                ],
            },
            "short": {
                "logic": "AND",
                "rules": [
                    {
                        "type": "indicator_compare",
                        "left": {"name": "close"},
                        "operator": "lt",
                        "right": {"name": "ICHI_cloud_bottom"},
                    },
                    {
                        "type": "indicator_compare",
                        "left": {"name": "ICHI_tenkan"},
                        "operator": "lt",
                        "right": {"name": "ICHI_kijun"},
                    },
                    {
                        "type": "indicator_compare",
                        "left": {"name": "EMA", "length": 50},
                        "operator": "lt",
                        "right": {"name": "EMA", "length": 200},
                    },
                    {
                        "type": "indicator_compare",
                        "left": {"name": "ADX", "length": 14},
                        "operator": "gt",
                        "right": {"value": 25},
                    },
                    {
                        "type": "indicator_compare",
                        "left": {"name": "RSI", "length": 14},
                        "operator": "lt",
                        "right": {"value": 50},
                    },
                ],
            },
        },
    },
    {
        "name": "4h · Ichimoku+EMA+MACD+ADX",
        "description": "Research template — strong trend + volume filter (4h).",
        "timeframe": "4H",
        "enabled": True,
        "definition_json": {
            "version": 1,
            "template": "research_4h_ichimoku",
            "long": {
                "logic": "AND",
                "rules": [
                    {
                        "type": "indicator_compare",
                        "left": {"name": "close"},
                        "operator": "gt",
                        "right": {"name": "ICHI_cloud_top"},
                    },
                    {
                        "type": "indicator_compare",
                        "left": {"name": "ICHI_tenkan"},
                        "operator": "gt",
                        "right": {"name": "ICHI_kijun"},
                    },
                    {
                        "type": "indicator_compare",
                        "left": {"name": "EMA", "length": 200},
                        "operator": "gt",
                        "right": {"name": "EMA", "length": 200, "bar_offset": 1},
                    },
                    _macd_line_gt_zero(),
                    {
                        "type": "indicator_compare",
                        "left": {"name": "ADX", "length": 14},
                        "operator": "gt",
                        "right": {"value": 25},
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
                        "left": {"name": "close"},
                        "operator": "lt",
                        "right": {"name": "ICHI_cloud_bottom"},
                    },
                    {
                        "type": "indicator_compare",
                        "left": {"name": "ICHI_tenkan"},
                        "operator": "lt",
                        "right": {"name": "ICHI_kijun"},
                    },
                    {
                        "type": "indicator_compare",
                        "left": {"name": "EMA", "length": 200},
                        "operator": "lt",
                        "right": {"name": "EMA", "length": 200, "bar_offset": 1},
                    },
                    _macd_line_lt_zero(),
                    {
                        "type": "indicator_compare",
                        "left": {"name": "ADX", "length": 14},
                        "operator": "gt",
                        "right": {"value": 25},
                    },
                ],
            },
        },
    },
]

RESEARCH_TEMPLATE_NAMES = tuple(t["name"] for t in RESEARCH_TEMPLATES)

LEGACY_STRATEGY_NAMES = ("EMA + RSI + MACD", "BB Lower + RSI Oversold")
