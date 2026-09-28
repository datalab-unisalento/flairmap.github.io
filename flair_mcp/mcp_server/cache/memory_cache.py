import time
from typing import Any


class MemoryCache:
    """L1: in-process memory cache with manual TTL."""

    def __init__(self):
        self._store: dict[str, tuple[Any, float | None]] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at is not None and time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        expires_at = time.time() + ttl if ttl is not None else None
        self._store[key] = (value, expires_at)