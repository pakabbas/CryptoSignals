import json

import pytest

from app.strategies.defaults import DEFAULT_BUY_STRATEGY
from app.strategies.validator import StrategyValidationError, validate_definition


def test_validate_default_buy_strategy():
    validate_definition(DEFAULT_BUY_STRATEGY["definition_json"])


def test_validate_rejects_empty_rules():
    with pytest.raises(StrategyValidationError):
        validate_definition({"version": 1, "long": {"logic": "AND", "rules": []}})


def test_strategies_list_page(client):
    response = client.get("/strategies/")
    assert response.status_code == 200
    assert b"Strategies" in response.data


def test_strategies_create_page(client):
    response = client.get("/strategies/new")
    assert response.status_code == 200
    assert b"BUY (long) rules" in response.data
