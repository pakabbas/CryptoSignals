"""Fixed strategy templates from indicators.md."""

from __future__ import annotations

from typing import Any

_MACD = {"fast": 12, "slow": 26, "signal": 9}


def _vol_vs_sma(length: int = 20) -> dict[str, Any]:
    return {
        "type": "indicator_compare",
        "left": {"name": "volume"},
        "operator": "gte",
        "right": {"name": "SMA", "length": length, "source": "volume"},
    }


def _ema_cross(fast: int, slow: int, direction: str) -> dict[str, Any]:
    return {
        "type": "indicator_cross",
        "left": {"name": "EMA", "length": fast},
        "right": {"name": "EMA", "length": slow},
        "direction": direction,
    }


def _stochrsi_cross(
    *,
    direction: str,
    from_below: float | None = None,
    from_above: float | None = None,
    length: int = 14,
    stoch_length: int | None = None,
    smooth_k: int = 3,
    smooth_d: int = 3,
) -> dict[str, Any]:
    stoch_length = stoch_length if stoch_length is not None else length
    params = {
        "length": length,
        "stoch_length": stoch_length,
        "smooth_k": smooth_k,
        "smooth_d": smooth_d,
    }
    rule: dict[str, Any] = {
        "type": "indicator_cross",
        "left": {"name": "STOCHRSIk", **params},
        "right": {"name": "STOCHRSId", **params},
        "direction": direction,
    }
    if from_below is not None:
        rule["from_below"] = from_below
    if from_above is not None:
        rule["from_above"] = from_above
    return rule


def _macd_cross(direction: str) -> dict[str, Any]:
    return {"type": "macd_cross", "direction": direction, **_MACD}


