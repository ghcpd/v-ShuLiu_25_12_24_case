"""Simple SQLite storage with basic migrations and file-level locking.

This is an initial implementation focusing on correctness and safety. It supports:
- persistent tasks and tags tables
- a migrations table for simple schema evolution
- per-process threading.Lock to avoid concurrent writes from same process
- a lightweight advisory lock using a lock file for multi-process safety

This module is designed to be replaced/extended with connection-pooling or WAL
based strategies if needed.
"""
from __future__ import annotations

import sqlite3
import threading
import time
import os
from contextlib import contextmanager
from typing import Iterator, Optional

DB_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS migrations (
    id TEXT PRIMARY KEY,
    applied_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT,
    completed INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    color TEXT,
    aliases TEXT,
    usage_count INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS task_tags (
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (task_id, tag_id)
);
"""

LOCKFILE_SUFFIX = ".lock"


class SQLiteStore:
    def __init__(self, path: str):
        self.path = path
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = threading.RLock()
        self._ensure_db()

    def _ensure_db(self) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        need_init = not os.path.exists(self.path)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        if need_init:
            self._conn.executescript(DB_SCHEMA)
            self._conn.commit()

    @contextmanager
    def _advisory_lock(self) -> Iterator[None]:
        """A simple advisory lock using a lockfile; cooperative between processes."""
        lockfile = self.path + LOCKFILE_SUFFIX
        with self._lock:
            # spin until we can create the lockfile
            start = time.time()
            while True:
                try:
                    fd = os.open(lockfile, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                    os.close(fd)
                    break
                except FileExistsError:
                    time.sleep(0.01)
                    if time.time() - start > 5:
                        raise TimeoutError("Timeout waiting for db lock")
            try:
                yield
            finally:
                try:
                    os.remove(lockfile)
                except Exception:
                    pass

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self._advisory_lock():
            assert self._conn is not None
            cur = self._conn
            try:
                cur.execute("BEGIN IMMEDIATE")
                yield cur
                cur.commit()
            except Exception:
                cur.rollback()
                raise

    def add_task(self, title: str, body: str | None = None) -> int:
        now = time.time()
        with self.transaction() as conn:
            cur = conn.execute(
                "INSERT INTO tasks (title, body, completed, created_at, updated_at) VALUES (?, ?, 0, ?, ?)",
                (title, body, now, now),
            )
            return cur.lastrowid

    def list_tasks(self) -> list[sqlite3.Row]:
        assert self._conn is not None
        cur = self._conn.execute("SELECT * FROM tasks ORDER BY id DESC")
        return list(cur.fetchall())

    def get_task(self, task_id: int) -> Optional[sqlite3.Row]:
        assert self._conn is not None
        cur = self._conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        return cur.fetchone()

    # Tag management methods
    def get_tag_by_name(self, name: str) -> Optional[sqlite3.Row]:
        assert self._conn is not None
        cur = self._conn.execute("SELECT * FROM tags WHERE name = ?", (name,))
        return cur.fetchone()

    def create_or_update_tag(self, name: str, description: str | None = None, color: str | None = None, aliases: str | None = None) -> int:
        now = time.time()
        with self.transaction() as conn:
            existing = conn.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()
            if existing:
                conn.execute(
                    "UPDATE tags SET description = COALESCE(?, description), color = COALESCE(?, color), aliases = COALESCE(?, aliases), updated_at = ? WHERE id = ?",
                    (description, color, aliases, now, existing[0]),
                )
                return existing[0]
            cur = conn.execute(
                "INSERT INTO tags (name, description, color, aliases, usage_count, created_at, updated_at) VALUES (?, ?, ?, ?, 0, ?, ?)",
                (name, description, color, aliases, now, now),
            )
            return cur.lastrowid

    def add_tag_to_task(self, task_id: int, tag_name: str) -> None:
        tag_row = self.get_tag_by_name(tag_name)
        if tag_row is None:
            tag_id = self.create_or_update_tag(tag_name)
        else:
            tag_id = tag_row["id"]
        with self.transaction() as conn:
            conn.execute("INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?, ?)", (task_id, tag_id))
            conn.execute("UPDATE tags SET usage_count = usage_count + 1, updated_at = ? WHERE id = ?", (time.time(), tag_id))

    def remove_tag_from_task(self, task_id: int, tag_name: str) -> None:
        tag_row = self.get_tag_by_name(tag_name)
        if tag_row is None:
            return
        tag_id = tag_row["id"]
        with self.transaction() as conn:
            conn.execute("DELETE FROM task_tags WHERE task_id = ? AND tag_id = ?", (task_id, tag_id))
            conn.execute("UPDATE tags SET usage_count = MAX(0, usage_count - 1), updated_at = ? WHERE id = ?", (time.time(), tag_id))

    def list_tags(self) -> list[sqlite3.Row]:
        assert self._conn is not None
        cur = self._conn.execute("SELECT * FROM tags ORDER BY usage_count DESC, name ASC")
        return list(cur.fetchall())

    def show_tag_stats(self) -> dict:
        assert self._conn is not None
        cur = self._conn.execute("SELECT name, usage_count FROM tags")
        return {row["name"]: row["usage_count"] for row in cur.fetchall()}

    def list_all_tag_names(self) -> list[str]:
        assert self._conn is not None
        cur = self._conn.execute("SELECT name FROM tags ORDER BY name ASC")
        return [r[0] for r in cur.fetchall()]

    def add_tasks_bulk(self, titles) -> None:
        """Add many tasks efficiently in a single transaction."""
        now = time.time()
        with self.transaction() as conn:
            conn.executemany(
                "INSERT INTO tasks (title, body, completed, created_at, updated_at) VALUES (?, ?, 0, ?, ?)",
                [(t, None, now, now) for t in titles],
            )
