"""Tests for caching layer."""

import unittest
import time

from todo_advanced.caching import Cache, get_cache


class TestCache(unittest.TestCase):
    """Test caching functionality."""

    def setUp(self):
        """Set up cache for testing."""
        self.cache = Cache(ttl_seconds=1)

    def test_set_and_get(self):
        """Test setting and getting value."""
        self.cache.set("key1", "value1")
        value = self.cache.get("key1")

        self.assertEqual(value, "value1")

    def test_get_nonexistent_key(self):
        """Test getting non-existent key."""
        value = self.cache.get("nonexistent")
        self.assertIsNone(value)

    def test_cache_expiration(self):
        """Test cache expiration with TTL."""
        self.cache = Cache(ttl_seconds=1)
        self.cache.set("key", "value")

        # Immediately get should work
        value = self.cache.get("key")
        self.assertEqual(value, "value")

        # After TTL expires, should return None
        time.sleep(1.1)
        value = self.cache.get("key")
        self.assertIsNone(value)

    def test_delete(self):
        """Test deleting cache entry."""
        self.cache.set("key", "value")
        self.cache.delete("key")

        value = self.cache.get("key")
        self.assertIsNone(value)

    def test_clear(self):
        """Test clearing all cache."""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.clear()

        self.assertIsNone(self.cache.get("key1"))
        self.assertIsNone(self.cache.get("key2"))

    def test_invalidate_prefix(self):
        """Test invalidating keys by prefix."""
        self.cache.set("work:tag1", "value1")
        self.cache.set("work:tag2", "value2")
        self.cache.set("personal:tag1", "value3")

        self.cache.invalidate_prefix("work:")

        self.assertIsNone(self.cache.get("work:tag1"))
        self.assertIsNone(self.cache.get("work:tag2"))
        self.assertEqual(self.cache.get("personal:tag1"), "value3")

    def test_global_cache(self):
        """Test global cache instance."""
        cache1 = get_cache()
        cache1.set("test_key", "test_value")

        cache2 = get_cache()
        value = cache2.get("test_key")

        self.assertEqual(value, "test_value")


if __name__ == "__main__":
    unittest.main()
