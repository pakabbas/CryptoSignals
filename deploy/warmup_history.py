"""Download/ensure ~7 days of OHLCV for all enabled coins × supported timeframes."""

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
    from app.services.history_warmup_service import HistoryWarmupService, MIN_HISTORY_DAYS

    days = int(os.getenv("HISTORY_WARMUP_DAYS", str(MIN_HISTORY_DAYS)))
    app = create_app()
    with app.app_context():
        summary = HistoryWarmupService().ensure_all(days=days)
        print(
            f"History warmup ({days}d): ok={summary['already_ok']} "
            f"downloaded={summary['downloaded']} errors={summary['errors']}"
        )
        for row in summary["pairs"]:
            status = row.get("status")
            bars = row.get("bars")
            expected = row.get("expected")
            err = row.get("error")
            line = (
                f"  {row.get('coin')} {row.get('timeframe')} "
                f"[{row.get('exchange')}] {status} bars={bars}/{expected}"
            )
            if err:
                line += f" err={err}"
            print(line)
        if summary["errors"]:
            sys.exit(1)


if __name__ == "__main__":
    main()
