"""
plugins.py - Plugin system with hooks and auto-discovery.
"""

import importlib
import pkgutil
from typing import Dict, List, Callable, Any


class PluginManager:
    def __init__(self):
        self.hooks: Dict[str, List[Callable]] = {}
        self.plugins = []

    def load_plugins(self, package_name: str = 'plugins'):
        try:
            package = importlib.import_module(package_name)
            for _, name, _ in pkgutil.iter_modules(package.__path__):
                module = importlib.import_module(f'{package_name}.{name}')
                if hasattr(module, 'register'):
                    module.register(self)
                self.plugins.append(module)
        except ImportError:
            pass  # No plugins

    def register_hook(self, hook_name: str, func: Callable):
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        self.hooks[hook_name].append(func)

    def trigger_hook(self, hook_name: str, *args, **kwargs):
        if hook_name in self.hooks:
            for func in self.hooks[hook_name]:
                func(*args, **kwargs)

    def add_custom_operator(self, name: str, func: Callable):
        # For query engine
        pass  # Will integrate with query.py