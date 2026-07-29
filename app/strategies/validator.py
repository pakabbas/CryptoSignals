from __future__ import annotations

from typing import Any


class StrategyValidationError(ValueError):
    pass


VALID_RULE_TYPES = {"indicator_compare", "macd_cross", "price_at_bb", "bb_reversion"}
VALID_OPERATORS = {"gt", "gte", "lt", "lte", "eq", ">", ">=", "<", "<=", "=="}
VALID_LOGIC = {"AND", "OR", "NOT"}


def validate_definition(definition: dict[str, Any]) -> None:
    if not isinstance(definition, dict):
        raise StrategyValidationError("Definition must be a JSON object")

    version = definition.get("version")
    if version != 1:
        raise StrategyValidationError("Unsupported strategy version (expected 1)")

    long_block = definition.get("long")
    short_block = definition.get("short")
    if not long_block and not short_block:
        raise StrategyValidationError("At least one of long (BUY) or short (SELL) blocks is required")

    for side_name, block in (("long", long_block), ("short", short_block)):
        if block is None:
            continue
        _validate_block(side_name, block)


def _validate_block(side_name: str, block: dict[str, Any]) -> None:
    if not isinstance(block, dict):
        raise StrategyValidationError(f"{side_name} block must be an object")

    logic = str(block.get("logic", "AND")).upper()
    if logic not in VALID_LOGIC:
        raise StrategyValidationError(f"Invalid logic '{logic}' in {side_name} block")

    rules = block.get("rules", [])
    if not isinstance(rules, list):
        raise StrategyValidationError(f"{side_name} rules must be a list")
    if not rules:
        raise StrategyValidationError(f"{side_name} block must contain at least one rule")

    for index, rule in enumerate(rules):
        _validate_rule(side_name, index, rule)


def _validate_rule(side_name: str, index: int, rule: dict[str, Any]) -> None:
    if not isinstance(rule, dict):
        raise StrategyValidationError(f"Rule {index + 1} in {side_name} must be an object")

    rtype = rule.get("type")
    if rtype not in VALID_RULE_TYPES:
        raise StrategyValidationError(f"Unknown rule type '{rtype}' in {side_name} rule {index + 1}")

    if rtype == "indicator_compare":
        op = rule.get("operator", "gt")
        if op not in VALID_OPERATORS:
            raise StrategyValidationError(f"Invalid operator in {side_name} rule {index + 1}")
        if not rule.get("left") or not rule.get("right"):
            raise StrategyValidationError(f"Compare rule {index + 1} needs left and right operands")

    if rtype == "macd_cross":
        direction = rule.get("direction", "up")
        if direction not in {"up", "down"}:
            raise StrategyValidationError(f"MACD direction must be up or down (rule {index + 1})")

    if rtype == "price_at_bb":
        band = rule.get("band", "lower")
        if band not in {"lower", "upper"}:
            raise StrategyValidationError(f"Bollinger band must be lower or upper (rule {index + 1})")

    if rtype == "bb_reversion":
        side = rule.get("side", "long")
        if side not in {"long", "short"}:
            raise StrategyValidationError(f"bb_reversion side must be long or short (rule {index + 1})")
