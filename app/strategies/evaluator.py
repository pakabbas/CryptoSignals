from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from app.indicators.engine import IndicatorRegistry, default_registry
from app.scanner.candle_utils import last_closed_bar_index


@dataclass(frozen=True)
class EvaluationResult:
    signal_type: str | None
    bar_index: int
    price: float
    candle_time: pd.Timestamp
    reasons: list[str]


class StrategyEvaluator:
    """Evaluate strategy JSON on OHLCV + indicators (closed candle only)."""

    def __init__(self, registry: IndicatorRegistry | None = None) -> None:
        self.registry = registry or default_registry

    def evaluate(
        self,
        df: pd.DataFrame,
        definition: dict[str, Any],
        timeframe: str,
    ) -> EvaluationResult:
        if df.empty or len(df) < 3:
            raise ValueError("Insufficient candle data")

        bar_idx = last_closed_bar_index(list(df.index.to_pydatetime()), timeframe)
        enriched = self._enrich_dataframe(df, definition)

        long_block = definition.get("long")
        short_block = definition.get("short")

        if long_block and self._evaluate_block(enriched, long_block, bar_idx):
            ts = enriched.index[bar_idx]
            return EvaluationResult(
                signal_type="BUY",
                bar_index=bar_idx,
                price=float(enriched["close"].iloc[bar_idx]),
                candle_time=ts,
                reasons=["Long rules matched"],
            )

        if short_block and self._evaluate_block(enriched, short_block, bar_idx):
            ts = enriched.index[bar_idx]
            return EvaluationResult(
                signal_type="SELL",
                bar_index=bar_idx,
                price=float(enriched["close"].iloc[bar_idx]),
                candle_time=ts,
                reasons=["Short rules matched"],
            )

        ts = enriched.index[bar_idx]
        return EvaluationResult(
            signal_type=None,
            bar_index=bar_idx,
            price=float(enriched["close"].iloc[bar_idx]),
            candle_time=ts,
            reasons=[],
        )

    def _enrich_dataframe(self, df: pd.DataFrame, definition: dict[str, Any]) -> pd.DataFrame:
        enriched = df.copy()
        for spec in self._collect_indicator_specs(definition):
            name = spec["name"].upper()
            params = {k: v for k, v in spec.items() if k != "name"}
            enriched = self.registry.compute(name, enriched, params)
        return enriched

    def _collect_indicator_specs(self, definition: dict[str, Any]) -> list[dict[str, Any]]:
        specs: list[dict[str, Any]] = []
        for side in ("long", "short"):
            block = definition.get(side)
            if not block:
                continue
            for rule in block.get("rules", []):
                specs.extend(self._specs_from_rule(rule))
        # dedupe
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for spec in specs:
            key = str(sorted(spec.items()))
            if key not in seen:
                seen.add(key)
                unique.append(spec)
        return unique

    def _specs_from_rule(self, rule: dict[str, Any]) -> list[dict[str, Any]]:
        specs: list[dict[str, Any]] = []
        for node in (rule.get("left"), rule.get("right")):
            if isinstance(node, dict) and "name" in node and node["name"] != "volume":
                specs.append(dict(node))
        if rule.get("type") == "macd_cross":
            specs.append({"name": "MACD", "fast": 12, "slow": 26, "signal": 9})
        if rule.get("type") == "price_at_bb":
            specs.append({"name": "BB", "length": 20, "std": 2.0})
        return specs

    def _evaluate_block(self, df: pd.DataFrame, block: dict[str, Any], bar_idx: int) -> bool:
        logic = block.get("logic", "AND").upper()
        rules = block.get("rules", [])
        if not rules:
            return False
        results = [self._evaluate_rule(df, rule, bar_idx) for rule in rules]
        if logic == "OR":
            return any(results)
        return all(results)

    def _evaluate_rule(self, df: pd.DataFrame, rule: dict[str, Any], bar_idx: int) -> bool:
        rtype = rule.get("type")
        if rtype == "indicator_compare":
            left = self._resolve_value(df, rule.get("left", {}), bar_idx)
            right = self._resolve_value(df, rule.get("right", {}), bar_idx)
            if left is None or right is None:
                return False
            op = rule.get("operator", "gt")
            return self._compare(left, right, op)
        if rtype == "macd_cross":
            direction = rule.get("direction", "up")
            macd_col = next(
                (
                    c
                    for c in df.columns
                    if c.startswith("MACD_")
                    and not c.startswith("MACDh")
                    and not c.startswith("MACDs")
                ),
                None,
            )
            signal_col = next((c for c in df.columns if c.startswith("MACDs_")), None)
            if macd_col is None or signal_col is None:
                return False
            if bar_idx < 1:
                return False
            prev_diff = df[macd_col].iloc[bar_idx - 1] - df[signal_col].iloc[bar_idx - 1]
            curr_diff = df[macd_col].iloc[bar_idx] - df[signal_col].iloc[bar_idx]
            if pd.isna(prev_diff) or pd.isna(curr_diff):
                return False
            if direction == "up":
                return prev_diff <= 0 < curr_diff
            return prev_diff >= 0 > curr_diff
        if rtype == "price_at_bb":
            band = rule.get("band", "lower")
            lower = next((c for c in df.columns if c.startswith("BBL_")), None)
            upper = next((c for c in df.columns if c.startswith("BBU_")), None)
            if not lower or not upper:
                return False
            close = df["close"].iloc[bar_idx]
            if band == "lower":
                return close <= df[lower].iloc[bar_idx]
            return close >= df[upper].iloc[bar_idx]
        return False

    def _resolve_value(self, df: pd.DataFrame, node: dict[str, Any], bar_idx: int) -> float | None:
        if not node:
            return None
        if "value" in node:
            return float(node["value"])
        name = node.get("name", "").upper()
        if name == "VOLUME":
            return float(df["volume"].iloc[bar_idx])
        if name == "EMA":
            col = f"EMA_{int(node.get('length', 20))}"
        elif name == "SMA":
            source = node.get("source", "close")
            col = f"SMA_{source}_{int(node.get('length', 20))}"
        elif name == "RSI":
            col = f"RSI_{int(node.get('length', 14))}"
        else:
            col = name
        if col not in df.columns:
            return None
        val = df[col].iloc[bar_idx]
        if pd.isna(val):
            return None
        return float(val)

    @staticmethod
    def _compare(left: float, right: float, operator: str) -> bool:
        if operator in ("gt", ">"):
            return left > right
        if operator in ("gte", ">="):
            return left >= right
        if operator in ("lt", "<"):
            return left < right
        if operator in ("lte", "<="):
            return left <= right
        if operator in ("eq", "=="):
            return left == right
        return False
