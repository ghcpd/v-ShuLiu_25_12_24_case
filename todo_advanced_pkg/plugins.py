"""Plugin discovery and hook invocation.

Plugins are Python modules placed under `todo_plugins` package and must expose
one or more hook functions (on_task_added, on_tag_added, on_task_completed).
This loader performs simple auto-discovery and invocation.
"""
import importlib
import pkgutil
from typing import List, Callable, Any

PLUGIN_PACKAGE = "todo_plugins"


def discover_plugins() -> List[Any]:
    plugins = []
    try:
        pkg = importlib.import_module(PLUGIN_PACKAGE)
    except ModuleNotFoundError:
        return []
    for finder, name, ispkg in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
        try:
            m = importlib.import_module(name)
            plugins.append(m)
        except Exception:
            # fail-safe: ignore faulty plugins
            continue
    return plugins


def run_hook(hook_name: str, *args, **kwargs):
    for p in discover_plugins():
        fn = getattr(p, hook_name, None)
        if callable(fn):
            try:
                fn(*args, **kwargs)
            except Exception:
                # plugin errors should not break core
                continue
