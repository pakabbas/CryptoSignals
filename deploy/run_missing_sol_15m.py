"""One-off: run missing 15m SOL baseline if absent after indicators reset."""

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
    from app.models import BacktestResult, Coin, Strategy
    from app.services.backtest_service import BacktestService

    app = create_app()
    with app.app_context():
        strategy = Strategy.query.filter_by(name="15m · Filtered Mean-Reversion").first()
        coin = Coin.query.filter_by(symbol="SOL/USDT").first()
        if not strategy or not coin:
            print("Missing strategy or coin")
            sys.exit(1)
        existing = (
            BacktestResult.query.filter_by(strategy_id=strategy.id, coin_id=coin.id, period_days=7)
            .order_by(BacktestResult.id.desc())
            .first()
        )
        if existing:
            print(f"Already have backtest #{existing.id}")
            return
        result = BacktestService().run(strategy.id, coin.id, 7, download=True)
        m = result.metrics_json or {}
        print(f"OK #{result.id} trades={m.get('total_trades')} return={m.get('return_pct')}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
