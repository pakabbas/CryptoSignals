"""Download OHLCV on a machine that can reach the exchange; write a JSON dump.

Example:
  python deploy/export_ohlcv_dump.py --symbol BTC/USDT --days 30 --exchange gate
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config.timeframes import SUPPORTED_TIMEFRAMES
from app.services.historical_download_service import HistoricalDownloadService


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--exchange", default="gate")
    parser.add_argument(
        "--out",
        default=str(ROOT / "deploy" / "data" / "btc_ohlcv_30d.json"),
    )
    parser.add_argument(
        "--timeframes",
        nargs="+",
        default=list(SUPPORTED_TIMEFRAMES),
    )
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    svc = HistoricalDownloadService()
    payload: dict = {
        "symbol": args.symbol,
        "days": args.days,
        "exchange": args.exchange,
        "timeframes": {},
    }
    for tf in args.timeframes:
        bars = svc.fetch_history(
            args.symbol,
            tf,
            args.days,
            exchange_id=args.exchange,
            include_warmup=True,
        )
        payload["timeframes"][tf] = [
            {
                "open_time": b.open_time.isoformat(),
                "open": str(b.open),
                "high": str(b.high),
                "low": str(b.low),
                "close": str(b.close),
                "volume": str(b.volume),
            }
            for b in bars
        ]
        span = 0.0
        if bars:
            span = (bars[-1].open_time - bars[0].open_time).total_seconds() / 86400
        print(f"{args.symbol} {tf}: {len(bars)} bars (~{span:.1f}d) via {args.exchange}")

    out_path.write_text(json.dumps(payload), encoding="utf-8")
    print(f"Wrote {out_path} ({out_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
