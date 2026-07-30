"""Import an OHLCV JSON dump into the app database (run on the server).

Example:
  python deploy/import_ohlcv_dump.py deploy/data/btc_ohlcv_30d.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app
from app.models import Coin
from app.services.candle_service import CandleService
from app.services.exchange_service import OhlcvBar


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dump_path", type=Path)
    args = parser.parse_args()

    payload = json.loads(args.dump_path.read_text(encoding="utf-8"))
    symbol = payload["symbol"]
    app = create_app()
    with app.app_context():
        coin = Coin.query.filter_by(symbol=symbol).first()
        if coin is None:
            raise SystemExit(f"Coin not found: {symbol}")
        candles = CandleService()
        total_new = 0
        for timeframe, rows in payload.get("timeframes", {}).items():
            bars = [
                OhlcvBar(
                    open_time=_parse_time(row["open_time"]),
                    open=Decimal(str(row["open"])),
                    high=Decimal(str(row["high"])),
                    low=Decimal(str(row["low"])),
                    close=Decimal(str(row["close"])),
                    volume=Decimal(str(row["volume"])),
                )
                for row in rows
            ]
            stored = candles.upsert_bars(coin.id, timeframe, bars)
            total_new += stored
            print(f"{symbol} {timeframe}: upserted {len(bars)} bars ({stored} new)")
        print(f"Done. New rows: {total_new}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
