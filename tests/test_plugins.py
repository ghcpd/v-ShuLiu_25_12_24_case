"""Tests for plugin system."""

import unittest

from todo_advanced.plugins import PluginManager, get_plugin_manager, reset_plugin_manager


class TestPluginManager(unittest.TestCase):
    """Test plugin system."""

    def setUp(self):
        """Set up plugin manager."""
        self.manager = PluginManager()

    def tearDown(self):
        """Clean up."""
        reset_plugin_manager()

    def test_default_hooks_exist(self):
        """Test that default hooks are created."""
        hook_names = [
            "on_task_added",
            "on_task_updated",
            "on_task_completed",
            "on_tag_added",
            "on_query_executed",
        ]

        for hook_name in hook_names:
            hook = self.manager.get_hook(hook_name)
            self.assertIsNotNone(hook)

    def test_subscribe_to_hook(self):
        """Test subscribing to a hook."""
        called = []

        def handler(task_id):
            called.append(task_id)

        self.manager.subscribe("on_task_added", handler)
        self.manager.fire_hook("on_task_added", 1)

        self.assertEqual(called, [1])

    def test_unsubscribe_from_hook(self):
        """Test unsubscribing from hook."""
        def handler(task_id):
            pass

        self.manager.subscribe("on_task_added", handler)
        self.manager.unsubscribe("on_task_added", handler)

        hook = self.manager.get_hook("on_task_added")
        self.assertEqual(len(hook._handlers), 0)

    def test_fire_hook_with_multiple_handlers(self):
        """Test firing hook with multiple handlers."""
        results = []

        def handler1(value):
            results.append(f"handler1:{value}")

        def handler2(value):
            results.append(f"handler2:{value}")

        self.manager.subscribe("on_task_completed", handler1)
        self.manager.subscribe("on_task_completed", handler2)

        self.manager.fire_hook("on_task_completed", "test")

        self.assertEqual(len(results), 2)
        self.assertIn("handler1:test", results)
        self.assertIn("handler2:test", results)

    def test_fire_nonexistent_hook(self):
        """Test firing non-existent hook returns empty list."""
        results = self.manager.fire_hook("nonexistent_hook")
        self.assertEqual(results, [])

    def test_global_plugin_manager(self):
        """Test global plugin manager singleton."""
        mgr1 = get_plugin_manager()
        mgr2 = get_plugin_manager()

        self.assertIs(mgr1, mgr2)


if __name__ == "__main__":
    unittest.main()
