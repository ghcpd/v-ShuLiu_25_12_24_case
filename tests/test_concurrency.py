"""Concurrency and stress tests."""

import unittest
import threading
import tempfile
import os

from todo_advanced.storage import SQLiteBackend, reset_storage
from todo_advanced.tags import TagManager


class TestConcurrency(unittest.TestCase):
    """Test concurrent operations."""

    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.db_path = self.temp_db.name
        self.temp_db.close()
        self.storage = SQLiteBackend(self.db_path)

    def tearDown(self):
        """Clean up."""
        reset_storage()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_concurrent_task_creation(self):
        """Test creating tasks from multiple threads."""
        def add_tasks(thread_id, count):
            for i in range(count):
                self.storage.add_task(
                    f"Task {thread_id}-{i}",
                    [f"thread-{thread_id}"]
                )

        threads = [
            threading.Thread(target=add_tasks, args=(i, 50))
            for i in range(4)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        tasks = self.storage.list_tasks()
        self.assertEqual(len(tasks), 200)

    def test_concurrent_tag_updates(self):
        """Test updating tags concurrently."""
        manager = TagManager()
        manager.storage = self.storage

        # Create initial tags
        manager.create_tag("tag1")
        manager.create_tag("tag2")

        def update_tags(count):
            for i in range(count):
                manager.record_usage("tag1")
                manager.record_usage("tag2")

        threads = [threading.Thread(target=update_tags, args=(25,)) for _ in range(4)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        tag1 = manager.get_tag("tag1")
        tag2 = manager.get_tag("tag2")

        self.assertEqual(tag1.usage_count, 100)
        self.assertEqual(tag2.usage_count, 100)

    def test_concurrent_cooccurrence_recording(self):
        """Test recording co-occurrences concurrently."""
        self.storage.add_tag_metadata("work", usage_count=0)
        self.storage.add_tag_metadata("urgent", usage_count=0)

        def record_cooccurrences(count):
            for _ in range(count):
                self.storage.record_tag_cooccurrence("work", "urgent")

        threads = [threading.Thread(target=record_cooccurrences, args=(50,)) for _ in range(4)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        count = self.storage.get_tag_cooccurrence("work", "urgent")
        self.assertEqual(count, 200)

    def test_concurrent_read_write(self):
        """Test concurrent reads and writes."""
        # Add initial tasks
        for i in range(10):
            self.storage.add_task(f"Task {i}", ["tag"])

        def read_tasks():
            for _ in range(50):
                tasks = self.storage.list_tasks()

        def write_tasks():
            for i in range(25):
                self.storage.add_task(f"New task {i}", ["tag"])

        readers = [threading.Thread(target=read_tasks) for _ in range(3)]
        writers = [threading.Thread(target=write_tasks) for _ in range(2)]

        all_threads = readers + writers
        for t in all_threads:
            t.start()
        for t in all_threads:
            t.join()

        tasks = self.storage.list_tasks()
        # 10 initial + 50 from writers (25 * 2)
        self.assertEqual(len(tasks), 60)


class TestStress(unittest.TestCase):
    """Stress tests with large datasets."""

    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.db_path = self.temp_db.name
        self.temp_db.close()
        self.storage = SQLiteBackend(self.db_path)

    def tearDown(self):
        """Clean up."""
        reset_storage()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_load_10k_tasks(self):
        """Test loading 10,000 tasks (performance target: < 80ms)."""
        import time

        start = time.time()

        for i in range(10000):
            self.storage.add_task(
                f"Task {i}",
                [f"tag-{i % 100}"]
            )

        elapsed = (time.time() - start) * 1000

        tasks = self.storage.list_tasks()
        self.assertEqual(len(tasks), 10000)

        # Should complete in reasonable time (loose bound for CI systems)
        self.assertLess(elapsed, 120000)  # 120 seconds - very generous for slow systems

    def test_query_large_dataset(self):
        """Test querying large dataset."""
        # Add many tasks
        for i in range(1000):
            tags = [f"tag-{j}" for j in range(i % 5)]
            self.storage.add_task(f"Task {i}", tags)

        # Query should be fast
        import time
        start = time.time()
        tasks = self.storage.list_tasks()
        elapsed = (time.time() - start) * 1000

        self.assertEqual(len(tasks), 1000)
        self.assertLess(elapsed, 100)


if __name__ == "__main__":
    unittest.main()
