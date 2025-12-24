# Advanced Tag System - Feature Specification

## Overview

This document describes the complete feature set for the Advanced Tag System for the TODO application. The system is designed to be a modern, persistent, modular, concurrency-safe extension to the minimal `todo_original.py` while maintaining 100% backward compatibility.

## 1. Architecture & Design

### 1.1 Modular Structure
The system is built as a Python package with clear separation of concerns:

- **api.py** - Public API (backward compatible + new features)
- **storage.py** - Persistent storage layer (SQLite)
- **tags.py** - Structured tag model and management
- **query_dsl.py** - Query language parser and executor
- **recommendations.py** - Tag suggestion engine
- **plugins.py** - Plugin system and hooks
- **validation.py** - Input validation
- **caching.py** - Performance caching
- **metrics.py** - Metrics and monitoring
- **cli.py** - CLI utilities and helpers

### 1.2 Design Principles

1. **Backward Compatibility**: All original API functions work identically
2. **Thread-Safe**: Uses RLock for concurrent access protection
3. **Persistent**: SQLite with automatic schema management
4. **Extensible**: Plugin hooks for custom behaviors
5. **Performance-Focused**: Optimized for 10K+ task workloads
6. **Type-Hinted**: Full Python type annotations for IDE support

## 2. Core Features

### 2.1 Persistent Storage

#### Database Choice: SQLite
- Built-in, no external dependencies
- ACID compliance for data integrity
- Thread-safe with proper locking
- Simple file-based storage
- Automatic schema creation and evolution

#### Schema
Three main tables:
1. **tasks** - Store task descriptions, completion status, and tags
2. **tag_metadata** - Store tag properties (color, description, aliases, etc.)
3. **tag_cooccurrence** - Store tag relationship frequencies

#### Concurrency
- RLock-protected access in SQLiteBackend
- Timeout-based connection handling (5 second timeout)
- Safe for concurrent reads and writes
- No transaction conflicts or deadlocks

### 2.2 Structured Tag Model

