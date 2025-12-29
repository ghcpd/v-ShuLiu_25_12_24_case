"""Tag model and helper utilities.

This module defines a `Tag` dataclass-like structure and functions to manage aliases,
colors, descriptions and co-occurrence updates. It's storage-agnostic and will call
into storage layer for persistence.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict


@dataclass
class Tag:
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    aliases: List[str] = field(default_factory=list)
    usage_count: int = 0
    created_at: float | None = None
    updated_at: float | None = None


# Placeholder functions; real persistence happens via storage module

def normalize_tag_name(name: str) -> str:
    return name.strip().lower()


def suggest_tags_by_keyword(keyword: str, tags: List[Tag]) -> List[Tag]:
    # Very simple suggestion: substring match + sort by usage_count
    keyword = keyword.lower()
    matches = [t for t in tags if keyword in t.name.lower() or (t.description and keyword in t.description.lower())]
    matches.sort(key=lambda t: -t.usage_count)
    return matches
