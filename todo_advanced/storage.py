"""
Persistent storage layer for tasks and tags.

Supports SQLite with concurrent access, automatic schema evolution,
and transaction safety.
"""

import sqlite3
import json
import threading
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class TaskRecord:
    """Internal task record."""
    id: int
    task: str
    completed: bool
    tags: List[str]
    created_at: str
    updated_at: str


@dataclass
class TagRecord:
    """Internal structured tag record."""
    name: str
    description: str = ""
    color: str = "#CCCCCC"
    aliases: List[str] = None
    usage_count: int = 0
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.utcnow().isoformat()


class StorageBackend:
    """Abstract base for storage backends."""

    def add_task(self, task: str, tags: List[str]) -> int:
        raise NotImplementedError

    def list_tasks(self) -> List[Dict]:
        raise NotImplementedError

    def get_task(self, task_id: int) -> Optional[Dict]:
        raise NotImplementedError

    def update_task(self, task_id: int, **updates) -> bool:
        raise NotImplementedError

    def delete_task(self, task_id: int) -> bool:
        raise NotImplementedError

    def add_tag_metadata(self, name: str, **metadata) -> bool:
        raise NotImplementedError

    def get_tag_metadata(self, name: str) -> Optional[Dict]:
        raise NotImplementedError

    def list_all_tags_metadata(self) -> List[Dict]:
        raise NotImplementedError

    def record_tag_usage(self, tag_name: str) -> None:
        raise NotImplementedError

    def get_tag_cooccurrence(self, tag1: str, tag2: str) -> int:
        raise NotImplementedError

    def record_tag_cooccurrence(self, tag1: str, tag2: str) -> None:
        raise NotImplementedError


