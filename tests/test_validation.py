"""Tests for validation utilities."""

import unittest

from todo_advanced.validation import Validator


class TestValidator(unittest.TestCase):
    """Test validation utilities."""

    def test_validate_task_valid(self):
        """Test validating valid task."""
        valid, error = Validator.validate_task("Buy groceries")
        self.assertTrue(valid)
        self.assertIsNone(error)

    def test_validate_task_empty(self):
        """Test validating empty task."""
        valid, error = Validator.validate_task("")
        self.assertFalse(valid)
        self.assertIsNotNone(error)

    def test_validate_task_too_long(self):
        """Test validating task that is too long."""
        long_task = "a" * 1001
        valid, error = Validator.validate_task(long_task)
        self.assertFalse(valid)

    def test_validate_tag_name_valid(self):
        """Test validating valid tag name."""
        valid, error = Validator.validate_tag_name("work")
        self.assertTrue(valid)

    def test_validate_tag_name_with_dash(self):
        """Test validating tag name with dash."""
        valid, error = Validator.validate_tag_name("work-related")
        self.assertTrue(valid)

    def test_validate_tag_name_with_underscore(self):
        """Test validating tag name with underscore."""
        valid, error = Validator.validate_tag_name("work_related")
        self.assertTrue(valid)

    def test_validate_tag_name_invalid_characters(self):
        """Test validating tag with invalid characters."""
        valid, error = Validator.validate_tag_name("work@related")
        self.assertFalse(valid)

    def test_validate_tag_name_too_long(self):
        """Test validating tag name that is too long."""
        long_tag = "a" * 51
        valid, error = Validator.validate_tag_name(long_tag)
        self.assertFalse(valid)

    def test_validate_color_valid(self):
        """Test validating valid color."""
        valid, error = Validator.validate_color("#FF0000")
        self.assertTrue(valid)

    def test_validate_color_invalid_format(self):
        """Test validating invalid color format."""
        valid, error = Validator.validate_color("FF0000")
        self.assertFalse(valid)

    def test_validate_tags_list_valid(self):
        """Test validating valid tags list."""
        valid, error = Validator.validate_tags_list(["work", "urgent"])
        self.assertTrue(valid)

    def test_validate_tags_list_not_list(self):
        """Test validating non-list tags."""
        valid, error = Validator.validate_tags_list("work")
        self.assertFalse(valid)

    def test_validate_tags_list_invalid_tag(self):
        """Test validating list with invalid tag."""
        valid, error = Validator.validate_tags_list(["work", "bad@tag"])
        self.assertFalse(valid)


if __name__ == "__main__":
    unittest.main()
