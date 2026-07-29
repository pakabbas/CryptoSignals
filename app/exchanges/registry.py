from __future__ import annotations

from typing import Any

import ccxt

# CCXT ids for read-only OHLCV. Kraken/Binance US work from US GCP; Binance/Bybit often blocked.
SUPPORTED_EXCHANGES: dict[str, dict[str, str]] = {
    "kraken": {"label": "Kraken", "ccxt_id": "kraken"},
    "binanceus": {"label": "Binance US", "ccxt_id": "binanceus"},
    "kucoin": {"label": "KuCoin", "ccxt_id": "kucoin"},
    "okx": {"label": "OKX", "ccxt_id": "okx"},
    "gate": {"label": "Gate.io", "ccxt_id": "gate"},
    "mexc": {"label": "MEXC", "ccxt_id": "mexc"},
    "coinbase": {"label": "Coinbase", "ccxt_id": "coinbase"},
    "bitstamp": {"label": "Bitstamp", "ccxt_id": "bitstamp"},
    "gemini": {"label": "Gemini", "ccxt_id": "gemini"},
    "htx": {"label": "HTX", "ccxt_id": "htx"},
    "cryptocom": {"label": "Crypto.com", "ccxt_id": "cryptocom"},
    "bybit": {"label": "Bybit (may block US IPs)", "ccxt_id": "bybit"},
    "binance": {"label": "Binance (may block US IPs)", "ccxt_id": "binance"},
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
