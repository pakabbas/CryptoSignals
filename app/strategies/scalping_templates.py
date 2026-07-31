"""Scalping strategy templates from ScalpingResearch.txt (5m)."""

from __future__ import annotations

from typing import Any

_MACD = {"fast": 12, "slow": 26, "signal": 9}

# Preferred pairs for scalping templates (liquid + volatile).
SCALPING_COIN_SYMBOLS: tuple[str, ...] = ("BTC/USDT", "SOL/USDT")


def _ema_cross(fast: int, slow: int, direction: str) -> dict[str, Any]:
    return {
        "type": "indicator_cross",
        "left": {"name": "EMA", "length": fast},
        "right": {"name": "EMA", "length": slow},
        "direction": direction,
    }


def _macd_cross(direction: str) -> dict[str, Any]:
    return {"type": "macd_cross", "direction": direction, **_MACD}


SCALPING_TEMPLATES: list[dict[str, Any]] = [
    {
        "name": "5m · Scalp EMA+RSI Momentum",
        "description": "ScalpingResearch A — EMA5/13 cross + RSI(5) filter; ATR 1× stop, 2R target.",
        "timeframe": "5m",
        "enabled": True,
        "coin_symbols": list(SCALPING_COIN_SYMBOLS),
        "definition_json": {
            "version": 1,
            "template": "scalp_5m_ema_rsi",
            "risk": {"atr_length": 14, "stop_atr_mult": 1.0, "target_rr": 2.0},
            "long": {
                "logic": "AND",
                "rules": [
                    _ema_cross(5, 13, "up"),
                    {
                        "type": "indicator_compare",
                        "left": {"name": "RSI", "length": 5},
                        "operator": "lt",
                        "right": {"value": 70},
                    },
                ],
            },
            "short": {
                "logic": "AND",
                "rules": [
                    _ema_cross(5, 13, "down"),
                    {
                        "type": "indicator_compare",
                        "left": {"name": "RSI", "length": 5},
                        "operator": "gt",
                        "right": {"value": 30},
                    },
                ],
            },
        },
    },
    {
        "name": "5m · Scalp VWAP+MACD",
        "description": "ScalpingResearch B — trade with VWAP bias + MACD cross + RSI(14); ATR 1× stop, 1.5R target.",
        "timeframe": "5m",
        "enabled": True,
        "coin_symbols": list(SCALPING_COIN_SYMBOLS),
        "definition_json": {
            "version": 1,
            "template": "scalp_5m_vwap_macd",
            "risk": {"atr_length": 14, "stop_atr_mult": 1.0, "target_rr": 1.5},
            "long": {
                "logic": "AND",
                "rules": [
                    {
                        "type": "indicator_compare",
                        "left": {"name": "close"},
                        "operator": "gt",
                        "right": {"name": "VWAP"},
                    },
                    _macd_cross("up"),
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
                        "right": {"name": "VWAP"},
                    },
                    _macd_cross("down"),
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
        "name": "5m · Scalp Bollinger+RSI",
        "description": "ScalpingResearch C — fade BB outer touch with RSI extreme; ATR 0.8× stop, 1.5R target.",
        "timeframe": "5m",
        "enabled": True,
        "coin_symbols": list(SCALPING_COIN_SYMBOLS),
        "definition_json": {
            "version": 1,
            "template": "scalp_5m_bb_rsi",
            "risk": {"atr_length": 14, "stop_atr_mult": 0.8, "target_rr": 1.5},
            "long": {
                "logic": "AND",
                "rules": [
                    {"type": "price_at_bb", "band": "lower"},
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
                    {"type": "price_at_bb", "band": "upper"},
                    {
                        "type": "indicator_compare",
                        "left": {"name": "RSI", "length": 14},
                        "operator": "gt",
                        "right": {"value": 70},
                    },
                ],
            },
        },
    },
]

SCALPING_TEMPLATE_NAMES = tuple(t["name"] for t in SCALPING_TEMPLATES)
