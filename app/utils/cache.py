from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class _CacheEntry(Generic[T]):
    value: T
    expires_at: float


class TTLCache(Generic[T]):
    """Thread-safe in-memory TTL cache for market data and computed snapshots."""

    def __init__(self, default_ttl_seconds: float = 60.0, max_entries: int = 512) -> None:
        self._default_ttl = default_ttl_seconds
        self._max_entries = max_entries
        self._data: dict[str, _CacheEntry[T]] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> T | None:
        now = time.monotonic()
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            if entry.expires_at <= now:
                del self._data[key]
                return None
            return entry.value

    def set(self, key: str, value: T, ttl_seconds: float | None = None) -> None:
        ttl = self._default_ttl if ttl_seconds is None else ttl_seconds
        expires_at = time.monotonic() + ttl
        with self._lock:
            if len(self._data) >= self._max_entries:
                self._evict_expired(now)
            if len(self._data) >= self._max_entries:
                oldest_key = min(self._data, key=lambda k: self._data[k].expires_at)
                del self._data[oldest_key]
            self._data[key] = _CacheEntry(value=value, expires_at=expires_at)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()

    def _evict_expired(self, now: float) -> None:
        expired = [k for k, v in self._data.items() if v.expires_at <= now]
        for key in expired:
            del self._data[key]


ohlcv_cache: TTLCache[Any] = TTLCache(default_ttl_seconds=90.0, max_entries=256)
scanner_dashboard_cache: TTLCache[Any] = TTLCache(default_ttl_seconds=55.0, max_entries=16)
