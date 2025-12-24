"""
todo_advanced.py

Backward-compatible wrapper that exposes the same public API as
`todo_original.py` but backed by a persistent, feature-rich tag system
implemented in the `todo_advanced_pkg` package.

This file intentionally keeps the original API signatures and behaviour so
existing callers don't break.
"""
from typing import List, Dict, Optional

from todo_advanced_pkg.core import AdvancedTodo

# single shared instance used by wrapper functions (keeps public API identical)
_store = AdvancedTodo("todo_advanced.db")


def add_todo(task: str, tags: Optional[List[str]] = None) -> None:
    _store.add_task(task, tags or [])


def list_todos() -> List[Dict]:
    return _store.list_tasks()


def filter_by_tags(tags: List[str], match_all: bool = False) -> List[Dict]:
    return _store.filter_tasks_by_tags(tags, match_all=match_all)


def add_tag_to_task(index: int, tag: str) -> None:
    _store.add_tag_to_task(index, tag)


def remove_tag_from_task(index: int, tag: str) -> None:
    _store.remove_tag_from_task(index, tag)


def show_tag_stats() -> Dict[str, int]:
    return _store.tag_stats()


def list_all_tags() -> List[str]:
    return _store.list_tags()


def complete_task(index: int) -> None:
    _store.complete_task(index)


# Advanced capabilities exposed for users who want them (optional)
def query_dsl(expression: str) -> List[Dict]:
    """Run the mini-DSL query and return matching tasks."""
    return _store.query(expression)


def recommend_tags_for_text(text: str, top_k: int = 5) -> List[str]:
    return _store.recommend_tags(text, top_k=top_k)
