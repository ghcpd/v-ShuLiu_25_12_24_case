"""Tests for public API."""

import unittest
import tempfile
import os

# We need to set up the storage before importing api
import todo_advanced.storage as storage_module

from todo_advanced import (
    add_todo,
    list_todos,
    filter_by_tags,
    add_tag_to_task,
    remove_tag_from_task,
    show_tag_stats,
    list_all_tags,
    complete_task,
    add_structured_tag,
    list_tags_with_metadata,
    query_tasks_dsl,
    recommend_tags,
)


class TestBackwardCompatibleAPI(unittest.TestCase):
    """Test original API compatibility."""

    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.db_path = self.temp_db.name
        self.temp_db.close()
        storage_module.reset_storage()
        storage_module.get_storage(self.db_path)

    def tearDown(self):
        """Clean up."""
        storage_module.reset_storage()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_add_todo(self):
        """Test adding a todo."""
        add_todo("Buy milk", tags=["shopping"])
        tasks = list_todos()

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["task"], "Buy milk")

    def test_list_todos(self):
        """Test listing todos."""
        add_todo("Task 1")
        add_todo("Task 2", tags=["work"])

        tasks = list_todos()
        self.assertEqual(len(tasks), 2)

    def test_filter_by_tags_any(self):
        """Test filtering by tags (any match)."""
        add_todo("Work task", tags=["work"])
        add_todo("Shopping", tags=["shopping"])
        add_todo("Work + Shopping", tags=["work", "shopping"])

        filtered = filter_by_tags(["work"], match_all=False)
        self.assertEqual(len(filtered), 2)

    def test_filter_by_tags_all(self):
        """Test filtering by tags (all match)."""
        add_todo("Work + Shopping", tags=["work", "shopping"])
        add_todo("Just work", tags=["work"])

        filtered = filter_by_tags(["work", "shopping"], match_all=True)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["task"], "Work + Shopping")

    def test_add_tag_to_task(self):
        """Test adding tag to existing task."""
        add_todo("Task", tags=["tag1"])
        add_tag_to_task(0, "tag2")

        tasks = list_todos()
        self.assertIn("tag2", tasks[0]["tags"])

    def test_remove_tag_from_task(self):
        """Test removing tag from task."""
        add_todo("Task", tags=["tag1", "tag2"])
        remove_tag_from_task(0, "tag1")

        tasks = list_todos()
        self.assertNotIn("tag1", tasks[0]["tags"])
        self.assertIn("tag2", tasks[0]["tags"])

    def test_show_tag_stats(self):
        """Test tag statistics."""
        add_todo("Task 1", tags=["work"])
        add_todo("Task 2", tags=["work", "urgent"])

        stats = show_tag_stats()
        self.assertEqual(stats["work"], 2)
        self.assertEqual(stats["urgent"], 1)

    def test_list_all_tags(self):
        """Test listing all tags."""
        add_todo("Task 1", tags=["work"])
        add_todo("Task 2", tags=["personal"])

        tags = list_all_tags()
        self.assertIn("work", tags)
        self.assertIn("personal", tags)

    def test_complete_task(self):
        """Test marking task as complete."""
        add_todo("Task")
        complete_task(0)

        tasks = list_todos()
        self.assertTrue(tasks[0]["completed"])


class TestNewAPI(unittest.TestCase):
    """Test new advanced API."""

    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.db_path = self.temp_db.name
        self.temp_db.close()
        storage_module.reset_storage()
        storage_module.get_storage(self.db_path)

    def tearDown(self):
        """Clean up."""
        storage_module.reset_storage()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_add_structured_tag(self):
        """Test adding structured tag."""
        add_structured_tag(
            "work",
            description="Work tasks",
            color="#FF0000",
            aliases=["job", "office"]
        )

        tags = list_tags_with_metadata()
        names = [t["name"] for t in tags]
        self.assertIn("work", names)

    def test_list_tags_with_metadata(self):
        """Test listing tags with metadata."""
        add_structured_tag("work", description="Work tasks")
        tags = list_tags_with_metadata()

        self.assertGreater(len(tags), 0)
        self.assertIn("description", tags[0])

    def test_query_tasks_dsl(self):
        """Test DSL query."""
        add_todo("Work task", tags=["work"])
        add_todo("Personal task", tags=["personal"])

        results = query_tasks_dsl("work")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["task"], "Work task")

    def test_recommend_tags(self):
        """Test tag recommendations."""
        add_structured_tag("work")
        add_structured_tag("email")

        recommendations = recommend_tags("Send work email")
        self.assertGreater(len(recommendations), 0)


if __name__ == "__main__":
    unittest.main()
