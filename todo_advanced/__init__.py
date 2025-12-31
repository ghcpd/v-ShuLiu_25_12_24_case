"""
Advanced Tag System for TODO Application.

A modern, persistent, modular, and concurrency-safe tag system that extends
the minimal todo_original.py while maintaining complete backward compatibility.
"""

__version__ = "1.0.0"

from .api import (
    add_todo,
    list_todos,
    filter_by_tags,
    add_tag_to_task,
    remove_tag_from_task,
    show_tag_stats,
    list_all_tags,
    complete_task,
    # New API functions
    add_structured_tag,
    list_tags_with_metadata,
    query_tasks_dsl,
    recommend_tags,
)

__all__ = [
    "add_todo",
    "list_todos",
    "filter_by_tags",
    "add_tag_to_task",
    "remove_tag_from_task",
    "show_tag_stats",
    "list_all_tags",
    "complete_task",
    "add_structured_tag",
    "list_tags_with_metadata",
    "query_tasks_dsl",
    "recommend_tags",
]
