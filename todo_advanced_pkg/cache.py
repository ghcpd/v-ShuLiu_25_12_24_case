"""Very small in-memory cache with simple TTL support for hot paths.
Used to cache tag lists and recommendation results to improve query latency.
"""
from __future__ import annotations
import time
import threading
from typing import Any, Optional

_lock = threading.Lock()
_cache: dict = {}


def get(key: str) -> Optional[Any]:
    with _lock:
        v = _cache.get(key)
        if not v:
            return None
        val, expires = v
        if expires and expires < time.time():
            del _cache[key]
            return None
        return val


def set(key: str, value: Any, ttl: Optional[float] = None) -> None:
    expires = time.time() + ttl if ttl else None
    with _lock:
        _cache[key] = (value, expires)


def invalidate(key: str) -> None:
    with _lock:
        _cache.pop(key, None)
