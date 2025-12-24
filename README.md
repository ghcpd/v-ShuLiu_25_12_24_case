# Advanced TODO System

A modern, persistent, modular, and concurrency-safe tag system that extends the minimal `todo_original.py` while maintaining complete backward compatibility.

## Features

### ✅ Persistent Storage
- SQLite-based persistent storage with automatic schema management
- Thread-safe concurrent access with locking
- Automatic schema evolution and recovery

### 🏷️ Structured Tags
- Tag metadata including description, color, and aliases
- Tag usage counters and co-occurrence tracking
- Tag relationship graph for recommendations

### 🔍 Advanced Querying
- Mini DSL (Domain-Specific Language) for complex queries
- Expressions: `tag:work AND (urgent OR personal) AND NOT archived`
- Support for parentheses, AND/OR/NOT operators

### 💡 Smart Recommendations
- Tag suggestions based on keyword similarity
- Co-occurrence history analysis
- Usage frequency weighting

### 🔒 Concurrency Safe
- Thread-safe operations with RLock protection
- Safe concurrent read/write operations
- No data corruption under stress

### 🔌 Plugin System
- Hook-based extensibility
- Auto-discovery of plugin modules
- Hooks: `on_task_added`, `on_tag_added`, `on_task_completed`, etc.

### 📊 CLI Enhancements
- Colorized output with ANSI colors
- Fuzzy search support
- Paging for long results
- Task and tag display helpers

### ⚡ Performance
- Load 10,000 tasks in < 80 ms
- Typical queries in < 50 ms
- Tag relationship updates in < 10 ms

## Installation

### Prerequisites
- Python 3.8 or higher
- No external package dependencies required (SQLite is built-in)

### Quick Start

```bash
# Clone or download the repository
cd /path/to/todo-advanced

# Run the one-click test script
# On Windows:
.\run_tests.ps1

# On Linux/macOS:
./run_tests.sh
```

## Usage

### Basic API (Backward Compatible)

```python
from todo_advanced import api

# Add a task with tags
api.add_todo("Buy milk", ["shopping", "urgent"])

# List all tasks
tasks = api.list_todos()

# Filter by tags
work_tasks = api.filter_by_tags(["work"], match_all=False)  # OR logic
urgent_work = api.filter_by_tags(["work", "urgent"], match_all=True)  # AND logic

# Tag management
api.add_tag_to_task(0, "new-tag")
api.remove_tag_from_task(0, "old-tag")

# Statistics
stats = api.show_tag_stats()
all_tags = api.list_all_tags()

# Mark task as completed
api.complete_task(0)
```

### Advanced Features

```python
from todo_advanced import api

# Create structured tags with metadata
tag = api.add_structured_tag(
    "work",
    description="Work-related tasks",
    color="#FF0000",
    aliases=["office", "job"]
)

# List tags with full metadata
tags = api.list_tags_with_metadata()

# DSL queries
results = api.query_tasks_dsl("tag:work AND urgent AND NOT completed:true")
results = api.query_tasks_dsl("(tag:work OR tag:personal) AND NOT archived")

# Get tag recommendations for a task
recommendations = api.recommend_tags(
    "Fix critical bug in authentication",
    existing_tags=["urgent"],
    limit=5
)

# Get related tags (by co-occurrence)
related = api.get_related_tags("work", limit=5)

# Get specific tag metadata
metadata = api.get_tag_metadata("work")
```

### Plugin System

```python
from todo_advanced.plugins import get_plugin_manager

pm = get_plugin_manager()

# Subscribe to hooks
def on_task_added(task_id, task, tags):
    print(f"Task added: {task} with tags {tags}")

pm.subscribe("on_task_added", on_task_added)

# Available hooks:
# - on_task_added(task_id, task, tags)
# - on_task_updated(task_id, task, tags)
# - on_task_completed(task_id, task)
# - on_tag_added(tag_name, tag_metadata)
# - on_query_executed(query, result_count)
```

### CLI Utilities

```python
from todo_advanced.cli import (
    print_colored, 
    print_task, 
    print_tasks,
    fuzzy_search,
    Colors
)

# Colored output
print_colored("Success!", Colors.GREEN)

# Task display
task = {"task": "Buy milk", "tags": ["shopping"], "completed": False}
print_task(task, index=0)

# Fuzzy search
results = fuzzy_search("wrk", ["work", "personal", "urgent"])
# Returns: ["work"]
```

## Architecture

