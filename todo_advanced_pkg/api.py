"""Public programmatic API for the advanced TODO system.

This module intentionally preserves the signatures and behavior of the
original lightweight API (see `todo_original.py`) while exposing richer
capabilities via additional functions (not imported into the legacy
wrapper).
"""
from typing import List, Optional, Dict, Any
from todo_advanced_pkg import storage, tags, query, plugins
from todo_advanced_pkg.models import Task


# --- Backward-compatible API ------------------------------------------------

def add_todo(task: str, tags: Optional[List[str]] = None) -> None:
    storage.add_task(task, tags or [])


def list_todos() -> List[Dict]:
    rows = storage.list_tasks()
    # preserve exact legacy dict shape
    return [Task(**r).to_legacy_dict() for r in rows]


def filter_by_tags(tags: List[str], match_all: bool = False) -> List[Dict]:
    # emulate original behavior using the persistent store
    all_tasks = storage.list_tasks()
    if not tags:
        return [Task(**r).to_legacy_dict() for r in all_tasks]
    out = []
    for r in all_tasks:
        item_tags = r.get("tags", [])
        if match_all:
            if all(t in item_tags for t in tags):
                out.append(Task(**r).to_legacy_dict())
        else:
            if any(t in item_tags for t in tags):
                out.append(Task(**r).to_legacy_dict())
    return out


def add_tag_to_task(index: int, tag: str) -> None:
    storage.add_tag_to_task_by_index(index, tag)


def remove_tag_from_task(index: int, tag: str) -> None:
    storage.remove_tag_from_task_by_index(index, tag)


def show_tag_stats() -> Dict[str, int]:
    return storage.tag_stats()


def list_all_tags() -> List[str]:
    return storage.all_tags()


def complete_task(index: int) -> None:
    storage.complete_task_by_index(index)


# --- Advanced API (new functionality) --------------------------------------

def query_tasks(dsl: str, limit: Optional[int] = 100) -> List[Dict[str, Any]]:
    """Run the mini-DSL and return scored tasks (rich dicts)."""
    return query.execute(dsl, limit=limit)


def recommend_tags(text: str, top_n: int = 5) -> List[Dict[str, Any]]:
    recs = tags.recommend_tags_for_text(text, top_n=top_n)
    return [{"tag": n, "score": s} for n, s in recs]


def register_plugin(module_name: str):
    plugins.register_plugin_by_name(module_name)


def discover_plugins() -> List[str]:
    return plugins.discover_plugins()


# Plugin hooks (fire-and-forget; plugins should be resilient)
def _emit_hook(hook_name: str, *args, **kwargs):
    for p in plugins.iter_plugins():
        try:
            fn = getattr(p, hook_name, None)
            if callable(fn):
                fn(*args, **kwargs)
        except Exception:
            # plugins are isolated: fail silently
            pass


def _on_task_added(task_row: Dict):
    _emit_hook("on_task_added", task_row)


# Note: new APIs intentionally not exported to the legacy wrapper to avoid
# changing the original surface by accident.
