"""Lightweight domain models and converters to/from the legacy dict-shape."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import json


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass
class Tag:
    id: int
    name: str
    aliases: List[str] = field(default_factory=list)
    color: Optional[str] = None
    description: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    usage_count: int = 0

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "aliases": list(self.aliases),
            "color": self.color,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "usage_count": self.usage_count,
        }


@dataclass
class Task:
    id: int
    task: str
    completed: bool = False
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_legacy_dict(self):
        # preserve the original minimal shape for backward compatibility
        return {
            "task": self.task,
            "completed": bool(self.completed),
            "tags": list(self.tags),
        }
