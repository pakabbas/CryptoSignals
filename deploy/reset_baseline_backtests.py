"""Delete all backtests, then run research templates × enabled coins (16 combos)."""

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
    from app.models import Strategy
    from app.services.backtest_service import BacktestService
    from app.strategies.research_templates import RESEARCH_TEMPLATE_NAMES

    period_days = int(os.getenv("BASELINE_BACKTEST_DAYS", "7"))
    app = create_app()
    with app.app_context():
        service = BacktestService()
        deleted = service.delete_all()
        print(f"Deleted {deleted} old backtest result(s)")

        strategies = (
            Strategy.query.filter(Strategy.name.in_(RESEARCH_TEMPLATE_NAMES))
            .order_by(Strategy.timeframe.asc(), Strategy.name.asc())
            .all()
        )
        ok = 0
        failed = 0
        for strategy in strategies:
            assigned = [coin for coin in strategy.coins if coin.enabled]
            if not assigned:
                print(f"SKIP {strategy.name}: no coins assigned", file=sys.stderr)
                continue
            for coin in assigned:
                label = f"{strategy.name} · {coin.symbol} · {period_days}d"
                try:
                    result = service.run(strategy.id, coin.id, period_days, download=True)
                    m = result.metrics_json or {}
                    print(
                        f"OK #{result.id} {label} "
                        f"trades={m.get('total_trades')} "
                        f"return={m.get('return_pct')} "
                        f"win={m.get('win_rate')}"
                    )
                    ok += 1
                except Exception as exc:
                    failed += 1
                    print(f"FAIL {label}: {exc}", file=sys.stderr)

        print(f"Done: {ok} ok, {failed} failed")
        if failed:
            sys.exit(1)


if __name__ == "__main__":
    main()
