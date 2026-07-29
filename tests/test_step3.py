import pytest

from app.strategies.research_templates import RESEARCH_TEMPLATES
from app.strategies.validator import StrategyValidationError, validate_definition


@pytest.mark.parametrize("template", RESEARCH_TEMPLATES, ids=lambda t: t["name"])
def test_validate_research_templates(template):
    validate_definition(template["definition_json"])


def test_validate_rejects_empty_rules():
    with pytest.raises(StrategyValidationError):
        validate_definition({"version": 1, "long": {"logic": "AND", "rules": []}})


def test_strategies_list_page(client):
    response = client.get("/strategies/")
    assert response.status_code == 200
    assert b"Strategy templates" in response.data
    assert b"15m" in response.data or b"Mean-Reversion" in response.data or b"Filtered" in response.data


def test_strategies_create_blocked(client):
    response = client.get("/strategies/new", follow_redirects=True)
    assert response.status_code == 200
    assert b"fixed research templates" in response.data.lower() or b"Research" in response.data or b"template" in response.data.lower()
