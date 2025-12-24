Feature specification for the Advanced Tag System

- Persistent storage: SQLite with WAL; schema contains tasks, tags, task_tags,
  tag_cooccurrence.
- Tag metadata: aliases (JSON), color, description, usage_count, timestamps.
- Query DSL: boolean tag expressions with parentheses and NOT.
- Plugin hooks: on_task_added, on_tag_added, on_task_completed (auto-discovered
  under `todo_plugins`).
- Backward compatibility: `todo_advanced.py` preserves the `todo_original.py`
  public API.
