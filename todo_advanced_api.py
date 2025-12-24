"""
Advanced TODO System - Direct API Wrapper

This module provides a direct import path for the advanced TODO system.
Users can import from either:
  - from todo_advanced import api
  - from todo_advanced.api import add_todo, etc.
  - import todo_advanced_api (this file)

For simplicity and compatibility, this file re-exports all functions.
"""

# Re-export all public API
from todo_advanced.api import (
    # Original API (backward compatible)
    add_todo,
    list_todos,
    filter_by_tags,
    add_tag_to_task,
    remove_tag_from_task,
    show_tag_stats,
    list_all_tags,
    complete_task,
    # New advanced API
    add_structured_tag,
    list_tags_with_metadata,
    query_tasks_dsl,
    recommend_tags,
    get_tag_metadata,
    get_related_tags,
)

__version__ = "1.0.0"
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
    "get_tag_metadata",
    "get_related_tags",
]
