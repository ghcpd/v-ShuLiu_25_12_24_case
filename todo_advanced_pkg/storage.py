"""SQLite-backed storage with simple migration and concurrency protections.

Design goals implemented simply but safely:
- WAL mode for concurrent readers/writers
- Single-file SQLite with transactional operations
- Small migration/version table to allow schema evolution
- Connection factory that is safe for multithreaded use
"""
from __future__ import annotations
import sqlite3
import threading
from pathlib import Path
from typing import Optional, Iterable, Tuple, Any
import json
from datetime import datetime

DB_FILE = Path(__file__).parent.parent / "todo.db"
_SCHEMA_VERSION = 1

_conn_local = threading.local()
_write_lock = threading.RLock()


def _get_conn() -> sqlite3.Connection:
    """Return a thread-local connection. Recreate the connection if the
    configured DB file changed (important for tests that monkeypatch
    `DB_FILE`). Caller should not close the connection.
    """
    cur_path = str(DB_FILE)
    conn = getattr(_conn_local, "conn", None)
    existing_path = getattr(_conn_local, "db_path", None)
    if conn is None or existing_path != cur_path:
        # close previous connection if any
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass
        conn = sqlite3.connect(cur_path, timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # PRAGMAs for durability and concurrency
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        _conn_local.conn = conn
        _conn_local.db_path = cur_path
    return conn


def initialize() -> None:
    """Create DB and run migrations (idempotent)."""
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    conn = _get_conn()
    with _write_lock, conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                k TEXT PRIMARY KEY,
                v TEXT NOT NULL
            )
            """
        )
        cur = conn.execute("SELECT v FROM metadata WHERE k='schema_version'")
        row = cur.fetchone()
        if row is None:
            conn.execute("INSERT INTO metadata(k,v) VALUES(?,?)", ("schema_version", str(_SCHEMA_VERSION)))
        else:
            # future migrations would be applied here based on int(row['v'])
            pass

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                aliases TEXT NOT NULL DEFAULT '[]',
                color TEXT,
                description TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                usage_count INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS task_tags (
                task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
                PRIMARY KEY (task_id, tag_id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tag_cooccurrence (
                tag_a INTEGER NOT NULL,
                tag_b INTEGER NOT NULL,
                weight INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (tag_a, tag_b),
                FOREIGN KEY(tag_a) REFERENCES tags(id) ON DELETE CASCADE,
                FOREIGN KEY(tag_b) REFERENCES tags(id) ON DELETE CASCADE
            )
            """
        )


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


# High-level helpers -------------------------------------------------------

def add_task(task: str, tags: Optional[Iterable[str]] = None) -> int:
    tags = list(tags or [])
    conn = _get_conn()
    with _write_lock, conn:
        cur = conn.execute(
            "INSERT INTO tasks(task, completed, created_at, updated_at) VALUES (?,0,?,?)",
            (task, _now_iso(), _now_iso()),
        )
        task_id = cur.lastrowid
        for t in tags:
            tag_id = _ensure_tag_row(conn, t)
            conn.execute("INSERT OR IGNORE INTO task_tags(task_id, tag_id) VALUES (?,?)", (task_id, tag_id))
            conn.execute("UPDATE tags SET usage_count = usage_count + 1, updated_at=? WHERE id=?", (_now_iso(), tag_id))
        if tags:
            _update_cooccurrence(conn, tags)
    return task_id


def list_tasks(limit: Optional[int] = None) -> list:
    conn = _get_conn()
    q = "SELECT * FROM tasks ORDER BY id ASC"
    if limit:
        q += f" LIMIT {int(limit)}"
    cur = conn.execute(q)
    rows = cur.fetchall()
    out = []
    for r in rows:
        tags = [row[0] for row in conn.execute(
            "SELECT name FROM tags t JOIN task_tags tt ON tt.tag_id=t.id WHERE tt.task_id=? ORDER BY t.name ASC", (r["id"],)
        ).fetchall()]
        out.append({
            "id": r["id"],
            "task": r["task"],
            "completed": bool(r["completed"]),
            "tags": tags,
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        })
    return out


