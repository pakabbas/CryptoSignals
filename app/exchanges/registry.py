from __future__ import annotations

from typing import Any

import ccxt

# CCXT ids for future multi-exchange support (read-only OHLCV today).
SUPPORTED_EXCHANGES: dict[str, dict[str, str]] = {
    "binance": {"label": "Binance", "ccxt_id": "binance"},
    "bybit": {"label": "Bybit", "ccxt_id": "bybit"},
    "kraken": {"label": "Kraken", "ccxt_id": "kraken"},
    "okx": {"label": "OKX", "ccxt_id": "okx"},
    "kucoin": {"label": "KuCoin", "ccxt_id": "kucoin"},
}


def normalize_exchange_id(name: str) -> str:
    key = (name or "binance").strip().lower()
    if key in SUPPORTED_EXCHANGES:
        return SUPPORTED_EXCHANGES[key]["ccxt_id"]
    return key


def list_supported_exchanges() -> list[dict[str, str]]:
    return [
        {"id": key, "label": meta["label"], "ccxt_id": meta["ccxt_id"]}
        for key, meta in SUPPORTED_EXCHANGES.items()
    ]


def create_ccxt_exchange(exchange_id: str) -> Any:
    ccxt_id = normalize_exchange_id(exchange_id)
    if not hasattr(ccxt, ccxt_id):
        raise ValueError(f"Unsupported exchange: {exchange_id}")
    exchange_class = getattr(ccxt, ccxt_id)
    return exchange_class({"enableRateLimit": True})
