"""
Structured tag model with metadata, aliases, and relationships.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from .storage import get_storage


@dataclass
class Tag:
    """Structured tag with metadata."""
    name: str
    description: str = ""
    color: str = "#CCCCCC"
    aliases: List[str] = field(default_factory=list)
    usage_count: int = 0
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict:
        """Convert tag to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "aliases": self.aliases,
            "usage_count": self.usage_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class TagManager:
    """Manages structured tags with metadata and relationships."""

    def __init__(self):
        self.storage = get_storage()

    def create_tag(
        self,
        name: str,
        description: str = "",
        color: str = "#CCCCCC",
        aliases: Optional[List[str]] = None,
    ) -> Tag:
        """Create a new structured tag."""
        if aliases is None:
            aliases = []

        tag = Tag(
            name=name,
            description=description,
            color=color,
            aliases=aliases,
        )

        self.storage.add_tag_metadata(
            name,
            description=description,
            color=color,
            aliases=aliases,
            usage_count=0,
        )

        return tag

    def get_tag(self, name: str) -> Optional[Tag]:
        """Retrieve tag metadata."""
        data = self.storage.get_tag_metadata(name)
        if data:
            return Tag(**data)
        return None

    def list_tags(self) -> List[Tag]:
        """List all tags."""
        tags_data = self.storage.list_all_tags_metadata()
        return [Tag(**data) for data in tags_data]

    def update_tag(self, name: str, **updates) -> bool:
        """Update tag metadata."""
        existing = self.storage.get_tag_metadata(name)
        if not existing:
            return False

        updated_data = {**existing, **updates}
        updated_data["updated_at"] = datetime.utcnow().isoformat()

        self.storage.add_tag_metadata(name, **updated_data)
        return True

    def add_alias(self, tag_name: str, alias: str) -> bool:
        """Add an alias to a tag."""
        tag = self.get_tag(tag_name)
        if not tag:
            return False

        if alias not in tag.aliases:
            tag.aliases.append(alias)
            return self.update_tag(tag_name, aliases=tag.aliases)
        return True

    def record_usage(self, tag_name: str) -> None:
        """Increment usage count for a tag."""
        self.storage.record_tag_usage(tag_name)

    def record_cooccurrence(self, tag1: str, tag2: str) -> None:
        """Record that two tags co-occurred in a task."""
        self.storage.record_tag_cooccurrence(tag1, tag2)

    def get_cooccurrence(self, tag1: str, tag2: str) -> int:
        """Get the co-occurrence count between two tags."""
        return self.storage.get_tag_cooccurrence(tag1, tag2)

    def get_related_tags(self, tag_name: str, limit: int = 5) -> List[tuple]:
        """
        Get tags that frequently co-occur with the given tag.
        Returns list of (tag_name, cooccurrence_count) tuples.
        """
        all_tags = [t.name for t in self.list_tags() if t.name != tag_name]
        relationships = [
            (other_tag, self.get_cooccurrence(tag_name, other_tag))
            for other_tag in all_tags
        ]
        # Sort by co-occurrence count descending
        relationships.sort(key=lambda x: x[1], reverse=True)
        return relationships[:limit]


# Global tag manager instance
_tag_manager: Optional[TagManager] = None


def get_tag_manager() -> TagManager:
    """Get or create global tag manager."""
    global _tag_manager
    if _tag_manager is None:
        _tag_manager = TagManager()
    return _tag_manager


def reset_tag_manager() -> None:
    """Reset tag manager (for testing)."""
    global _tag_manager
    _tag_manager = None
