"""
Caching layer for performance optimization.
"""

from typing import Any, Callable, Dict, Optional
from functools import wraps
from datetime import datetime, timedelta


class Cache:
    """Simple cache with TTL support."""

    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, tuple] = {}  # key -> (value, timestamp)

    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache if not expired."""
        if key in self._cache:
            value, timestamp = self._cache[key]
            age = (datetime.utcnow() - timestamp).total_seconds()
            if age < self.ttl_seconds:
                return value
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Set a cache entry."""
        self._cache[key] = (value, datetime.utcnow())

    def delete(self, key: str) -> None:
        """Delete a cache entry."""
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()

    def invalidate_prefix(self, prefix: str) -> None:
        """Invalidate all keys starting with prefix."""
        keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
        for key in keys_to_delete:
            del self._cache[key]


# Global cache instance
_cache = Cache()


def get_cache() -> Cache:
    """Get global cache instance."""
    return _cache


def cached(ttl_seconds: int = 300, key_prefix: str = ""):
    """Decorator for caching function results."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key
            cache_key = f"{key_prefix}:{func.__name__}:{args}:{sorted(kwargs.items())}"

            # Try cache
            result = _cache.get(cache_key)
            if result is not None:
                return result

            # Compute and cache
            result = func(*args, **kwargs)
            _cache.set(cache_key, result)
            return result

        return wrapper

    return decorator
