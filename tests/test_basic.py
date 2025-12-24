"""
tests/test_basic.py - Basic functionality tests.
"""

import tempfile
import os
from todo_advanced import AdvancedTodoSystem
from storage import Storage


def test_add_and_list():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        db_path = f.name
    try:
        system = AdvancedTodoSystem()
        system.storage = Storage(db_path)
        system._load_tasks()
        initial = len(system.list_todos())
        system.add_todo("Test task", ["work"])
        assert len(system.list_todos()) == initial + 1
    finally:
        os.unlink(db_path)


def test_filter():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        db_path = f.name
    try:
        system = AdvancedTodoSystem()
        system.storage = Storage(db_path)
        system._load_tasks()
        system.add_todo("Urgent task", ["urgent", "work"])
        system.add_todo("Personal task", ["personal"])
        filtered = system.filter_by_tags(["work"])
        assert len(filtered) >= 1
        assert any("work" in t["tags"] for t in filtered)
    finally:
        os.unlink(db_path)


def test_tag_stats():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        db_path = f.name
    try:
        system = AdvancedTodoSystem()
        system.storage = Storage(db_path)
        system._load_tasks()
        stats = system.show_tag_stats()
        assert isinstance(stats, dict)
    finally:
        os.unlink(db_path)


def test_list_tags():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        db_path = f.name
    try:
        system = AdvancedTodoSystem()
        system.storage = Storage(db_path)
        system._load_tasks()
        tags = system.list_all_tags()
        assert isinstance(tags, list)
    finally:
        os.unlink(db_path)