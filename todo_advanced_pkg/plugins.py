"""Simple plugin discovery and hook invocation.

Plugins are Python modules placed under `todo_advanced_plugins` package or
registered by module name. Each plugin may implement any of the hook
functions documented here (they are optional and run isolated from the core).

Hooks:
- on_task_added(task_row)
- on_tag_added(tag_row)
- on_task_completed(task_row)
"""
from __future__ import annotations
import importlib
import pkgutil
import sys
from types import ModuleType
from typing import List, Iterator


_PLUGIN_PACKAGE = "todo_advanced_plugins"
_registered: List[str] = []


def discover_plugins() -> List[str]:
    names = list(_registered)
    # discover in-package plugins if package exists
    try:
        pkg = importlib.import_module(_PLUGIN_PACKAGE)
    except Exception:
        return names
    for finder, name, ispkg in pkgutil.iter_modules(pkg.__path__):
        fq = f"{_PLUGIN_PACKAGE}.{name}"
        if fq not in names:
            names.append(fq)
    return names


def register_plugin_by_name(name: str) -> ModuleType:
    mod = importlib.import_module(name)
    if name not in _registered:
        _registered.append(name)
    return mod


def iter_plugins() -> Iterator[ModuleType]:
    for name in list(_registered):
        try:
            yield importlib.import_module(name)
        except Exception:
            continue


# auto-register any plugins listed on sys.modules that look right
for n, m in list(sys.modules.items()):
    if n.startswith(_PLUGIN_PACKAGE + "."):
        _registered.append(n)