class SQLiteBackend(StorageBackend):
    """SQLite-based persistent storage with thread-safety."""

    def __init__(self, db_path: str = "todo_advanced.db"):
        self.db_path = Path(db_path)
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self):
        """Get a new database connection."""
        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database schema."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()

                # Tasks table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task TEXT NOT NULL,
                        completed BOOLEAN DEFAULT 0,
                        tags TEXT DEFAULT '[]',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)

                # Tags metadata table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tag_metadata (
                        name TEXT PRIMARY KEY,
                        description TEXT DEFAULT '',
                        color TEXT DEFAULT '#CCCCCC',
                        aliases TEXT DEFAULT '[]',
                        usage_count INTEGER DEFAULT 0,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)

                # Tag co-occurrence table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tag_cooccurrence (
                        tag1 TEXT NOT NULL,
                        tag2 TEXT NOT NULL,
                        count INTEGER DEFAULT 1,
                        PRIMARY KEY (tag1, tag2),
                        FOREIGN KEY (tag1) REFERENCES tag_metadata(name),
                        FOREIGN KEY (tag2) REFERENCES tag_metadata(name)
                    )
                """)

                conn.commit()
            finally:
                conn.close()

    def add_task(self, task: str, tags: List[str]) -> int:
        """Add a new task and return its ID."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                now = datetime.utcnow().isoformat()
                tags_json = json.dumps(tags)

                cursor.execute("""
                    INSERT INTO tasks (task, tags, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (task, tags_json, now, now))

                conn.commit()
                return cursor.lastrowid
            finally:
                conn.close()

    def list_tasks(self) -> List[Dict]:
        """List all tasks."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, task, completed, tags, created_at, updated_at
                    FROM tasks
                    ORDER BY id
                """)
                rows = cursor.fetchall()
                return [
                    {
                        "id": row["id"],
                        "task": row["task"],
                        "completed": bool(row["completed"]),
                        "tags": json.loads(row["tags"]),
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                    }
                    for row in rows
                ]
            finally:
                conn.close()

    def get_task(self, task_id: int) -> Optional[Dict]:
        """Get a specific task by ID."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, task, completed, tags, created_at, updated_at
                    FROM tasks WHERE id = ?
                """, (task_id,))
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row["id"],
                        "task": row["task"],
                        "completed": bool(row["completed"]),
                        "tags": json.loads(row["tags"]),
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                    }
                return None
            finally:
                conn.close()

    def update_task(self, task_id: int, **updates) -> bool:
        """Update a task with given fields."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                now = datetime.utcnow().isoformat()
                updates["updated_at"] = now

                # JSON serialize tags if present
                if "tags" in updates and isinstance(updates["tags"], list):
                    updates["tags"] = json.dumps(updates["tags"])

                set_clauses = ", ".join([f"{k} = ?" for k in updates.keys()])
                values = list(updates.values()) + [task_id]

                cursor.execute(f"""
                    UPDATE tasks SET {set_clauses} WHERE id = ?
                """, values)

                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()

    def delete_task(self, task_id: int) -> bool:
        """Delete a task by ID."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()

    def add_tag_metadata(self, name: str, **metadata) -> bool:
        """Add or update tag metadata."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                now = datetime.utcnow().isoformat()

                description = metadata.get("description", "")
                color = metadata.get("color", "#CCCCCC")
                aliases = json.dumps(metadata.get("aliases", []))
                usage_count = metadata.get("usage_count", 0)

                cursor.execute("""
                    INSERT OR REPLACE INTO tag_metadata
                    (name, description, color, aliases, usage_count, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (name, description, color, aliases, usage_count, now, now))

                conn.commit()
                return True
            finally:
                conn.close()

    def get_tag_metadata(self, name: str) -> Optional[Dict]:
        """Get metadata for a specific tag."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name, description, color, aliases, usage_count, created_at, updated_at
                    FROM tag_metadata WHERE name = ?
                """, (name,))
                row = cursor.fetchone()
                if row:
                    return {
                        "name": row["name"],
                        "description": row["description"],
                        "color": row["color"],
                        "aliases": json.loads(row["aliases"]),
                        "usage_count": row["usage_count"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                    }
                return None
            finally:
                conn.close()

    def list_all_tags_metadata(self) -> List[Dict]:
        """List metadata for all tags."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name, description, color, aliases, usage_count, created_at, updated_at
                    FROM tag_metadata
                    ORDER BY name
                """)
                rows = cursor.fetchall()
                return [
                    {
                        "name": row["name"],
                        "description": row["description"],
                        "color": row["color"],
                        "aliases": json.loads(row["aliases"]),
                        "usage_count": row["usage_count"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                    }
                    for row in rows
                ]
            finally:
                conn.close()

    def record_tag_usage(self, tag_name: str) -> None:
        """Increment usage count for a tag."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                now = datetime.utcnow().isoformat()

                cursor.execute("""
                    UPDATE tag_metadata
                    SET usage_count = usage_count + 1, updated_at = ?
                    WHERE name = ?
                """, (now, tag_name))

                conn.commit()
            finally:
                conn.close()

    def record_tag_cooccurrence(self, tag1: str, tag2: str) -> None:
        """Record co-occurrence of two tags."""
        if tag1 == tag2:
            return

        # Normalize order for bidirectional lookup
        t1, t2 = sorted([tag1, tag2])

        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO tag_cooccurrence (tag1, tag2, count)
                    VALUES (?, ?, 1)
                    ON CONFLICT(tag1, tag2) DO UPDATE SET count = count + 1
                """, (t1, t2))

                conn.commit()
            finally:
                conn.close()

    def get_tag_cooccurrence(self, tag1: str, tag2: str) -> int:
        """Get co-occurrence count between two tags."""
        t1, t2 = sorted([tag1, tag2])

        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT count FROM tag_cooccurrence
                    WHERE tag1 = ? AND tag2 = ?
                """, (t1, t2))
                row = cursor.fetchone()
                return row["count"] if row else 0
            finally:
                conn.close()


# Global storage instance
_storage_instance: Optional[SQLiteBackend] = None


def get_storage(db_path: str = "todo_advanced.db") -> SQLiteBackend:
    """Get or create the global storage instance."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = SQLiteBackend(db_path)
    return _storage_instance


def reset_storage() -> None:
    """Reset the global storage instance (for testing)."""
    global _storage_instance
    _storage_instance = None
