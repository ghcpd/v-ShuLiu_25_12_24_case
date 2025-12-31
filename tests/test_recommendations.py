"""Tests for tag recommendation engine."""

import unittest
import tempfile
import os

from todo_advanced.recommendations import TagRecommender
from todo_advanced.tags import TagManager
from todo_advanced.storage import SQLiteBackend, reset_storage


class TestTagRecommender(unittest.TestCase):
    """Test tag recommendation."""

    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.db_path = self.temp_db.name
        self.temp_db.close()

        self.storage = SQLiteBackend(self.db_path)
        self.tag_manager = TagManager()
        self.tag_manager.storage = self.storage
        
        self.recommender = TagRecommender()
        self.recommender.tag_manager = self.tag_manager
        self.recommender.storage = self.storage

    def tearDown(self):
        """Clean up."""
        reset_storage()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_recommend_by_keyword(self):
        """Test keyword-based recommendations."""
        self.tag_manager.create_tag("work")
        self.tag_manager.create_tag("working")
        self.tag_manager.create_tag("personal")

        recommendations = self.recommender.recommend_by_keyword("work")

        self.assertGreater(len(recommendations), 0)
        # Should include work and working
        tags = [tag for tag, _ in recommendations]
        self.assertIn("work", tags)

    def test_recommend_with_threshold(self):
        """Test keyword recommendations with threshold."""
        self.tag_manager.create_tag("project")
        self.tag_manager.create_tag("personal")

        recommendations = self.recommender.recommend_by_keyword("proj", threshold=0.7)

        self.assertGreater(len(recommendations), 0)

    def test_recommend_by_task_content(self):
        """Test task content-based recommendations."""
        self.tag_manager.create_tag("work")
        self.tag_manager.create_tag("email")
        self.tag_manager.create_tag("personal")

        task_text = "Send work email to boss"
        recommendations = self.recommender.recommend_by_task_content(task_text)

        self.assertGreater(len(recommendations), 0)

    def test_recommend_excludes_existing(self):
        """Test that recommendations exclude existing tags."""
        self.tag_manager.create_tag("work")
        self.tag_manager.create_tag("urgent")
        self.tag_manager.create_tag("personal")

        recommendations = self.recommender.recommend_by_task_content(
            "Work task", existing_tags=["work"]
        )

        tags = [tag for tag, _ in recommendations]
        self.assertNotIn("work", tags)

    def test_recommend_by_cooccurrence(self):
        """Test co-occurrence based recommendations."""
        self.tag_manager.create_tag("work")
        self.tag_manager.create_tag("urgent")
        self.tag_manager.create_tag("meeting")

        # Record co-occurrences
        self.tag_manager.record_cooccurrence("work", "urgent")
        self.tag_manager.record_cooccurrence("work", "urgent")
        self.tag_manager.record_cooccurrence("work", "meeting")

        recommendations = self.recommender.recommend_by_cooccurrence(["work"])

        self.assertGreater(len(recommendations), 0)
        tags = [tag for tag, _ in recommendations]
        self.assertIn("urgent", tags)


if __name__ == "__main__":
    unittest.main()
