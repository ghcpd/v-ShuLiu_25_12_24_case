"""Plugin discovery and hook system.

Plugins are simple modules providing hook functions: on_task_added, on_tag_added, on_task_completed
and optionally custom query operators.

Auto-discovery looks for modules under `todo_advanced_plugins` entry point (simple filesystem scan for now).
"""
from __future__ import annotations

import importlib
import pkgutil
import logging
from typing import Callable, List

logger = logging.getLogger(__name__)

HOOKS = ["on_task_added", "on_tag_added", "on_task_completed"]


def discover_plugins(package_name: str = "todo_advanced_plugins") -> List[object]:
    plugins = []
    try:
        pkg = importlib.import_module(package_name)
    except ModuleNotFoundError:
        return []
    for finder, name, ispkg in pkgutil.iter_modules(pkg.__path__):
        full = f"{package_name}.{name}"
        try:
            mod = importlib.import_module(full)
            plugins.append(mod)
            logger.info("Loaded plugin %s", full)
        except Exception:
            logger.exception("Failed to load plugin %s", full)
    return plugins


def call_hook(hook: str, *args, **kwargs):
    for mod in discover_plugins():
        fn = getattr(mod, hook, None)
        if callable(fn):
            try:
                fn(*args, **kwargs)
            except Exception:
                logger.exception("Plugin hook %s failed", hook)
