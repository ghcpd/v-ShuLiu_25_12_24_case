"""Tests for persistent storage layer."""

import unittest
import tempfile
import os
import json
from pathlib import Path
from datetime import datetime

from todo_advanced.storage import SQLiteBackend, TaskRecord, TagRecord, reset_storage, get_storage


class TestSQLiteBackend(unittest.TestCase):
    """Test SQLite backend storage."""

    def setUp(self):
        """Create temporary database for testing."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.db_path = self.temp_db.name
        self.temp_db.close()
        self.backend = SQLiteBackend(self.db_path)

    def tearDown(self):
        """Clean up temporary database."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
        reset_storage()

    def test_add_and_list_tasks(self):
        """Test adding and listing tasks."""
        task_id = self.backend.add_task("Buy groceries", ["shopping", "urgent"])
        self.assertIsInstance(task_id, int)

        tasks = self.backend.list_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["task"], "Buy groceries")
        self.assertEqual(tasks[0]["tags"], ["shopping", "urgent"])

    def test_get_task(self):
        """Test retrieving a specific task."""
        task_id = self.backend.add_task("Test task", ["test"])
        task = self.backend.get_task(task_id)

        self.assertIsNotNone(task)
        self.assertEqual(task["task"], "Test task")

    def test_update_task(self):
        """Test updating task."""
        task_id = self.backend.add_task("Original task", ["tag1"])
        updated = self.backend.update_task(task_id, task="Updated task", tags=["tag2", "tag3"])

        self.assertTrue(updated)
        task = self.backend.get_task(task_id)
        self.assertEqual(task["task"], "Updated task")
        self.assertEqual(task["tags"], ["tag2", "tag3"])

    def test_complete_task(self):
        """Test marking task as completed."""
        task_id = self.backend.add_task("Do something", ["work"])
        updated = self.backend.update_task(task_id, completed=True)

        self.assertTrue(updated)
        task = self.backend.get_task(task_id)
        self.assertTrue(task["completed"])

    def test_delete_task(self):
        """Test deleting a task."""
        task_id = self.backend.add_task("Delete me", ["temp"])
        deleted = self.backend.delete_task(task_id)

        self.assertTrue(deleted)
        task = self.backend.get_task(task_id)
        self.assertIsNone(task)

    def test_tag_metadata(self):
        """Test tag metadata operations."""
        self.backend.add_tag_metadata("work", description="Work-related tasks", color="#FF0000")
        metadata = self.backend.get_tag_metadata("work")

        self.assertIsNotNone(metadata)
        self.assertEqual(metadata["description"], "Work-related tasks")
        self.assertEqual(metadata["color"], "#FF0000")

    def test_tag_usage_tracking(self):
        """Test tag usage count."""
        self.backend.add_tag_metadata("important", usage_count=0)
        self.backend.record_tag_usage("important")
        self.backend.record_tag_usage("important")

        metadata = self.backend.get_tag_metadata("important")
        self.assertEqual(metadata["usage_count"], 2)

    def test_tag_cooccurrence(self):
        """Test tag co-occurrence tracking."""
        self.backend.add_tag_metadata("work", usage_count=0)
        self.backend.add_tag_metadata("urgent", usage_count=0)

        self.backend.record_tag_cooccurrence("work", "urgent")
        self.backend.record_tag_cooccurrence("work", "urgent")

        count = self.backend.get_tag_cooccurrence("work", "urgent")
        self.assertEqual(count, 2)

    def test_concurrent_access(self):
        """Test thread safety."""
        import threading

        def add_tasks(count):
            for i in range(count):
                self.backend.add_task(f"Task {i}", ["tag1"])

        threads = [threading.Thread(target=add_tasks, args=(10,)) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        tasks = self.backend.list_tasks()
        self.assertEqual(len(tasks), 30)


class TestStorageGlobal(unittest.TestCase):
    """Test global storage instance."""

    def tearDown(self):
        """Clean up."""
        reset_storage()
        if os.path.exists("test_todo.db"):
            os.unlink("test_todo.db")

    def test_get_storage_singleton(self):
        """Test that get_storage returns singleton."""
        storage1 = get_storage("test_todo.db")
        storage2 = get_storage("test_todo.db")

        self.assertIs(storage1, storage2)


if __name__ == "__main__":
    unittest.main()