Each tag can have:
- **Name** (required, alphanumeric + dash/underscore)
- **Description** (optional)
- **Color** (hex code for CLI display, e.g., #FF0000)
- **Aliases** (alternative names, e.g., "work" ↔ "office")
- **Usage Counter** (tracks how many tasks use this tag)
- **Timestamps** (created_at, updated_at for auditing)

#### Example Tag
```json
{
  "name": "work",
  "description": "Work-related tasks",
  "color": "#FF0000",
  "aliases": ["office", "job"],
  "usage_count": 42,
  "created_at": "2024-12-24T10:30:00.000000",
  "updated_at": "2024-12-24T15:45:00.000000"
}
```

### 2.3 Tag Recommendations

#### Algorithm
1. **Keyword Matching** (50% weight)
   - String similarity between keywords in task and tag names
   - Also checks alias matches

2. **Co-occurrence History** (30% weight)
   - How frequently tags appear together
   - Learns from existing task patterns

3. **Usage Frequency** (20% weight)
   - Popular tags are recommended more
   - Prevents recommending obscure tags

#### Methods
- `recommend_by_task_content()` - Based on task text and existing tags
- `recommend_by_keyword()` - Direct keyword matching
- `recommend_by_cooccurrence()` - Based on existing tags only

### 2.4 Query DSL (Domain-Specific Language)

#### Syntax
```
tag:name              # Tasks with tag "name"
completed:true        # Completed tasks
task:keyword          # Tasks containing keyword
```

#### Operators
- **AND** - Both conditions must be true
- **OR** - Either condition must be true
- **NOT** - Negates expression
- **(...)** - Groups expressions for precedence

#### Examples
```
tag:work AND urgent              # Tasks tagged with both work and urgent
(tag:work OR tag:personal) AND NOT completed:true  # Complex query
tag:work AND (urgent OR deadline:today)  # Nested expressions
```

#### Implementation
- **Lexer** - Tokenizes input string
- **Parser** - Builds AST (Abstract Syntax Tree)
- **Executor** - Evaluates AST against tasks

### 2.5 Concurrency Safety

#### Thread-Safe Operations
- Task creation (add_task)
- Task updates (update_task)
- Tag metadata operations
- Co-occurrence recording
- All protected by RLock

#### Testing
- 50+ concurrent operations verified
- 500+ concurrent additions stress tested
- No data corruption observed

### 2.6 Plugin System

#### Hook Points
- `on_task_added(task_id, task, tags)` - When task is created
- `on_task_updated(task_id, task, tags)` - When task is modified
- `on_task_completed(task_id, task)` - When task is marked done
- `on_tag_added(tag_name, tag_metadata)` - When tag is created
- `on_query_executed(query, result_count)` - After query execution

#### Plugin Loading
- Auto-discovery from `plugins/` directory
- Manual registration via `subscribe()`
- Multiple handlers per hook

#### Example Plugin
```python
# plugins/notification_plugin.py
def register_hooks(plugin_manager):
    plugin_manager.subscribe("on_task_added", notify_task)

def notify_task(task_id, task, tags):
    print(f"New task: {task}")
```

### 2.7 Validation

#### Task Validation
- Non-empty string
- Max 1000 characters
- Reject null/None values

#### Tag Name Validation
- Alphanumeric + dash and underscore only
- Max 50 characters
- Must be non-empty
- Matches regex: `^[a-zA-Z0-9_-]+$`

#### Color Validation
- Valid hex color code
- Format: `#RRGGBB` (e.g., #FF0000)

### 2.8 CLI Enhancements

#### Features
- **Colorized Output** - ANSI color codes for status and tags
- **Fuzzy Search** - Partial matching for task/tag search
- **Paging** - Display long results with page breaks
- **Status Indicators** - ✓ for complete, ○ for incomplete

#### Color Support
- Task status (green/blue)
- Tags (cyan)
- Errors (red)
- Success (green)
- Info (cyan)

## 3. API Reference

### 3.1 Backward Compatible API

All functions from `todo_original.py`:
```python
add_todo(task: str, tags: Optional[List[str]] = None) -> None
list_todos() -> List[Dict]
filter_by_tags(tags: List[str], match_all: bool = False) -> List[Dict]
add_tag_to_task(index: int, tag: str) -> None
remove_tag_from_task(index: int, tag: str) -> None
show_tag_stats() -> Dict[str, int]
list_all_tags() -> List[str]
complete_task(index: int) -> None
```

### 3.2 New Advanced API

```python
add_structured_tag(name, description="", color="#CCCCCC", aliases=None) -> Dict
list_tags_with_metadata() -> List[Dict]
query_tasks_dsl(query: str) -> List[Dict]
recommend_tags(task_text, existing_tags=None, limit=5) -> List[tuple]
get_tag_metadata(tag_name: str) -> Optional[Dict]
get_related_tags(tag_name: str, limit: int = 5) -> List[tuple]
```

## 4. Performance Targets

All targets are verified by automated performance tests:

| Operation | Target | Status | Test Location |
|-----------|--------|--------|----------------|
| Load 10,000 tasks | < 80 ms | ✅ | perf_test.py |
| Typical query | < 50 ms | ✅ | perf_test.py |
| Tag update | < 10 ms | ✅ | perf_test.py |
| Concurrent safety | No corruption | ✅ | test_advanced_todo.py |

## 5. Testing Strategy

### 5.1 Test Coverage

#### Unit Tests (test_advanced_todo.py)
- **Backward Compatibility** (8 tests)
- **Persistence** (2 tests)
- **Concurrency** (2 tests)
- **Query DSL** (4 tests)
- **Tag Metadata** (3 tests)
- **Validation** (5 tests)
- **Plugins** (2 tests)
- **Performance** (2 tests)

#### Total: 28+ unit tests

### 5.2 Property-Based Testing

Can be extended with Hypothesis for:
- Random tag names and validation
- Random DSL query generation and execution
- Concurrent operation ordering

### 5.3 Stress Testing

- 10,000 task creation and retrieval
- 500+ concurrent task additions
- 100+ simultaneous read/write operations
- Large result set handling (10K items)

## 6. Database Schema

### tasks table
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task TEXT NOT NULL,
    completed BOOLEAN DEFAULT 0,
    tags TEXT DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
```

### tag_metadata table
```sql
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

### tag_cooccurrence table
```sql
CREATE TABLE tag_cooccurrence (
    tag1 TEXT NOT NULL,
    tag2 TEXT NOT NULL,
    count INTEGER DEFAULT 1,
    PRIMARY KEY (tag1, tag2)
)
```

## 7. Configuration & Customization

### Database Path
```python
from todo_advanced.storage import get_storage
storage = get_storage("custom_path.db")
```

### Plugin Discovery
```python
from todo_advanced.plugins import get_plugin_manager
pm = get_plugin_manager()
pm.discover_plugins("custom_plugins_dir")
```

### Cache TTL
```python
from todo_advanced.caching import get_cache
cache = get_cache()
cache.ttl_seconds = 600  # 10 minutes
```

## 8. Backward Compatibility

### Guarantee
100% API compatibility with `todo_original.py`:
- Same function signatures
- Same return types
- Same behavior for all operations
- No breaking changes

### Testing
All original API tests pass without modification (8 tests in test_advanced_todo.py)

## 9. Future Enhancements

### Phase 2
- Full-text search across task descriptions
- Due date tracking and reminders
- Task priorities and ordering
- Recurring task support

### Phase 3
- Multi-user support with permissions
- Task dependencies (blocking/blocked-by)
- REST API interface
- Web dashboard UI

### Phase 4
- Distributed task synchronization
- End-to-end encryption
- Analytics and reporting
- Integration with external services

## 10. Deployment & Packaging

### Installation
```bash
pip install -r requirements.txt
```

### File Structure
```
project/
├── todo_advanced/           # Main package
│   ├── __init__.py
│   ├── api.py              # Public API
│   ├── storage.py          # Database
│   ├── tags.py             # Tag model
│   ├── query_dsl.py        # Query language
│   ├── recommendations.py  # Recommender
│   ├── plugins.py          # Plugin system
│   ├── validation.py       # Validation
│   ├── caching.py          # Caching
│   ├── metrics.py          # Metrics
│   └── cli.py              # CLI tools
├── tests/                  # Test suite
│   ├── __init__.py
│   └── test_advanced_todo.py
├── perf_test.py           # Performance tests
├── run_tests.sh           # Unix test runner
├── run_tests.ps1          # Windows test runner
├── requirements.txt       # Dependencies
├── requirements-dev.txt   # Dev dependencies
├── README.md              # User guide
└── FEATURE_SPEC.md        # This file
```

## 11. Known Limitations

1. Single-user (no user accounts or permissions)
2. No encryption of stored data
3. SQLite limited to ~140TB file size (practical limit much lower)
4. In-process caching only (not distributed)
5. No automatic backups (manual backup needed)

## 12. Success Criteria

✅ All items completed:
- [x] Persistent tag & task storage
- [x] Structured tag model with metadata
- [x] Tag recommendations engine
- [x] Query DSL with operators
- [x] Concurrency safety
- [x] Modular architecture
- [x] Plugin system with hooks
- [x] Enhanced CLI
- [x] Backward compatibility
- [x] Comprehensive test suite
- [x] Performance benchmarks
- [x] Documentation

---

**FEATURE_SPEC.md** - Advanced Tag System v1.0.0
