"""
todo_advanced.py - Advanced TODO system with persistent tags, query language, etc.
Preserves the original API for backward compatibility.
"""

from typing import List, Optional, Dict
import threading
from storage import Storage
from models import Task, Tag
from tags import TagManager
from query import QueryParser
from plugins import PluginManager


class AdvancedTodoSystem:
    def __init__(self):
        self.storage = Storage()
        self.tag_manager = TagManager(self.storage)
        self.query_parser = QueryParser()
        self.plugin_manager = PluginManager()
        self.plugin_manager.load_plugins('nonexistent_plugins')
        self.tasks: List[Task] = []
        self.next_id = 1
        self.lock = threading.RLock()
        self._load_tasks()

    def _load_tasks(self):
        self.tasks = self.storage.load_tasks()
        if self.tasks:
            self.next_id = max(t.id for t in self.tasks) + 1

    def add_todo(self, task: str, tags: Optional[List[str]] = None) -> None:
        with self.lock:
            if tags is None:
                tags = []
            resolved_tags = [self.tag_manager.resolve_alias(t) for t in tags]
            new_task = Task(id=self.next_id, task=task, tags=resolved_tags)
            self.tasks.append(new_task)
            self.storage.save_task(new_task)
            self.next_id += 1
            # Update tag usage and co-occurrences
            for tag in resolved_tags:
                self.tag_manager.increment_usage(tag)
                for other in resolved_tags:
                    if other != tag:
                        self.tag_manager.add_co_occurrence(tag, other)
            self.plugin_manager.trigger_hook('on_task_added', new_task)

    def list_todos(self) -> List[Dict]:
        with self.lock:
            # Convert to dict for compatibility
            return [
                {
                    "task": t.task,
                    "completed": t.completed,
                    "tags": t.tags,
                }
                for t in self.tasks
            ]

    def filter_by_tags(self, tags: List[str], match_all: bool = False) -> List[Dict]:
        with self.lock:
            resolved_tags = [self.tag_manager.resolve_alias(t) for t in tags]
            filtered = []
            for task in self.tasks:
                task_tags = set(task.tags)
                if match_all:
                    if all(t in task_tags for t in resolved_tags):
                        filtered.append(task)
                else:
                    if any(t in task_tags for t in resolved_tags):
                        filtered.append(task)
            return [
                {
                    "task": t.task,
                    "completed": t.completed,
                    "tags": t.tags,
                }
                for t in filtered
            ]

    def add_tag_to_task(self, index: int, tag: str) -> None:
        with self.lock:
            if 0 <= index < len(self.tasks):
                resolved_tag = self.tag_manager.resolve_alias(tag)
                self.tasks[index].add_tag(resolved_tag)
                self.storage.save_task(self.tasks[index])
                self.tag_manager.increment_usage(resolved_tag)
                # Update co-occurrences
                for other in self.tasks[index].tags:
                    if other != resolved_tag:
                        self.tag_manager.add_co_occurrence(resolved_tag, other)

    def remove_tag_from_task(self, index: int, tag: str) -> None:
        with self.lock:
            if 0 <= index < len(self.tasks):
                resolved_tag = self.tag_manager.resolve_alias(tag)
                self.tasks[index].remove_tag(resolved_tag)
                self.storage.save_task(self.tasks[index])

    def show_tag_stats(self) -> Dict[str, int]:
        with self.lock:
            return self.tag_manager.get_tag_stats()

    def list_all_tags(self) -> List[str]:
        with self.lock:
            return self.tag_manager.list_all_tags()

    def complete_task(self, index: int) -> None:
        with self.lock:
            if 0 <= index < len(self.tasks):
                self.tasks[index].complete()
                self.storage.save_task(self.tasks[index])
                self.plugin_manager.trigger_hook('on_task_completed', self.tasks[index])

    # Additional methods for advanced features
    def query_tasks(self, query: str) -> List[Dict]:
        with self.lock:
            filtered = self.query_parser.evaluate(query, self.tasks)
            return [
                {
                    "task": t.task,
                    "completed": t.completed,
                    "tags": t.tags,
                }
                for t in filtered
            ]

    def suggest_tags(self, keyword: str) -> List[str]:
        return self.tag_manager.suggest_tags(keyword)


# Global instance for API
_system = AdvancedTodoSystem()


# Public API (same as original)
def add_todo(task: str, tags: Optional[List[str]] = None) -> None:
    _system.add_todo(task, tags)


def list_todos() -> List[Dict]:
    return _system.list_todos()


def filter_by_tags(tags: List[str], match_all: bool = False) -> List[Dict]:
    return _system.filter_by_tags(tags, match_all)


def add_tag_to_task(index: int, tag: str) -> None:
    _system.add_tag_to_task(index, tag)


def remove_tag_from_task(index: int, tag: str) -> None:
    _system.remove_tag_from_task(index, tag)


def show_tag_stats() -> Dict[str, int]:
    return _system.show_tag_stats()


def list_all_tags() -> List[str]:
    return _system.list_all_tags()


def complete_task(index: int) -> None:
    _system.complete_task(index)


# Additional advanced API
def query_tasks(query: str) -> List[Dict]:
    return _system.query_tasks(query)


def suggest_tags(keyword: str) -> List[str]:
    return _system.suggest_tags(keyword)