#!/usr/bin/env python3
"""Probe CCXT exchanges for BTC/USDT OHLCV from this server's IP (geo-sensitive)."""

from __future__ import annotations

import sys
from typing import Any

import ccxt

# Exchanges to try (CCXT id -> human label). Order: prefer liquid spot markets.
CANDIDATES: list[tuple[str, str]] = [
    ("kraken", "Kraken"),
    ("coinbase", "Coinbase"),
    ("bitstamp", "Bitstamp"),
    ("gemini", "Gemini"),
    ("kucoin", "KuCoin"),
    ("okx", "OKX"),
    ("gate", "Gate.io"),
    ("mexc", "MEXC"),
    ("htx", "HTX"),
    ("cryptocom", "Crypto.com"),
    ("bybit", "Bybit"),
    ("binance", "Binance"),
    ("binanceus", "Binance US"),
]

SYMBOL = "BTC/USDT"
TIMEFRAME = "1h"
LIMIT = 5


def try_exchange(exchange_id: str) -> tuple[bool, str]:
    if not hasattr(ccxt, exchange_id):
        return False, "not in ccxt"
    exchange_class = getattr(ccxt, exchange_id)
    exchange: Any = exchange_class({"enableRateLimit": True, "timeout": 20000})
    try:
        raw = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=LIMIT)
        if not raw or len(raw) < 1:
            return False, "empty ohlcv"
        close = raw[-1][4]
        return True, f"ok close={close} bars={len(raw)}"
    except Exception as exc:
        msg = str(exc).replace("\n", " ")
        if len(msg) > 220:
            msg = msg[:220] + "..."
        return False, msg
    finally:
        try:
            exchange.close()
        except Exception:
            pass


def main() -> int:
    print(f"Probing OHLCV {SYMBOL} {TIMEFRAME} from {sys.platform}\n")
    working: list[str] = []
    for exchange_id, label in CANDIDATES:
        ok, detail = try_exchange(exchange_id)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {label} ({exchange_id}): {detail}")
        if ok:
            working.append(exchange_id)
    print()
    if working:
        print("WORKING:", ", ".join(working))
        print("RECOMMENDED:", working[0])
        return 0
    print("No exchange returned OHLCV from this network.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
