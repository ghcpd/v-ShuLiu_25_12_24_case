"""Persistent storage layer using SQLite with simple migrations and concurrency safety."""
import sqlite3
import threading
import json
from datetime import datetime
from typing import List, Dict, Optional

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task TEXT NOT NULL,
        completed INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        aliases TEXT DEFAULT '[]',
        color TEXT DEFAULT NULL,
        description TEXT DEFAULT NULL,
        usage_count INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS task_tags (
        task_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        PRIMARY KEY (task_id, tag_id),
        FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE,
        FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tag_cooccurrence (
        tag_a INTEGER NOT NULL,
        tag_b INTEGER NOT NULL,
        weight INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (tag_a, tag_b)
    )
    """,
]


class Storage:
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        # enable WAL for concurrent readers/writers
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA foreign_keys=ON;")
        self._ensure_schema()
        # simple in-memory cache for tag name -> id to speed up bulk ops
        self._tag_cache = {}

    def _ensure_schema(self):
        with self._lock:
            cur = self._conn.cursor()
            for sql in SCHEMA:
                cur.execute(sql)
            self._conn.commit()

    def close(self):
        with self._lock:
            self._conn.close()

    # Tasks
    def add_task(self, task_text: str, tags: Optional[List[str]] = None) -> int:
        """Insert a task; optionally attach tags in the same transaction to avoid
        excessive commits (improves bulk-insert performance).
        """
        now = datetime.utcnow().isoformat()
        if tags is None:
            tags = []
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "INSERT INTO tasks (task, completed, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (task_text, 0, now, now),
            )
            tid = cur.lastrowid
            # attach tags within same transaction
            for tag in tags:
                tag_id = self.ensure_tag(tag)
                try:
                    cur.execute(
                        "INSERT INTO task_tags (task_id, tag_id) VALUES (?, ?)", (tid, tag_id)
                    )
                except sqlite3.IntegrityError:
                    pass
                # reuse `now` rather than calling datetime repeatedly
                cur.execute(
                    "UPDATE tags SET usage_count = usage_count + 1, updated_at = ? WHERE id=?",
                    (now, tag_id),
                )
            # update cooccurrence once for the new task
            cur.execute("SELECT tag_id FROM task_tags WHERE task_id=? ORDER BY tag_id", (tid,))
            tag_ids = [r[0] for r in cur.fetchall()]
            for i in range(len(tag_ids)):
                for j in range(i + 1, len(tag_ids)):
                    a, b = tag_ids[i], tag_ids[j]
                    if a > b:
                        a, b = b, a
                    cur.execute(
                        "INSERT INTO tag_cooccurrence (tag_a, tag_b, weight) VALUES (?, ?, 1) "
                        "ON CONFLICT(tag_a, tag_b) DO UPDATE SET weight = weight + 1",
                        (a, b),
                    )
            self._conn.commit()
            return tid

    def list_tasks(self) -> List[Dict]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM tasks ORDER BY id")
            rows = [dict(r) for r in cur.fetchall()]
            # attach tags and normalize types
            for r in rows:
                r["tags"] = self._get_tags_for_task(r["id"])
                # SQLite returns ints for booleans; convert to bool for compatibility
                r["completed"] = bool(r.get("completed"))
            return rows

    def get_task(self, task_id: int) -> Optional[Dict]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
            row = cur.fetchone()
            if not row:
                return None
            r = dict(row)
            r["tags"] = self._get_tags_for_task(r["id"])
            r["completed"] = bool(r.get("completed"))
            return r

    def complete_task(self, task_id: int) -> None:
        now = datetime.utcnow().isoformat()
        with self._lock:
            self._conn.execute(
                "UPDATE tasks SET completed=1, updated_at=? WHERE id=?", (now, task_id)
            )
            self._conn.commit()

    # Tags
    def _get_tag_row(self, name: str) -> Optional[sqlite3.Row]:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM tags WHERE name=?", (name,))
        return cur.fetchone()

    def ensure_tag(self, name: str) -> int:
        now = datetime.utcnow().isoformat()
        with self._lock:
            # check in-memory cache first
            if name in self._tag_cache:
                return self._tag_cache[name]
            cur = self._conn.cursor()
            row = self._get_tag_row(name)
            if row:
                self._tag_cache[name] = row["id"]
                return row["id"]
            cur.execute(
                "INSERT INTO tags (name, aliases, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (name, json.dumps([]), now, now),
            )
            tid = cur.lastrowid
            self._tag_cache[name] = tid
            self._conn.commit()
            return tid

    def list_tags(self) -> List[Dict]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM tags ORDER BY name")
            rows = [dict(r) for r in cur.fetchall()]
            for r in rows:
                r["aliases"] = json.loads(r.get("aliases") or "[]")
            return rows

    def get_tag_by_name(self, name: str) -> Optional[Dict]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM tags WHERE name=?", (name,))
            row = cur.fetchone()
            if not row:
                return None
            r = dict(row)
            r["aliases"] = json.loads(r.get("aliases") or "[]")
            return r

    def increment_tag_usage(self, tag_id: int) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE tags SET usage_count = usage_count + 1, updated_at = ? WHERE id=?",
                (datetime.utcnow().isoformat(), tag_id),
            )
            self._conn.commit()

    # Task <-> Tag relations
    def add_tag_to_task(self, task_id: int, tag_name: str) -> None:
        with self._lock:
            tag_id = self.ensure_tag(tag_name)
            cur = self._conn.cursor()
            try:
                cur.execute(
                    "INSERT INTO task_tags (task_id, tag_id) VALUES (?, ?)", (task_id, tag_id)
                )
            except sqlite3.IntegrityError:
                # already present
                pass
            self.increment_tag_usage(tag_id)
            self._update_cooccurrence_for_task(task_id)
            self._conn.commit()

    def remove_tag_from_task(self, task_id: int, tag_name: str) -> None:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT id FROM tags WHERE name=?", (tag_name,))
            row = cur.fetchone()
            if not row:
                return
            tag_id = row["id"]
            cur.execute("DELETE FROM task_tags WHERE task_id=? AND tag_id=?", (task_id, tag_id))
            self._conn.commit()

    def _get_tags_for_task(self, task_id: int) -> List[str]:
        cur = self._conn.cursor()
        cur.execute(
            "SELECT t.name FROM tags t JOIN task_tags tt ON t.id = tt.tag_id WHERE tt.task_id=? ORDER BY t.name",
            (task_id,),
        )
        return [r[0] for r in cur.fetchall()]

    # Co-occurrence
    def _update_cooccurrence_for_task(self, task_id: int) -> None:
        cur = self._conn.cursor()
        cur.execute(
            "SELECT tag_id FROM task_tags WHERE task_id=? ORDER BY tag_id", (task_id,)
        )
        tag_ids = [r[0] for r in cur.fetchall()]
        # increment pair counts for each combination
        for i in range(len(tag_ids)):
            for j in range(i + 1, len(tag_ids)):
                a, b = tag_ids[i], tag_ids[j]
                # store ordered pairs (min,max) to avoid duplicates
                if a > b:
                    a, b = b, a
                cur.execute(
                    "INSERT INTO tag_cooccurrence (tag_a, tag_b, weight) VALUES (?, ?, 1) "
                    "ON CONFLICT(tag_a, tag_b) DO UPDATE SET weight = weight + 1",
                    (a, b),
                )
        self._conn.commit()

    def tag_cooccurrence(self, tag_name: str, top_k: int = 5) -> List[Dict]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT id FROM tags WHERE name=?", (tag_name,))
            row = cur.fetchone()
            if not row:
                return []
            tid = row["id"]
            cur.execute(
                "SELECT t.name, c.weight FROM tag_cooccurrence c JOIN tags t ON (t.id = c.tag_b) "
                "WHERE c.tag_a=? ORDER BY c.weight DESC LIMIT ?",
                (tid, top_k),
            )
            return [{"tag": r[0], "weight": r[1]} for r in cur.fetchall()]

    # Stats
    def tag_stats(self) -> Dict[str, int]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT name, usage_count FROM tags ORDER BY name")
            return {r[0]: r[1] for r in cur.fetchall()}

    # Search helpers
    def find_tasks_by_tag_names(self, tag_names: List[str], match_all: bool = False) -> List[Dict]:
        with self._lock:
            if not tag_names:
                return self.list_tasks()
            cur = self._conn.cursor()
            # find tag ids
            cur.execute(
                "SELECT id, name FROM tags WHERE name IN ({})".format(
                    ",".join(["?"] * len(tag_names))
                ),
                tuple(tag_names),
            )
            rows = cur.fetchall()
            if not rows:
                return []
            tag_ids = [r[0] for r in rows]
            if match_all:
                # tasks that have all tag_ids
                q = (
                    "SELECT t.* FROM tasks t WHERE t.id IN ("
                    "SELECT task_id FROM task_tags WHERE tag_id IN ({}) "
                    "GROUP BY task_id HAVING COUNT(DISTINCT tag_id) = ?"
                    ") ORDER BY t.id"
                ).format(
                    ",".join(["?"] * len(tag_ids))
                )
                params = tuple(tag_ids) + (len(tag_ids),)
                cur.execute(q, params)
            else:
                q = (
                    "SELECT DISTINCT t.* FROM tasks t JOIN task_tags tt ON t.id=tt.task_id "
                    "WHERE tt.tag_id IN ({}) ORDER BY t.id"
                ).format(
                    ",".join(["?"] * len(tag_ids))
                )
                cur.execute(q, tuple(tag_ids))
            rows = [dict(r) for r in cur.fetchall()]
            for r in rows:
                r["tags"] = self._get_tags_for_task(r["id"])
            return rows
