"""Backward-compatible wrapper exposing the original API while providing
an advanced, persistent tag system implemented in the `todo_advanced_pkg` package.

This module preserves the exact public API and behavior of `todo_original.py`
but persists data to SQLite and provides advanced tagging features via the
`todo_advanced_pkg` implementation.
"""
from typing import List, Optional, Dict

from todo_advanced_pkg.api import (
    add_todo as _add_todo,
    list_todos as _list_todos,
    filter_by_tags as _filter_by_tags,
    add_tag_to_task as _add_tag_to_task,
    remove_tag_from_task as _remove_tag_from_task,
    show_tag_stats as _show_tag_stats,
    list_all_tags as _list_all_tags,
    complete_task as _complete_task,
)


# Public API (signatures kept identical to todo_original.py)

def add_todo(task: str, tags: Optional[List[str]] = None) -> None:
    return _add_todo(task, tags)


def list_todos() -> List[Dict]:
    return _list_todos()


def filter_by_tags(tags: List[str], match_all: bool = False) -> List[Dict]:
    return _filter_by_tags(tags, match_all=match_all)


def add_tag_to_task(index: int, tag: str) -> None:
    return _add_tag_to_task(index, tag)


def remove_tag_from_task(index: int, tag: str) -> None:
    return _remove_tag_from_task(index, tag)


def show_tag_stats() -> Dict[str, int]:
    return _show_tag_stats()


def list_all_tags() -> List[str]:
    return _list_all_tags()


def complete_task(index: int) -> None:
    return _complete_task(index)
