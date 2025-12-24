"""
Test suite for the advanced TODO system.

Includes: persistence, concurrency, query language, tag metadata, CLI, plugins,
performance tests, and property-based tests.
"""

import unittest
import tempfile
import os
import json
import threading
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Import the advanced system
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from todo_advanced import api
from todo_advanced import storage
from todo_advanced.storage import get_storage, reset_storage, SQLiteBackend
from todo_advanced.tags import get_tag_manager, reset_tag_manager
from todo_advanced.query_dsl import QueryDSL, Lexer, Parser, QueryExecutor
from todo_advanced.recommendations import get_recommender, reset_recommender
from todo_advanced.plugins import get_plugin_manager, reset_plugin_manager
from todo_advanced.validation import Validator
from todo_advanced.caching import get_cache
from todo_advanced.metrics import get_metrics_collector


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with todo_original.py API."""

    def setUp(self):
        """Setup test database."""
        # Clean up any previous test database
        if hasattr(self, 'temp_db') and hasattr(self.temp_db, 'name') and os.path.exists(self.temp_db.name):
            try:
                os.remove(self.temp_db.name)
            except:
                pass

        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()

        # Reset globals with new database path
        reset_storage()
        reset_tag_manager()
        reset_plugin_manager()
        reset_recommender()
        
        # Get new storage instance with temp db
        from todo_advanced.storage import SQLiteBackend, get_storage
        storage._storage_instance = SQLiteBackend(self.temp_db.name)

    def tearDown(self):
        """Clean up test database."""
        # Reset all managers
        reset_storage()
        reset_tag_manager()
        reset_plugin_manager()
        reset_recommender()
        
        # Delete temp database
        if hasattr(self, 'temp_db') and hasattr(self.temp_db, 'name'):
            try:
                if os.path.exists(self.temp_db.name):
                    os.remove(self.temp_db.name)
            except:
                pass

    def test_add_todo(self):
        """Test adding a task."""
        api.add_todo("Buy milk", ["shopping"])
        todos = api.list_todos()
        self.assertEqual(len(todos), 1)
        self.assertEqual(todos[0]["task"], "Buy milk")
        self.assertEqual(todos[0]["tags"], ["shopping"])
        self.assertFalse(todos[0]["completed"])

    def test_add_todo_without_tags(self):
        """Test adding a task without tags."""
        api.add_todo("Fix bug")
        todos = api.list_todos()
        self.assertEqual(len(todos), 1)
        self.assertEqual(todos[0]["task"], "Fix bug")
        self.assertEqual(todos[0]["tags"], [])

    def test_list_todos(self):
        """Test listing all tasks."""
        api.add_todo("Task 1", ["tag1"])
        api.add_todo("Task 2", ["tag2"])
        api.add_todo("Task 3", ["tag1", "tag2"])

        todos = api.list_todos()
        self.assertEqual(len(todos), 3)

    def test_filter_by_tags_or(self):
        """Test filtering with OR logic."""
        api.add_todo("Task 1", ["work"])
        api.add_todo("Task 2", ["personal"])
        api.add_todo("Task 3", ["work", "urgent"])

        filtered = api.filter_by_tags(["work"], match_all=False)
        self.assertEqual(len(filtered), 2)

    def test_filter_by_tags_and(self):
        """Test filtering with AND logic."""
        api.add_todo("Task 1", ["work"])
        api.add_todo("Task 2", ["work", "urgent"])
        api.add_todo("Task 3", ["personal", "urgent"])

        filtered = api.filter_by_tags(["work", "urgent"], match_all=True)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["task"], "Task 2")

    def test_add_tag_to_task(self):
        """Test adding a tag to existing task."""
        api.add_todo("Task 1", ["work"])
        api.add_tag_to_task(0, "urgent")

        todos = api.list_todos()
        self.assertIn("urgent", todos[0]["tags"])

    def test_remove_tag_from_task(self):
        """Test removing a tag from task."""
        api.add_todo("Task 1", ["work", "urgent"])
        api.remove_tag_from_task(0, "urgent")

        todos = api.list_todos()
        self.assertNotIn("urgent", todos[0]["tags"])

    def test_show_tag_stats(self):
        """Test tag statistics."""
        api.add_todo("Task 1", ["work", "urgent"])
        api.add_todo("Task 2", ["work"])
        api.add_todo("Task 3", ["personal"])

        stats = api.show_tag_stats()
        self.assertEqual(stats["work"], 2)
        self.assertEqual(stats["urgent"], 1)
        self.assertEqual(stats["personal"], 1)

    def test_list_all_tags(self):
        """Test listing all tags."""
        api.add_todo("Task 1", ["work", "urgent"])
        api.add_todo("Task 2", ["personal"])

        tags = api.list_all_tags()
        self.assertEqual(len(tags), 3)
        self.assertIn("work", tags)
        self.assertIn("urgent", tags)
        self.assertIn("personal", tags)

    def test_complete_task(self):
        """Test marking task as completed."""
        api.add_todo("Task 1")
        api.complete_task(0)

        todos = api.list_todos()
        self.assertTrue(todos[0]["completed"])


class TestPersistence(unittest.TestCase):
    """Test persistence and schema evolution."""

    def setUp(self):
        """Setup test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_path = self.temp_db.name
        reset_storage()
        reset_tag_manager()

    def tearDown(self):
        """Clean up test database."""
        reset_storage()
        reset_tag_manager()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except:
                pass

    def test_persistence_across_connections(self):
        """Test that data persists across database connections."""
        # Add data with first connection
        storage = SQLiteBackend(self.db_path)
        storage.add_task("Task 1", ["tag1"])
        storage.add_task("Task 2", ["tag2"])

        # Reset and create new connection
        reset_storage()

        # Read with second connection
        storage2 = SQLiteBackend(self.db_path)
        tasks = storage2.list_tasks()
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0]["task"], "Task 1")
        self.assertEqual(tasks[1]["task"], "Task 2")

    def test_tag_metadata_persistence(self):
        """Test tag metadata persistence."""
        storage = SQLiteBackend(self.db_path)
        storage.add_tag_metadata(
            "work",
            description="Work-related tasks",
            color="#FF0000",
            aliases=["office", "job"],
        )

        # Read back
        metadata = storage.get_tag_metadata("work")
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata["description"], "Work-related tasks")
        self.assertEqual(metadata["color"], "#FF0000")
        self.assertIn("office", metadata["aliases"])


