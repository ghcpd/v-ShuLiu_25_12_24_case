"""Tests for tag management."""

import unittest
import tempfile
import os

from todo_advanced.tags import TagManager, Tag, get_tag_manager, reset_tag_manager
from todo_advanced.storage import SQLiteBackend, reset_storage


class TestTag(unittest.TestCase):
    """Test Tag dataclass."""

    def test_tag_creation(self):
        """Test creating a tag."""
        tag = Tag(
            name="work",
            description="Work tasks",
            color="#FF0000",
            aliases=["office", "job"]
        )

        self.assertEqual(tag.name, "work")
        self.assertEqual(tag.description, "Work tasks")
        self.assertEqual(tag.color, "#FF0000")
        self.assertIn("office", tag.aliases)

    def test_tag_to_dict(self):
        """Test converting tag to dictionary."""
        tag = Tag(name="test", description="Test tag")
        tag_dict = tag.to_dict()

        self.assertEqual(tag_dict["name"], "test")
        self.assertEqual(tag_dict["description"], "Test tag")
        self.assertIn("created_at", tag_dict)


class TestTagManager(unittest.TestCase):
    """Test tag management functionality."""

    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # Use custom storage for this test
        self.storage = SQLiteBackend(self.db_path)
        self.manager = TagManager()
        self.manager.storage = self.storage

    def tearDown(self):
        """Clean up."""
        reset_tag_manager()
        reset_storage()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_create_tag(self):
        """Test creating a tag."""
        tag = self.manager.create_tag(
            "project",
            description="Project tasks",
            color="#0000FF"
        )

        self.assertEqual(tag.name, "project")
        self.assertEqual(tag.description, "Project tasks")

    def test_get_tag(self):
        """Test retrieving a tag."""
        self.manager.create_tag("urgent", description="Urgent tasks")
        tag = self.manager.get_tag("urgent")

        self.assertIsNotNone(tag)
        self.assertEqual(tag.description, "Urgent tasks")

    def test_list_tags(self):
        """Test listing all tags."""
        self.manager.create_tag("work")
        self.manager.create_tag("personal")
        self.manager.create_tag("shopping")

        tags = self.manager.list_tags()
        names = [t.name for t in tags]

        self.assertEqual(len(tags), 3)
        self.assertIn("work", names)

    def test_add_alias(self):
        """Test adding alias to tag."""
        self.manager.create_tag("work")
        success = self.manager.add_alias("work", "job")

        self.assertTrue(success)
        tag = self.manager.get_tag("work")
        self.assertIn("job", tag.aliases)

    def test_record_usage(self):
        """Test recording tag usage."""
        self.manager.create_tag("important")
        self.manager.record_usage("important")
        self.manager.record_usage("important")

        tag = self.manager.get_tag("important")
        self.assertEqual(tag.usage_count, 2)

    def test_record_cooccurrence(self):
        """Test recording tag co-occurrence."""
        self.manager.create_tag("work")
        self.manager.create_tag("urgent")

        self.manager.record_cooccurrence("work", "urgent")
        self.manager.record_cooccurrence("work", "urgent")

        count = self.manager.get_cooccurrence("work", "urgent")
        self.assertEqual(count, 2)

    def test_get_related_tags(self):
        """Test getting related tags."""
        self.manager.create_tag("work")
        self.manager.create_tag("urgent")
        self.manager.create_tag("meeting")

        self.manager.record_cooccurrence("work", "urgent")
        self.manager.record_cooccurrence("work", "urgent")
        self.manager.record_cooccurrence("work", "meeting")

        related = self.manager.get_related_tags("work")
        names = [name for name, _ in related]

        self.assertGreater(len(related), 0)
        self.assertIn("urgent", names)


if __name__ == "__main__":
    unittest.main()