def _ensure_tag_row(conn: sqlite3.Connection, name: str) -> int:
    cur = conn.execute("SELECT id, aliases FROM tags WHERE name=?", (name,))
    row = cur.fetchone()
    if row:
        return row["id"]
    now = _now_iso()
    cur = conn.execute(
        "INSERT INTO tags(name, aliases, created_at, updated_at, usage_count) VALUES(?,?,?,?,0)",
        (name, json.dumps([]), now, now),
    )
    return cur.lastrowid


def _get_tag_row_by_name(conn: sqlite3.Connection, name: str):
    cur = conn.execute("SELECT * FROM tags WHERE name=?", (name,))
    return cur.fetchone()


def _update_cooccurrence(conn: sqlite3.Connection, tags: Iterable[str]) -> None:
    tags = sorted(set(tags))
    ids = []
    for t in tags:
        row = _get_tag_row_by_name(conn, t)
        if row:
            ids.append(row["id"])
    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            # increment both (a,b) and (b,a) to make lookups simple
            conn.execute(
                "INSERT INTO tag_cooccurrence(tag_a, tag_b, weight) VALUES(?,?,1) ON CONFLICT(tag_a,tag_b) DO UPDATE SET weight=weight+1",
                (a, b),
            )
            conn.execute(
                "INSERT INTO tag_cooccurrence(tag_a, tag_b, weight) VALUES(?,?,1) ON CONFLICT(tag_a,tag_b) DO UPDATE SET weight=weight+1",
                (b, a),
            )


def add_tag_to_task_by_index(index: int, tag: str) -> None:
    conn = _get_conn()
    with _write_lock, conn:
        cur = conn.execute("SELECT id FROM tasks ORDER BY id ASC LIMIT 1 OFFSET ?", (index,))
        row = cur.fetchone()
        if not row:
            raise IndexError("task index out of range")
        task_id = row["id"]
        tag_id = _ensure_tag_row(conn, tag)
        conn.execute("INSERT OR IGNORE INTO task_tags(task_id, tag_id) VALUES(?,?)", (task_id, tag_id))
        conn.execute("UPDATE tags SET usage_count = usage_count + 1, updated_at=? WHERE id=?", (_now_iso(), tag_id))


def remove_tag_from_task_by_index(index: int, tag: str) -> None:
    conn = _get_conn()
    with _write_lock, conn:
        cur = conn.execute("SELECT id FROM tasks ORDER BY id ASC LIMIT 1 OFFSET ?", (index,))
        row = cur.fetchone()
        if not row:
            raise IndexError("task index out of range")
        task_id = row["id"]
        cur = conn.execute("SELECT id FROM tags WHERE name=?", (tag,))
        trow = cur.fetchone()
        if not trow:
            return
        tag_id = trow["id"]
        conn.execute("DELETE FROM task_tags WHERE task_id=? AND tag_id=?", (task_id, tag_id))


def complete_task_by_index(index: int) -> None:
    conn = _get_conn()
    with _write_lock, conn:
        cur = conn.execute("SELECT id FROM tasks ORDER BY id ASC LIMIT 1 OFFSET ?", (index,))
        row = cur.fetchone()
        if not row:
            raise IndexError("task index out of range")
        conn.execute("UPDATE tasks SET completed=1, updated_at=? WHERE id=?", (_now_iso(), row["id"]))


def tag_stats() -> dict:
    conn = _get_conn()
    cur = conn.execute("SELECT name, usage_count FROM tags ORDER BY name ASC")
    return {r["name"]: r["usage_count"] for r in cur.fetchall()}


def all_tags() -> list:
    conn = _get_conn()
    cur = conn.execute("SELECT name FROM tags ORDER BY name ASC")
    return [r["name"] for r in cur.fetchall()]


# Lightweight query helper used by the query engine (kept small here)

def search_tasks_by_keywords(keywords: Iterable[str], limit: Optional[int] = None) -> list:
    conn = _get_conn()
    clauses = []
    params: list[Any] = []
    for kw in keywords:
        clauses.append("task LIKE ?")
        params.append(f"%{kw}%")
    q = "SELECT * FROM tasks"
    if clauses:
        q += " WHERE " + " AND ".join(clauses)
    q += " ORDER BY id ASC"
    if limit:
        q += f" LIMIT {int(limit)}"
    cur = conn.execute(q, params)
    return [dict(r) for r in cur.fetchall()]


# Ensure DB is ready on import
initialize()
