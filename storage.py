"""
storage.py - Persistent storage using SQLite with concurrency safety.
"""

import sqlite3
import json
import threading
from contextlib import contextmanager
from datetime import datetime
from typing import List, Dict, Any
from models import Task, Tag


class Storage:
    def __init__(self, db_path: str = "todo_advanced.db"):
        self.db_path = db_path
        self.lock = threading.RLock()  # Reentrant lock for concurrency
        self._init_db()

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY,
                    task TEXT NOT NULL,
                    completed BOOLEAN DEFAULT FALSE,
                    tags TEXT DEFAULT '[]',  -- JSON list
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    name TEXT PRIMARY KEY,
                    aliases TEXT DEFAULT '[]',  -- JSON set
                    color TEXT DEFAULT '#FFFFFF',
                    description TEXT DEFAULT '',
                    created_at TEXT,
                    updated_at TEXT,
                    usage_count INTEGER DEFAULT 0,
                    co_occurrences TEXT DEFAULT '{}'  -- JSON dict
                )
            """)
            conn.commit()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        try:
            yield conn
        finally:
            conn.close()

    def save_task(self, task: Task):
        with self.lock, self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO tasks (id, task, completed, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                task.id,
                task.task,
                task.completed,
                json.dumps(task.tags),
                task.created_at.isoformat(),
                task.updated_at.isoformat()
            ))
            conn.commit()

    def load_tasks(self) -> List[Task]:
        with self.lock, self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM tasks").fetchall()
            tasks = []
            for row in rows:
                id_, task_str, completed, tags_json, created_at, updated_at = row
                tags = json.loads(tags_json)
                created = datetime.fromisoformat(created_at)
                updated = datetime.fromisoformat(updated_at)
                task = Task(id=id_, task=task_str, completed=bool(completed), tags=tags, created_at=created, updated_at=updated)
                tasks.append(task)
            return tasks

    def delete_task(self, task_id: int):
        with self.lock, self._get_connection() as conn:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()

    def save_tag(self, tag: Tag):
        with self.lock, self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO tags (name, aliases, color, description, created_at, updated_at, usage_count, co_occurrences)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tag.name,
                json.dumps(list(tag.aliases)),
                tag.color,
                tag.description,
                tag.created_at.isoformat(),
                tag.updated_at.isoformat(),
                tag.usage_count,
                json.dumps(tag.co_occurrences)
            ))
            conn.commit()

    def load_tags(self) -> Dict[str, Tag]:
        with self.lock, self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM tags").fetchall()
            tags = {}
            for row in rows:
                name, aliases_json, color, desc, created_at, updated_at, usage, co_json = row
                aliases = set(json.loads(aliases_json))
                co_occurrences = json.loads(co_json)
                created = datetime.fromisoformat(created_at)
                updated = datetime.fromisoformat(updated_at)
                tag = Tag(
                    name=name,
                    aliases=aliases,
                    color=color,
                    description=desc,
                    created_at=created,
                    updated_at=updated,
                    usage_count=usage,
                    co_occurrences=co_occurrences
                )
                tags[name] = tag
            return tags

    def delete_tag(self, tag_name: str):
        with self.lock, self._get_connection() as conn:
            conn.execute("DELETE FROM tags WHERE name = ?", (tag_name,))
            conn.commit()