"""High-level API that composes storage, tags, query, and plugins."""
from typing import List, Dict, Optional
from .storage import Storage
from .tags import recommend_tags_by_text
from .query import run_query
from . import plugins
import os


class AdvancedTodo:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join(os.getcwd(), "todo_advanced.db")
        self._storage = Storage(db_path)

    # Basic task/tag API (keeps `todo_original.py` behaviour)
    def add_task(self, task: str, tags: List[str]) -> None:
        tid = self._storage.add_task(task, tags)
        for tag in tags:
            plugins.run_hook("on_tag_added", tag)
        plugins.run_hook("on_task_added", {"id": tid, "task": task, "tags": tags})

    def list_tasks(self) -> List[Dict]:
        return self._storage.list_tasks()

    def filter_tasks_by_tags(self, tags: List[str], match_all: bool = False) -> List[Dict]:
        return self._storage.find_tasks_by_tag_names(tags, match_all=match_all)

    def add_tag_to_task(self, index: int, tag: str) -> None:
        tasks = self.list_tasks()
        if index < 0 or index >= len(tasks):
            raise IndexError("task index out of range")
        task_id = tasks[index]["id"]
        self._storage.add_tag_to_task(task_id, tag)
        plugins.run_hook("on_tag_added", tag)

    def remove_tag_from_task(self, index: int, tag: str) -> None:
        tasks = self.list_tasks()
        if index < 0 or index >= len(tasks):
            raise IndexError("task index out of range")
        task_id = tasks[index]["id"]
        self._storage.remove_tag_from_task(task_id, tag)

    def tag_stats(self) -> Dict[str, int]:
        return self._storage.tag_stats()

    def list_tags(self) -> List[str]:
        return [t["name"] for t in self._storage.list_tags()]

    def complete_task(self, index: int) -> None:
        tasks = self.list_tasks()
        if index < 0 or index >= len(tasks):
            raise IndexError("task index out of range")
        task_id = tasks[index]["id"]
        self._storage.complete_task(task_id)
        plugins.run_hook("on_task_completed", {"id": task_id})

    # Advanced
    def query(self, expression: str) -> List[Dict]:
        tasks = self.list_tasks()
        return run_query(expression, tasks)

    def recommend_tags(self, text: str, top_k: int = 5) -> List[str]:
        tags = self._storage.list_tags()
        return recommend_tags_by_text(tags, text, top_k=top_k)
