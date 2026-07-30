"""Apply indicators.md templates, keep BTC/SOL only, clear backtests + signals."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    os.environ.setdefault("ENABLE_SCHEDULER", "false")

    from app import create_app
    from app.services.backtest_service import BacktestService
    from app.services.coin_service import CoinService
    from app.services.signal_service import SignalService
    from app.services.strategy_service import StrategyService
    from app.strategies.research_templates import RESEARCH_TEMPLATE_NAMES

    app = create_app()
    with app.app_context():
        coins = CoinService().ensure_default_coins()
        StrategyService().ensure_research_templates()
        enabled = [c.symbol for c in coins if c.enabled]
        print(f"Enabled coins: {enabled}")
        print(f"Active templates: {list(RESEARCH_TEMPLATE_NAMES)}")

        deleted_bt = BacktestService().delete_all()
        deleted_sig = SignalService().delete_all()
        print(f"Deleted {deleted_bt} backtests, {deleted_sig} signals")

        run_bt = os.getenv("RUN_BASELINE_BACKTESTS", "true").lower() in {"1", "true", "yes"}
        if not run_bt:
            return

        from app.models import Strategy

        period_days = int(os.getenv("BASELINE_BACKTEST_DAYS", "7"))
        strategies = (
            Strategy.query.filter(Strategy.name.in_(RESEARCH_TEMPLATE_NAMES), Strategy.enabled.is_(True))
            .order_by(Strategy.timeframe.asc())
            .all()
        )
        service = BacktestService()
        ok = fail = 0
        for strategy in strategies:
            assigned = [coin for coin in strategy.coins if coin.enabled]
            if not assigned:
                print(f"SKIP {strategy.name}: no coins assigned")
                continue
            for coin in assigned:
                label = f"{strategy.name} · {coin.symbol}"
                try:
                    result = service.run(strategy.id, coin.id, period_days, download=True)
                    m = result.metrics_json or {}
                    print(
                        f"OK #{result.id} {label} trades={m.get('total_trades')} "
                        f"return={m.get('return_pct')} win={m.get('win_rate')}"
                    )
                    ok += 1
                except Exception as exc:
                    fail += 1
                    print(f"FAIL {label}: {exc}", file=sys.stderr)
        print(f"Done: {ok} ok, {fail} failed")
        if fail:
            sys.exit(1)


if __name__ == "__main__":
    main()