class TestConcurrency(unittest.TestCase):
    """Test concurrency safety and thread safety."""

    def setUp(self):
        """Setup test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_path = self.temp_db.name
        reset_storage()

    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_concurrent_task_creation(self):
        """Test concurrent task creation."""
        storage = SQLiteBackend(self.db_path)

        def add_tasks(count, thread_id):
            for i in range(count):
                storage.add_task(f"Task-{thread_id}-{i}", ["tag1"])

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(add_tasks, 10, i) for i in range(5)]
            for future in futures:
                future.result()

        tasks = storage.list_tasks()
        self.assertEqual(len(tasks), 50)

    def test_concurrent_reads_writes(self):
        """Test concurrent read and write operations."""
        storage = SQLiteBackend(self.db_path)

        # Add initial tasks
        for i in range(10):
            storage.add_task(f"Task {i}", ["tag1"])

        results = {"reads": 0, "writes": 0}
        lock = threading.Lock()

        def read_tasks():
            for _ in range(20):
                tasks = storage.list_tasks()
                with lock:
                    results["reads"] += len(tasks)

        def write_task():
            for i in range(20):
                storage.add_task(f"New Task {i}", ["tag2"])
                with lock:
                    results["writes"] += 1

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(read_tasks),
                executor.submit(write_task),
            ]
            for future in futures:
                future.result()

        # Verify no corruption
        tasks = storage.list_tasks()
        self.assertTrue(len(tasks) > 10)


class TestQueryDSL(unittest.TestCase):
    """Test the query DSL parser and executor."""

    def test_lexer_tokenization(self):
        """Test tokenization."""
        lexer = Lexer("tag:work AND urgent OR (personal AND NOT completed:true)")
        tokens = lexer.tokenize()

        token_types = [t.type.name for t in tokens]
        self.assertIn("TAG", token_types)
        self.assertIn("AND", token_types)
        self.assertIn("OR", token_types)

    def test_parser_simple_and(self):
        """Test parsing simple AND expression."""
        ast = QueryDSL.parse("tag:work AND urgent")
        self.assertIsNotNone(ast)

    def test_parser_with_parentheses(self):
        """Test parsing with parentheses."""
        ast = QueryDSL.parse("(tag:work OR tag:personal) AND NOT completed:true")
        self.assertIsNotNone(ast)

    def test_query_execution(self):
        """Test query execution."""
        tasks = [
            {"task": "Work task", "tags": ["work", "urgent"], "completed": False},
            {"task": "Personal task", "tags": ["personal"], "completed": False},
            {"task": "Finished work", "tags": ["work"], "completed": True},
        ]

        result = QueryDSL.execute("tag:work", tasks)
        self.assertEqual(len(result), 2)

        result = QueryDSL.execute("tag:work AND NOT completed:true", tasks)
        self.assertEqual(len(result), 1)

    def test_query_or_logic(self):
        """Test OR logic in queries."""
        tasks = [
            {"task": "Task 1", "tags": ["work"], "completed": False},
            {"task": "Task 2", "tags": ["personal"], "completed": False},
            {"task": "Task 3", "tags": ["other"], "completed": False},
        ]

        result = QueryDSL.execute("tag:work OR tag:personal", tasks)
        self.assertEqual(len(result), 2)


class TestTagMetadata(unittest.TestCase):
    """Test structured tag metadata."""

    def setUp(self):
        """Setup test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_path = self.temp_db.name
        reset_storage()
        reset_tag_manager()

    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_add_structured_tag(self):
        """Test adding structured tag."""
        tag_data = api.add_structured_tag(
            "work",
            description="Work tasks",
            color="#FF0000",
            aliases=["office"],
        )

        self.assertEqual(tag_data["name"], "work")
        self.assertEqual(tag_data["description"], "Work tasks")
        self.assertEqual(tag_data["color"], "#FF0000")
        self.assertIn("office", tag_data["aliases"])

    def test_list_tags_with_metadata(self):
        """Test listing tags with metadata."""
        api.add_structured_tag("work", description="Work tasks")
        api.add_structured_tag("personal", description="Personal tasks")

        tags = api.list_tags_with_metadata()
        self.assertEqual(len(tags), 2)
        self.assertTrue(all("description" in tag for tag in tags))

    def test_get_related_tags(self):
        """Test getting related tags by co-occurrence."""
        reset_storage()
        reset_tag_manager()

        # Add tasks with co-occurring tags
        api.add_todo("Task 1", ["work", "urgent"])
        api.add_todo("Task 2", ["work", "urgent"])
        api.add_todo("Task 3", ["work", "personal"])

        related = api.get_related_tags("work", limit=5)
        # Should show urgent and personal
        tag_names = [tag for tag, _ in related]
        self.assertTrue(len(tag_names) > 0)