RESEARCH_TEMPLATES: list[dict[str, Any]] = [
    {
        "name": "15m · Filtered Mean-Reversion",
        "description": "indicators.md — EMA50 bias, ADX<25, StochRSI cross, volume; ATR 1×/2× risk.",
        "timeframe": "15m",
        "enabled": True,
        "definition_json": {
            "version": 1,
            "template": "ind_15m_mean_reversion",
            "risk": {"atr_length": 14, "stop_atr_mult": 1.0, "target_atr_mult": 2.0},
            "long": {
                "logic": "AND",
                "rules": [
                    {
                        "type": "indicator_compare",
                        "left": {"name": "close"},
                        "operator": "gt",
                        "right": {"name": "EMA", "length": 50},
                    },
                    {
                        "type": "indicator_compare",
                        "left": {"name": "ADX", "length": 14},
                        "operator": "lt",
                        "right": {"value": 25},
                    },
                    _stochrsi_cross(
                        direction="up",
                        from_below=20,
                        length=10,
                        stoch_length=10,
                        smooth_k=3,
                        smooth_d=3,
                    ),
                    _vol_vs_sma(20),
                ],
            },
            "short": {
                "logic": "AND",
                "rules": [
                    {
                        "type": "indicator_compare",
                        "left": {"name": "close"},
                        "operator": "lt",
                        "right": {"name": "EMA", "length": 50},
                    },
                    {
                        "type": "indicator_compare",
                        "left": {"name": "ADX", "length": 14},
                        "operator": "lt",
                        "right": {"value": 25},
                    },
                    _stochrsi_cross(
                        direction="down",
                        from_above=80,
                        length=10,
                        stoch_length=10,
                        smooth_k=3,
                        smooth_d=3,
                    ),
                    _vol_vs_sma(20),
                ],
            },
        },
    },
    {
        "name": "30m · Trend + Momentum",
        "description": "indicators.md — EMA21/50, MACD cross, RSI band, ADX≥20, volume; ATR 1.2× stop, 2R target.",
        "timeframe": "30m",
        "enabled": True,
        "definition_json": {
            "version": 1,
            "template": "ind_30m_trend_momentum",
            "risk": {"atr_length": 14, "stop_atr_mult": 1.2, "target_rr": 2.0},
            "long": {
                "logic": "AND",
                "rules": [
                    {
                        "type": "indicator_compare",
                        "left": {"name": "EMA", "length": 21},
                        "operator": "gt",
                        "right": {"name": "EMA", "length": 50},
                    },
                    _macd_cross("up"),
                    {
                        "type": "indicator_compare",
                        "left": {"name": "RSI", "length": 14},
                        "operator": "gte",
                        "right": {"value": 45},
                    },
                    {
                        "type": "indicator_compare",
                        "left": {"name": "RSI", "length": 14},
                        "operator": "lte",
                        "right": {"value": 65},
                    },
                    {
                        "type": "indicator_compare",
                        "left": {"name": "ADX", "length": 14},
                        "operator": "gte",
                        "right": {"value": 20},
                    },
                    _vol_vs_sma(20),
                ],
            },
            "short": {
                "logic": "AND",
                "rules": [
                    {
                        "type": "indicator_compare",
                        "left": {"name": "EMA", "length": 21},
                        "operator": "lt",
                        "right": {"name": "EMA", "length": 50},
                    },
                    _macd_cross("down"),
                    {
                        "type": "indicator_compare",
                        "left": {"name": "RSI", "length": 14},
                        "operator": "gte",
                        "right": {"value": 35},
                    },
                    {
                        "type": "indicator_compare",
                        "left": {"name": "RSI", "length": 14},
                        "operator": "lte",
                        "right": {"value": 55},
                    },
                    {
                        "type": "indicator_compare",
                        "left": {"name": "ADX", "length": 14},
                        "operator": "gte",
                        "right": {"value": 20},
                    },
                    _vol_vs_sma(20),
                ],
            },
        },
    },
    {
        "name": "1h · Trend-Aligned Momentum",
        "description": "indicators.md — EMA9/21 cross, EMA50 filter, RSI, ADX>20, VWAP; ATR 1.5× stop, 2R target.",
        "timeframe": "1H",
        "enabled": True,
        "definition_json": {
            "version": 1,
            "template": "ind_1h_trend_momentum",
            "risk": {"atr_length": 14, "stop_atr_mult": 1.5, "target_rr": 2.0},
            "long": {
                "logic": "AND",
                "rules": [
                    _ema_cross(9, 21, "up"),
                    {
                        "type": "indicator_compare",
                        "left": {"name": "close"},
                        "operator": "gt",
                        "right": {"name": "EMA", "length": 50},
                    },
                    {
                        "type": "indicator_compare",
                        "left": {"name": "RSI", "length": 14},
                        "operator": "gt",
                        "right": {"value": 55},
                    },
                    {
                        "type": "indicator_compare",
                        "left": {"name": "ADX", "length": 14},
                        "operator": "gt",
                        "right": {"value": 20},
                    },
                    {
                        "type": "indicator_compare",
                        "left": {"name": "close"},
                        "operator": "gt",
                        "right": {"name": "VWAP"},
                    },
                ],
            },
            "short": {
                "logic": "AND",
                "rules": [
                    _ema_cross(9, 21, "down"),
                    {
                        "type": "indicator_compare",
                        "left": {"name": "close"},
                        "operator": "lt",
                        "right": {"name": "EMA", "length": 50},
                    },
                    {
                        "type": "indicator_compare",
                        "left": {"name": "RSI", "length": 14},
                        "operator": "lt",
                        "right": {"value": 45},
                    },
                    {
                        "type": "indicator_compare",
                        "left": {"name": "ADX", "length": 14},
                        "operator": "gt",
                        "right": {"value": 20},
                    },
                    {
                        "type": "indicator_compare",
                        "left": {"name": "close"},
                        "operator": "lt",
                        "right": {"name": "VWAP"},
                    },
                ],
            },
        },
    },
    {
        "name": "4h · Trend-Following Swing",
        "description": "indicators.md — EMA50/200, ADX≥25, StochRSI pullback, MACD confirm; ATR 2× stop, 2R target.",
        "timeframe": "4H",
        "enabled": True,
        "definition_json": {
            "version": 1,
            "template": "ind_4h_trend_swing",
            "risk": {"atr_length": 14, "stop_atr_mult": 2.0, "target_rr": 2.0},
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
                        "left": {"name": "ADX", "length": 14},
                        "operator": "gte",
                        "right": {"value": 25},
                    },
                    _stochrsi_cross(
                        direction="up",
                        from_below=20,
                        length=14,
                        stoch_length=14,
                        smooth_k=5,
                        smooth_d=5,
                    ),
                    _macd_cross("up"),
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
                        "left": {"name": "ADX", "length": 14},
                        "operator": "gte",
                        "right": {"value": 25},
                    },
                    _stochrsi_cross(
                        direction="down",
                        from_above=80,
                        length=14,
                        stoch_length=14,
                        smooth_k=5,
                        smooth_d=5,
                    ),
                    _macd_cross("down"),
                ],
            },
        },
    },
]

RESEARCH_TEMPLATE_NAMES = tuple(t["name"] for t in RESEARCH_TEMPLATES)

# Disabled forever when templates sync (old Research.txt + defaults).
LEGACY_STRATEGY_NAMES = (
    "EMA + RSI + MACD",
    "BB Lower + RSI Oversold",
    "15m · Bollinger+RSI",
    "30m · EMA+RSI+MACD",
    "1h · Ichimoku+EMA+ADX+RSI",
    "4h · Ichimoku+EMA+MACD+ADX",
)