```
todo_advanced/
├── __init__.py              # Package exports
├── api.py                   # Main API wrapper (backward compatible)
├── storage.py               # SQLite persistence layer
├── tags.py                  # Structured tag model
├── query_dsl.py             # DSL parser and executor
├── recommendations.py       # Tag recommendation engine
├── plugins.py               # Plugin system
├── validation.py            # Input validation
├── caching.py               # Performance caching
├── metrics.py               # Metrics collection
└── cli.py                   # CLI utilities

tests/
├── test_advanced_todo.py    # Comprehensive test suite
└── __init__.py

perf_test.py                # Performance benchmarks
run_tests.sh                # Unix/Linux/macOS test runner
run_tests.ps1               # Windows PowerShell test runner
requirements.txt            # Core dependencies
requirements-dev.txt        # Development dependencies
```

## Test Coverage

The test suite includes:

### Unit Tests
- **Backward Compatibility**: All original API functions work identically
- **Persistence**: Data survives restarts and reconnections
- **Concurrency**: 50+ concurrent operations without corruption
- **Query DSL**: Complex expressions with multiple operators
- **Tag Metadata**: Creation, updates, aliases, and relationships
- **Validation**: Input validation and error handling
- **Plugins**: Hook subscription and multi-handler support

### Performance Tests
- Load 10,000 tasks < 80 ms ✅
- Typical queries < 50 ms ✅
- Tag relationship updates < 10 ms ✅
- Concurrent write safety ✅

### Stress Tests
- 500+ concurrent task additions
- 100+ simultaneous read/write operations
- Large result set handling

## Performance Targets

| Operation | Target | Status |
|-----------|--------|--------|
| Load 10,000 tasks | < 80 ms | ✅ Pass |
| Typical query | < 50 ms | ✅ Pass |
| Tag relationship update | < 10 ms | ✅ Pass |
| Concurrent write safety | Zero corruption | ✅ Pass |

## Database Schema

### Tasks Table
```
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task TEXT NOT NULL,
    completed BOOLEAN DEFAULT 0,
    tags TEXT DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
```

### Tag Metadata Table
```
CREATE TABLE tag_metadata (
    name TEXT PRIMARY KEY,
    description TEXT DEFAULT '',
    color TEXT DEFAULT '#CCCCCC',
    aliases TEXT DEFAULT '[]',
    usage_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
```

### Tag Co-occurrence Table
```
CREATE TABLE tag_cooccurrence (
    tag1 TEXT NOT NULL,
    tag2 TEXT NOT NULL,
    count INTEGER DEFAULT 1,
    PRIMARY KEY (tag1, tag2)
)
```

## Query DSL Syntax

### Basic Syntax
```
tag:name              # Task has tag "name"
completed:true        # Task is completed
task:keyword          # Task description contains keyword
```

### Operators
```
AND                   # Both conditions must be true
OR                    # Either condition must be true
NOT                   # Negates the following expression
()                    # Groups expressions
```

### Examples
```
tag:work              # Tasks with "work" tag
tag:urgent OR tag:important  # Tasks with either tag
tag:work AND NOT completed:true  # Incomplete work tasks
(tag:work OR tag:personal) AND tag:urgent  # Complex query
```

## Running Tests

### One-Click Test
```bash
# Windows
.\run_tests.ps1

# Linux/macOS
./run_tests.sh
```

### Manual Test Execution
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/ -v

# Run performance tests
python perf_test.py
```

## Backward Compatibility

All functions from `todo_original.py` are fully compatible:

```python
# These work exactly as before:
add_todo(task, tags)
list_todos()
filter_by_tags(tags, match_all)
add_tag_to_task(index, tag)
remove_tag_from_task(index, tag)
show_tag_stats()
list_all_tags()
complete_task(index)
```

## Extensibility

### Creating Plugins

```python
# plugins/auto_tag_plugin.py
def register_hooks(plugin_manager):
    plugin_manager.subscribe("on_task_added", auto_tag_on_add)

def auto_tag_on_add(task_id, task, tags):
    """Auto-tag based on keywords."""
    if "bug" in task.lower():
        # Could auto-add "urgent" or other tags
        pass
```

### Custom Query Operators

Extend the QueryDSL parser in `query_dsl.py` to support custom operators like:
- `priority:high`
- `due_date:tomorrow`
- `assigned_to:john`

## Limitations & Future Enhancements

### Current Limitations
- Single-user (no user accounts)
- No encryption at rest
- In-process caching only (no distributed cache)

### Planned Enhancements
- Full-text search support
- Due date tracking and reminders
- Task dependencies and ordering
- Multi-user support with permissions
- REST API interface
- Web UI dashboard

## Contributing

1. Add tests for any new features
2. Ensure all tests pass before submitting
3. Update documentation for API changes
4. Follow existing code style and conventions

## License

This project is provided as-is for educational and development purposes.

## Support

For issues or questions:
1. Check the test suite for usage examples
2. Review the docstrings in the source code
3. Run performance tests to verify your environment

---

**Advanced TODO System v1.0.0**
*A modern tag system for todo management*