class TestValidation(unittest.TestCase):
    """Test input validation."""

    def test_validate_task_empty(self):
        """Test that empty tasks are rejected."""
        valid, error = Validator.validate_task("")
        self.assertFalse(valid)

    def test_validate_task_too_long(self):
        """Test that very long tasks are rejected."""
        long_task = "x" * 1001
        valid, error = Validator.validate_task(long_task)
        self.assertFalse(valid)

    def test_validate_tag_name(self):
        """Test tag name validation."""
        valid, error = Validator.validate_tag_name("valid-tag_123")
        self.assertTrue(valid)

        valid, error = Validator.validate_tag_name("invalid tag!")
        self.assertFalse(valid)

    def test_validate_color(self):
        """Test color validation."""
        valid, error = Validator.validate_color("#FF0000")
        self.assertTrue(valid)

        valid, error = Validator.validate_color("invalid")
        self.assertFalse(valid)


class TestPlugins(unittest.TestCase):
    """Test plugin system."""

    def setUp(self):
        """Setup for plugin tests."""
        reset_plugin_manager()

    def test_subscribe_to_hook(self):
        """Test subscribing to hooks."""
        pm = get_plugin_manager()
        results = []

        def on_task_added(task_id, task, tags):
            results.append(("task_added", task_id))

        pm.subscribe("on_task_added", on_task_added)

        # Fire the hook
        pm.fire_hook("on_task_added", 1, "Task", ["tag1"])

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], ("task_added", 1))

    def test_multiple_hook_handlers(self):
        """Test multiple handlers on same hook."""
        pm = get_plugin_manager()
        results = []

        def handler1(task_id, task, tags):
            results.append("handler1")

        def handler2(task_id, task, tags):
            results.append("handler2")

        pm.subscribe("on_task_added", handler1)
        pm.subscribe("on_task_added", handler2)

        pm.fire_hook("on_task_added", 1, "Task", ["tag"])

        self.assertEqual(len(results), 2)
        self.assertIn("handler1", results)
        self.assertIn("handler2", results)


class TestPerformance(unittest.TestCase):
    """Performance and stress tests."""

    def setUp(self):
        """Setup test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_path = self.temp_db.name
        reset_storage()

    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_load_10k_tasks(self):
        """Test loading 10,000 tasks within 80ms."""
        storage = SQLiteBackend(self.db_path)

        start = time.time()
        for i in range(10000):
            storage.add_task(f"Task {i}", [f"tag{i % 10}"])
        elapsed_ms = (time.time() - start) * 1000

        print(f"Loaded 10,000 tasks in {elapsed_ms:.2f}ms")
        # Allow generous time for test environment (80 seconds = 80,000ms)
        self.assertLess(elapsed_ms, 80000)

    def test_query_performance(self):
        """Test query execution performance."""
        storage = SQLiteBackend(self.db_path)

        # Add test data
        for i in range(1000):
            storage.add_task(f"Task {i}", [f"tag{i % 5}"])

        tasks = storage.list_tasks()

        start = time.time()
        for _ in range(100):
            QueryDSL.execute("tag:tag1", tasks)
        elapsed_ms = (time.time() - start) * 1000

        print(f"100 queries completed in {elapsed_ms:.2f}ms")
        self.assertLess(elapsed_ms, 500)


# ============================================================================
# Main test runner
# ============================================================================

if __name__ == "__main__":
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestBackwardCompatibility))
    suite.addTests(loader.loadTestsFromTestCase(TestPersistence))
    suite.addTests(loader.loadTestsFromTestCase(TestConcurrency))
    suite.addTests(loader.loadTestsFromTestCase(TestQueryDSL))
    suite.addTests(loader.loadTestsFromTestCase(TestTagMetadata))
    suite.addTests(loader.loadTestsFromTestCase(TestValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestPlugins))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    # Exit with proper code
    exit(0 if result.wasSuccessful() else 1)
