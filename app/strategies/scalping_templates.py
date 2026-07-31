"""Scalping strategy templates from ScalpingResearch.txt (5m) — mandatory rules only."""

from __future__ import annotations

from typing import Any

_MACD = {"fast": 12, "slow": 26, "signal": 9}

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


def _close_vs_ema(length: int, operator: str) -> dict[str, Any]:
    return {
        "type": "indicator_compare",
        "left": {"name": "close"},
        "operator": operator,
        "right": {"name": "EMA", "length": length},
    }


SCALPING_TEMPLATES: list[dict[str, Any]] = [
    {
        "name": "5m · Scalp EMA+RSI Momentum",
        "description": (
            "ScalpingResearch A (mandatory) — EMA5×13 + RSI(5); "
            "short requires close below EMA5/8/13; ATR 1× / 2R; max hold 6; cooldown 2 after loss."
        ),
        "timeframe": "5m",
        "enabled": True,
        "coin_symbols": list(SCALPING_COIN_SYMBOLS),
        "definition_json": {
            "version": 1,
            "template": "scalp_5m_ema_rsi",
            "risk": {"atr_length": 14, "stop_atr_mult": 1.0, "target_rr": 2.0},
            "management": {
                "entry_fill": "close",
                "max_hold_bars": 6,
                "max_hold_if_losing": True,
                "cooldown_bars": 2,
                "cooldown_after": "loss",
                "exit_rsi_extreme": {"length": 5, "long_gt": 70, "short_lt": 30},
            },
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
                    # Candle closes below all EMAs (mandatory short confirmation)
                    _close_vs_ema(5, "lt"),
                    _close_vs_ema(8, "lt"),
                    _close_vs_ema(13, "lt"),
                ],
            },
        },
    },
    {
        "name": "5m · Scalp VWAP+MACD",
        "description": (
            "ScalpingResearch B (mandatory) — VWAP bias + MACD cross; "
            "next-open fill; ATR 1× / 1.5R; exit on VWAP crossback or MACD flip; max hold 8; cooldown 1."
        ),
        "timeframe": "5m",
        "enabled": True,
        "coin_symbols": list(SCALPING_COIN_SYMBOLS),
        "definition_json": {
            "version": 1,
            "template": "scalp_5m_vwap_macd",
            "risk": {"atr_length": 14, "stop_atr_mult": 1.0, "target_rr": 1.5},
            "management": {
                "entry_fill": "next_open",
                "max_hold_bars": 8,
                "max_hold_if_losing": False,
                "cooldown_bars": 1,
                "cooldown_after": "any",
                "exit_vwap_crossback": True,
                "exit_macd_flip": True,
            },
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
                ],
            },
        },
    },
    {
        "name": "5m · Scalp Bollinger+RSI",
        "description": (
            "ScalpingResearch C (mandatory) — fresh BB outer touch + RSI extreme; "
            "next-open fill; ATR 0.8× stop; TP at mid-BB; max hold 3; cooldown 2."
        ),
        "timeframe": "5m",
        "enabled": True,
        "coin_symbols": list(SCALPING_COIN_SYMBOLS),
        "definition_json": {
            "version": 1,
            "template": "scalp_5m_bb_rsi",
            "risk": {"atr_length": 14, "stop_atr_mult": 0.8, "target_rr": 1.5},
            "management": {
                "entry_fill": "next_open",
                "max_hold_bars": 3,
                "max_hold_if_losing": False,
                "cooldown_bars": 2,
                "cooldown_after": "any",
                "exit_mid_bb": True,
                "fresh_bb_touch": True,
            },
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
