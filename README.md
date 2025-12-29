# Advanced TODO Tag System

This project extends the minimal `todo_original.py` with a complete, modern Tag System that is persistent, modular, concurrency-safe, and extensible.

## Features

- **Persistent Storage**: Uses SQLite for tasks and tags.
- **Structured Tags**: Aliases, colors, descriptions, timestamps, usage counters, co-occurrence graphs.
- **Tag Recommendations**: Suggests tags based on similarity and history.
- **Query Language**: DSL like `tag:work AND (urgent OR personal) AND NOT archived`.
- **Concurrency Safety**: Thread-safe operations.
- **Modular Architecture**: Separate modules for storage, tags, queries, plugins, etc.
- **Plugin System**: Hooks for custom behaviors.
- **Enhanced CLI**: Fuzzy search, colors, paging, DSL queries.
- **Backward Compatibility**: Same API as `todo_original.py`.

## Installation

```bash
pip install -r requirements.txt
```

For development:
```bash
pip install -r requirements-dev.txt
```

## Usage

Import `todo_advanced` instead of `todo_original` for advanced features.

```python
from todo_advanced import add_todo, list_todos, query_tasks

add_todo("Finish project", ["work", "urgent"])
tasks = query_tasks("tag:work AND NOT completed")
```

## CLI

```bash
python -m cli add "New task" --tags work urgent
python -m cli list --query "tag:work"
python -m cli list --fuzzy "project"
```

## Testing

Run `run_tests.ps1` (Windows) or `run_tests.sh` (Unix) for one-click testing.

Or manually:
```bash
pytest tests/
python perf_test.py
```

## Performance Targets

- Load 10,000 tasks: < 80 ms
- Typical queries: < 50 ms
- Tag updates: < 10 ms
- No corruption under concurrent writes