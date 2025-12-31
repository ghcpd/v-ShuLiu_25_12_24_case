"""
Main API wrapper providing backward compatibility and new features.

This module bridges the original todo_original.py API with the advanced
tag system, maintaining 100% backward compatibility.
"""

from typing import List, Optional, Dict
from .storage import get_storage
from .tags import get_tag_manager
from .query_dsl import QueryDSL
from .recommendations import get_recommender
from .plugins import get_plugin_manager
from .validation import Validator


# Initialize managers at import time
def _init_managers():
    """Initialize all managers."""
    get_storage()
    get_tag_manager()
    get_plugin_manager()


_init_managers()


# ============================================================================
# BACKWARD-COMPATIBLE API (from todo_original.py)
# ============================================================================


def add_todo(task: str, tags: Optional[List[str]] = None) -> None:
    """Add a task with optional string tags. (Original API)"""
    if tags is None:
        tags = []

    # Validate
    valid, error = Validator.validate_task(task)
    if not valid:
        raise ValueError(error)

    valid, error = Validator.validate_tags_list(tags)
    if not valid:
        raise ValueError(error)

    # Add to storage
    storage = get_storage()
    task_id = storage.add_task(task, tags)

    # Record tag usage and co-occurrence
    tag_manager = get_tag_manager()
    for tag in tags:
        tag_manager.record_usage(tag)

    # Record co-occurrence
    for i, tag1 in enumerate(tags):
        for tag2 in tags[i + 1 :]:
            tag_manager.record_cooccurrence(tag1, tag2)

    # Fire hook
    plugin_mgr = get_plugin_manager()
    plugin_mgr.fire_hook("on_task_added", task_id, task, tags)


def list_todos() -> List[Dict]:
    """Return all tasks in their current form. (Original API)"""
    storage = get_storage()
    tasks = storage.list_tasks()

    # Convert to original format (without timestamps and IDs)
    return [
        {
            "task": t["task"],
            "completed": t["completed"],
            "tags": t["tags"],
        }
        for t in tasks
    ]


def filter_by_tags(tags: List[str], match_all: bool = False) -> List[Dict]:
    """
    Filter tasks by plain string tags. (Original API)
    - match_all=False: OR logic
    - match_all=True:  AND logic
    """
    storage = get_storage()
    all_tasks = storage.list_tasks()

    if not tags:
        return [
            {
                "task": t["task"],
                "completed": t["completed"],
                "tags": t["tags"],
            }
            for t in all_tasks
        ]

    filtered = []
    for item in all_tasks:
        item_tags = item.get("tags", [])
        if match_all:
            if all(tag in item_tags for tag in tags):
                filtered.append(item)
        else:
            if any(tag in item_tags for tag in tags):
                filtered.append(item)

    return [
        {
            "task": t["task"],
            "completed": t["completed"],
            "tags": t["tags"],
        }
        for t in filtered
    ]


def add_tag_to_task(index: int, tag: str) -> None:
    """Append a single string tag to a task by index. (Original API)"""
    storage = get_storage()
    tasks = storage.list_tasks()

    if index < 0 or index >= len(tasks):
        raise IndexError("task index out of range")

    # Validate tag
    valid, error = Validator.validate_tag_name(tag)
    if not valid:
        raise ValueError(error)

    task = tasks[index]
    if tag not in task["tags"]:
        new_tags = task["tags"] + [tag]

        # Update in storage by task ID
        storage.update_task(task["id"], tags=new_tags)

        # Record usage
        tag_manager = get_tag_manager()
        tag_manager.record_usage(tag)

        # Fire hook
        plugin_mgr = get_plugin_manager()
        plugin_mgr.fire_hook("on_task_updated", task["id"], task["task"], new_tags)


def remove_tag_from_task(index: int, tag: str) -> None:
    """Remove a tag from a task. (Original API)"""
    storage = get_storage()
    tasks = storage.list_tasks()

    if index < 0 or index >= len(tasks):
        raise IndexError("task index out of range")

    task = tasks[index]
    if tag in task["tags"]:
        new_tags = [t for t in task["tags"] if t != tag]
        storage.update_task(task["id"], tags=new_tags)

        # Fire hook
        plugin_mgr = get_plugin_manager()
        plugin_mgr.fire_hook("on_task_updated", task["id"], task["task"], new_tags)


