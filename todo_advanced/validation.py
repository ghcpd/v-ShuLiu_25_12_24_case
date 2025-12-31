"""
Validation utilities for tasks and tags.
"""

import re
from typing import List, Tuple, Optional


class Validator:
    """Validates tasks and tags."""

    @staticmethod
    def validate_task(task: str) -> Tuple[bool, Optional[str]]:
        """Validate a task string."""
        if not task:
            return False, "Task cannot be empty"
        if len(task) > 1000:
            return False, "Task exceeds 1000 characters"
        return True, None

    @staticmethod
    def validate_tag_name(name: str) -> Tuple[bool, Optional[str]]:
        """Validate a tag name."""
        if not name:
            return False, "Tag name cannot be empty"
        if not re.match(r"^[a-zA-Z0-9_-]+$", name):
            return False, "Tag name can only contain alphanumeric, dash, and underscore"
        if len(name) > 50:
            return False, "Tag name exceeds 50 characters"
        return True, None

    @staticmethod
    def validate_color(color: str) -> Tuple[bool, Optional[str]]:
        """Validate a color hex value."""
        if not re.match(r"^#[0-9A-Fa-f]{6}$", color):
            return False, "Color must be a valid hex code (e.g., #CCCCCC)"
        return True, None

    @staticmethod
    def validate_tags_list(tags: List[str]) -> Tuple[bool, Optional[str]]:
        """Validate a list of tags."""
        if not isinstance(tags, list):
            return False, "Tags must be a list"
        for tag in tags:
            valid, error = Validator.validate_tag_name(tag)
            if not valid:
                return False, f"Invalid tag '{tag}': {error}"
        return True, None
