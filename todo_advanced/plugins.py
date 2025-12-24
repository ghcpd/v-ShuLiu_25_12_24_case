"""
Plugin system for extensibility.

Provides auto-discovery of plugins and hook system for custom behaviors.
"""

import importlib
import inspect
from pathlib import Path
from typing import Callable, List, Dict, Any, Optional


class PluginHook:
    """Represents a hook that plugins can subscribe to."""

    def __init__(self, name: str):
        self.name = name
        self._handlers: List[Callable] = []

    def subscribe(self, handler: Callable) -> None:
        """Subscribe a handler to this hook."""
        if handler not in self._handlers:
            self._handlers.append(handler)

    def unsubscribe(self, handler: Callable) -> None:
        """Unsubscribe a handler from this hook."""
        if handler in self._handlers:
            self._handlers.remove(handler)

    def fire(self, *args, **kwargs) -> List[Any]:
        """Fire the hook and collect results from all handlers."""
        results = []
        for handler in self._handlers:
            try:
                result = handler(*args, **kwargs)
                results.append(result)
            except Exception as e:
                print(f"Error in hook handler {handler.__name__}: {e}")
        return results


class PluginManager:
    """Manages plugins and hooks."""

    def __init__(self):
        self._hooks: Dict[str, PluginHook] = {}
        self._plugins: Dict[str, Any] = {}
        self._init_default_hooks()

    def _init_default_hooks(self) -> None:
        """Initialize default hooks."""
        hook_names = [
            "on_task_added",
            "on_task_updated",
            "on_task_completed",
            "on_task_deleted",
            "on_tag_added",
            "on_tag_updated",
            "on_tag_deleted",
            "on_query_executed",
        ]
        for name in hook_names:
            self._hooks[name] = PluginHook(name)

    def get_hook(self, name: str) -> Optional[PluginHook]:
        """Get a hook by name."""
        return self._hooks.get(name)

    def subscribe(self, hook_name: str, handler: Callable) -> None:
        """Subscribe a handler to a hook."""
        hook = self._hooks.get(hook_name)
        if hook:
            hook.subscribe(handler)

    def unsubscribe(self, hook_name: str, handler: Callable) -> None:
        """Unsubscribe a handler from a hook."""
        hook = self._hooks.get(hook_name)
        if hook:
            hook.unsubscribe(handler)

    def fire_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Fire a hook."""
        hook = self._hooks.get(hook_name)
        if hook:
            return hook.fire(*args, **kwargs)
        return []

    def load_plugin(self, plugin_module: str) -> bool:
        """Load a plugin module."""
        try:
            module = importlib.import_module(plugin_module)
            self._plugins[plugin_module] = module

            # Auto-register hooks if plugin has register_hooks function
            if hasattr(module, "register_hooks"):
                module.register_hooks(self)

            return True
        except Exception as e:
            print(f"Error loading plugin {plugin_module}: {e}")
            return False

    def discover_plugins(self, plugin_dir: str = "plugins") -> List[str]:
        """Auto-discover and load plugins from a directory."""
        plugin_path = Path(plugin_dir)
        if not plugin_path.exists():
            return []

        loaded = []
        for file in plugin_path.glob("*.py"):
            if file.name.startswith("_"):
                continue
            module_name = f"plugins.{file.stem}"
            if self.load_plugin(module_name):
                loaded.append(module_name)

        return loaded

    def list_plugins(self) -> List[str]:
        """List loaded plugins."""
        return list(self._plugins.keys())


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get or create global plugin manager."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


def reset_plugin_manager() -> None:
    """Reset plugin manager (for testing)."""
    global _plugin_manager
    _plugin_manager = None