def show_tag_stats() -> Dict[str, int]:
    """Return a dict of tag -> count. (Original API)"""
    storage = get_storage()
    all_tasks = storage.list_tasks()

    stats = {}
    for item in all_tasks:
        for tag in item.get("tags", []):
            stats[tag] = stats.get(tag, 0) + 1
    return stats


def list_all_tags() -> List[str]:
    """Return all distinct string tags. (Original API)"""
    storage = get_storage()
    all_tasks = storage.list_tasks()

    result = set()
    for item in all_tasks:
        for tag in item.get("tags", []):
            result.add(tag)
    return sorted(result)


def complete_task(index: int) -> None:
    """Mark a task as completed. (Original API)"""
    storage = get_storage()
    tasks = storage.list_tasks()

    if index < 0 or index >= len(tasks):
        raise IndexError("task index out of range")

    task = tasks[index]
    storage.update_task(task["id"], completed=True)

    # Fire hook
    plugin_mgr = get_plugin_manager()
    plugin_mgr.fire_hook("on_task_completed", task["id"], task["task"])


# ============================================================================
# NEW ADVANCED API FUNCTIONS
# ============================================================================


def add_structured_tag(
    name: str,
    description: str = "",
    color: str = "#CCCCCC",
    aliases: Optional[List[str]] = None,
) -> Dict:
    """
    Create a structured tag with metadata.

    Args:
        name: Tag name
        description: Optional description
        color: Optional hex color code (default: #CCCCCC)
        aliases: Optional list of aliases

    Returns:
        Tag metadata dictionary
    """
    # Validate
    valid, error = Validator.validate_tag_name(name)
    if not valid:
        raise ValueError(f"Invalid tag name: {error}")

    if color and not color.startswith("#CCCCCC"):
        valid, error = Validator.validate_color(color)
        if not valid:
            raise ValueError(f"Invalid color: {error}")

    tag_manager = get_tag_manager()
    tag = tag_manager.create_tag(name, description, color, aliases or [])

    # Fire hook
    plugin_mgr = get_plugin_manager()
    plugin_mgr.fire_hook("on_tag_added", name, tag.to_dict())

    return tag.to_dict()


def list_tags_with_metadata() -> List[Dict]:
    """
    List all tags with their metadata.

    Returns:
        List of tag dictionaries with full metadata
    """
    tag_manager = get_tag_manager()
    tags = tag_manager.list_tags()
    return [tag.to_dict() for tag in tags]


def query_tasks_dsl(query: str) -> List[Dict]:
    """
    Execute a DSL query against tasks.

    Examples:
        tag:work AND urgent
        (tag:work OR tag:office) AND NOT completed:true
        task:email

    Args:
        query: DSL query string

    Returns:
        List of matching tasks
    """
    storage = get_storage()
    all_tasks = storage.list_tasks()

    try:
        result_tasks = QueryDSL.execute(query, all_tasks)

        # Fire hook
        plugin_mgr = get_plugin_manager()
        plugin_mgr.fire_hook("on_query_executed", query, len(result_tasks))

        # Convert to original format
        return [
            {
                "task": t["task"],
                "completed": t["completed"],
                "tags": t["tags"],
            }
            for t in result_tasks
        ]
    except ValueError as e:
        raise ValueError(f"Invalid DSL query: {e}")


def recommend_tags(
    task_text: str, existing_tags: Optional[List[str]] = None, limit: int = 5
) -> List[tuple]:
    """
    Recommend tags for a task based on content and history.

    Args:
        task_text: Task description
        existing_tags: Tags already assigned to task
        limit: Maximum number of recommendations

    Returns:
        List of (tag_name, score) tuples
    """
    recommender = get_recommender()
    return recommender.recommend_by_task_content(task_text, existing_tags, limit)


def get_tag_metadata(tag_name: str) -> Optional[Dict]:
    """Get metadata for a specific tag."""
    tag_manager = get_tag_manager()
    tag = tag_manager.get_tag(tag_name)
    return tag.to_dict() if tag else None


def get_related_tags(tag_name: str, limit: int = 5) -> List[tuple]:
    """
    Get tags that frequently co-occur with the given tag.

    Returns:
        List of (tag_name, cooccurrence_count) tuples
    """
    tag_manager = get_tag_manager()
    return tag_manager.get_related_tags(tag_name, limit)
