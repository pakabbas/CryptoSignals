from app.strategies.scalping_templates import (
    SCALPING_COIN_SYMBOLS,
    SCALPING_TEMPLATES,
    SCALPING_TEMPLATE_NAMES,
)
from app.strategies.validator import validate_definition
from app.services.coin_service import CoinService
from app.services.strategy_service import StrategyService
from app.models import Strategy


def test_all_scalping_templates_validate():
    assert len(SCALPING_TEMPLATES) == 3
    for template in SCALPING_TEMPLATES:
        validate_definition(template["definition_json"])
        assert template["timeframe"] == "5m"
        assert "risk" in template["definition_json"]
        assert "management" in template["definition_json"]
        assert template["coin_symbols"] == list(SCALPING_COIN_SYMBOLS)


def test_scalping_templates_seeded_for_btc_sol(app):
    with app.app_context():
        CoinService().ensure_default_coins()
        StrategyService().ensure_research_templates()
        for name in SCALPING_TEMPLATE_NAMES:
            strategy = Strategy.query.filter_by(name=name).first()
            assert strategy is not None
            assert strategy.enabled is True
            assert strategy.timeframe == "5m"
            symbols = {c.symbol for c in strategy.coins}
            assert symbols == {"BTC/USDT", "SOL/USDT"}
