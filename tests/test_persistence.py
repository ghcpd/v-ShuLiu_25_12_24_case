"""
tests/test_persistence.py - Persistence tests.
"""

import os
import tempfile
from todo_advanced import AdvancedTodoSystem
from storage import Storage


def test_persistence():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        db_path = f.name
    try:
        system = AdvancedTodoSystem()
        system.storage = Storage(db_path)  # New storage with path
        system.add_todo("Persistent task", ["test"])
        del system
        # Reload
        system2 = AdvancedTodoSystem()
        system2.storage = Storage(db_path)
        system2._load_tasks()  # Reload tasks from new db
        tasks = system2.list_todos()
        assert len(tasks) == 1
        assert tasks[0]["task"] == "Persistent task"
    finally:
        os.unlink(db_path)