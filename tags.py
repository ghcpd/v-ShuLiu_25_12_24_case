"""
tags.py - Tag management, recommendations, and metadata.
"""

from typing import List, Dict, Set
from difflib import SequenceMatcher
from datetime import datetime
from models import Tag
from storage import Storage


class TagManager:
    def __init__(self, storage: Storage):
        self.storage = storage
        self.tags: Dict[str, Tag] = {}
        self._load_tags()

    def _load_tags(self):
        self.tags = self.storage.load_tags()

    def get_or_create_tag(self, name: str) -> Tag:
        if name not in self.tags:
            tag = Tag(name=name)
            self.tags[name] = tag
            self.storage.save_tag(tag)
        return self.tags[name]

    def add_alias(self, tag_name: str, alias: str):
        tag = self.get_or_create_tag(tag_name)
        tag.add_alias(alias)
        self.storage.save_tag(tag)

    def remove_alias(self, tag_name: str, alias: str):
        if tag_name in self.tags:
            self.tags[tag_name].remove_alias(alias)
            self.storage.save_tag(self.tags[tag_name])

    def set_color(self, tag_name: str, color: str):
        tag = self.get_or_create_tag(tag_name)
        tag.color = color
        tag.updated_at = datetime.now()
        self.storage.save_tag(tag)

    def set_description(self, tag_name: str, desc: str):
        tag = self.get_or_create_tag(tag_name)
        tag.description = desc
        tag.updated_at = datetime.now()
        self.storage.save_tag(tag)

    def increment_usage(self, tag_name: str):
        tag = self.get_or_create_tag(tag_name)
        tag.increment_usage()
        self.storage.save_tag(tag)

    def add_co_occurrence(self, tag1: str, tag2: str):
        if tag1 != tag2:
            t1 = self.get_or_create_tag(tag1)
            t2 = self.get_or_create_tag(tag2)
            t1.add_co_occurrence(tag2)
            t2.add_co_occurrence(tag1)
            self.storage.save_tag(t1)
            self.storage.save_tag(t2)

    def resolve_alias(self, alias: str) -> str:
        for tag in self.tags.values():
            if alias in tag.aliases or alias == tag.name:
                return tag.name
        return alias  # If not found, return as is

    def suggest_tags(self, keyword: str, limit: int = 5) -> List[str]:
        suggestions = []
        for tag_name, tag in self.tags.items():
            similarity = SequenceMatcher(None, keyword.lower(), tag_name.lower()).ratio()
            desc_sim = SequenceMatcher(None, keyword.lower(), tag.description.lower()).ratio() if tag.description else 0
            max_sim = max(similarity, desc_sim)
            if max_sim > 0.5:  # Threshold
                suggestions.append((tag_name, max_sim, tag.usage_count))
        # Sort by similarity then usage
        suggestions.sort(key=lambda x: (-x[1], -x[2]))
        return [s[0] for s in suggestions[:limit]]

    def get_related_tags(self, tag_name: str, limit: int = 5) -> List[str]:
        if tag_name not in self.tags:
            return []
        co = self.tags[tag_name].co_occurrences
        related = sorted(co.items(), key=lambda x: -x[1])
        return [r[0] for r in related[:limit]]

    def list_all_tags(self) -> List[str]:
        return sorted(self.tags.keys())

    def get_tag_stats(self) -> Dict[str, int]:
        return {name: tag.usage_count for name, tag in self.tags.items()}