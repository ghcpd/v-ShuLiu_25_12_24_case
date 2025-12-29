"""
models.py - Data models for the advanced TODO system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Set


@dataclass
class Tag:
    name: str
    aliases: Set[str] = field(default_factory=set)
    color: str = "#FFFFFF"
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    co_occurrences: Dict[str, int] = field(default_factory=dict)

    def add_alias(self, alias: str):
        self.aliases.add(alias)
        self.updated_at = datetime.now()

    def remove_alias(self, alias: str):
        self.aliases.discard(alias)
        self.updated_at = datetime.now()

    def increment_usage(self):
        self.usage_count += 1
        self.updated_at = datetime.now()

    def add_co_occurrence(self, other_tag: str):
        self.co_occurrences[other_tag] = self.co_occurrences.get(other_tag, 0) + 1


@dataclass
class Task:
    id: int
    task: str
    completed: bool = False
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_tag(self, tag: str):
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()

    def remove_tag(self, tag: str):
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()

    def complete(self):
        self.completed = True
        self.updated_at = datetime.now()