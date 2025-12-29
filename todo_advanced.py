"""Compatibility wrapper + advanced API for TODO app.

This module exposes the same public API as `todo_original.py` (same function names and
signatures) but backed by a persistent SQLite store and a richer tag model.

Existing callers importing `todo_original` remain unchanged. This module is opt-in for
users who want the advanced behavior.
"""
from __future__ import annotations

from typing import List, Optional, Dict
from todo_advanced.storage import SQLiteStore

DB_PATH = ".data/todo_advanced.db"

_store = SQLiteStore(DB_PATH)


def _task_row_to_dict(row) -> Dict:
    # Keep original API fields: task (string), completed (bool), tags (List[str])
    tid = row["id"]
    cur = _store._conn.execute(
        "SELECT t.name FROM tags t JOIN task_tags tt ON t.id = tt.tag_id WHERE tt.task_id = ? ORDER BY t.name ASC",
        (tid,),
    )
    tags = [r[0] for r in cur.fetchall()]
    return {"task": row["title"], "completed": bool(row["completed"]), "tags": tags}


# ---------------------------------------------------------------------------
# Public API (same names as todo_original)
# ---------------------------------------------------------------------------

def add_todo(task: str, tags: Optional[List[str]] = None) -> None:
    if tags is None:
        tags = []
    tid = _store.add_task(task, None)
    for tag in tags:
        _store.add_tag_to_task(tid, tag)


def list_todos() -> List[Dict]:
    rows = _store.list_tasks()
    return [_task_row_to_dict(r) for r in rows]


def filter_by_tags(tags: List[str], match_all: bool = False) -> List[Dict]:
    if not tags:
        return list_todos()
    assert _store._conn is not None
    placeholders = ",".join("?" for _ in tags)
    if match_all:
        # tasks that have all of the tags
        sql = f"SELECT t.* FROM tasks t JOIN task_tags tt ON t.id = tt.task_id JOIN tags g ON g.id = tt.tag_id WHERE g.name IN ({placeholders}) GROUP BY t.id HAVING COUNT(DISTINCT g.name) = ? ORDER BY t.id DESC"
        params = tags + [len(tags)]
    else:
        sql = f"SELECT DISTINCT t.* FROM tasks t JOIN task_tags tt ON t.id = tt.task_id JOIN tags g ON g.id = tt.tag_id WHERE g.name IN ({placeholders}) ORDER BY t.id DESC"
        params = tags
    cur = _store._conn.execute(sql, tuple(params))
    return [_task_row_to_dict(r) for r in cur.fetchall()]


def add_tag_to_task(index: int, tag: str) -> None:
    rows = _store.list_tasks()
    if index < 0 or index >= len(rows):
        raise IndexError("task index out of range")
    task_id = rows[index]["id"]
    _store.add_tag_to_task(task_id, tag)


def remove_tag_from_task(index: int, tag: str) -> None:
    rows = _store.list_tasks()
    if index < 0 or index >= len(rows):
        raise IndexError("task index out of range")
    task_id = rows[index]["id"]
    _store.remove_tag_from_task(task_id, tag)


def show_tag_stats() -> Dict[str, int]:
    return _store.show_tag_stats()


def list_all_tags() -> List[str]:
    return _store.list_all_tag_names()


def complete_task(index: int) -> None:
    import time
    rows = _store.list_tasks()
    if index < 0 or index >= len(rows):
        raise IndexError("task index out of range")
    tid = rows[index]["id"]
    with _store.transaction() as conn:
        conn.execute("UPDATE tasks SET completed = 1, updated_at = ? WHERE id = ?", (time.time(), tid))
