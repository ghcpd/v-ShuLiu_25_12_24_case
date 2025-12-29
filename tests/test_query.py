"""
tests/test_query.py - Query language tests.
"""

import tempfile
import os
from todo_advanced import AdvancedTodoSystem
from storage import Storage


def test_query():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        db_path = f.name
    try:
        system = AdvancedTodoSystem()
        system.storage = Storage(db_path)
        system._load_tasks()  # Reload from new db
        system.add_todo("Work task", ["work", "urgent"])
        system.add_todo("Home task", ["personal"])
        results = system.query_tasks("tag:work")
        work_tasks = [r for r in results if "work" in r["tags"]]
        assert len(work_tasks) == 1
        assert work_tasks[0]["task"] == "Work task"
    finally:
        os.unlink(db_path)