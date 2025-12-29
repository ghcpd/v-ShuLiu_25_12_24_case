# Advanced TODO Application - Feature Specification

## Overview

This document provides a comprehensive technical specification for the Advanced Tag System feature addition to the TODO application. The system extends the original minimal implementation with persistent storage, structured tags, powerful query capabilities, and plugin extensibility—all while maintaining 100% backward compatibility.

## Architecture

### Core Components

1. **Storage Layer** (`storage.py`)
   - SQLite-based persistent storage with thread safety
   - Automatic schema initialization and migration
   - Transaction support for concurrent access
   - Tables: `tasks`, `tag_metadata`, `tag_cooccurrence`

2. **Tag Management** (`tags.py`)
   - Structured tag model with metadata (name, description, color, aliases)
   - Tag relationship tracking via co-occurrence graph
   - Usage frequency tracking
   - Tag aliases for name synonyms

3. **Query DSL** (`query_dsl.py`)
   - Lexer, Parser, and Executor for domain-specific queries
   - Support for AND/OR/NOT operators
   - Parentheses for grouping
   - Tag filters: `tag:name`, `completed:true`, `task:keyword`
   - Example: `(tag:work OR tag:office) AND NOT completed:true`

4. **Recommendations** (`recommendations.py`)
   - Keyword-based similarity scoring
   - Task content analysis
   - Co-occurrence pattern learning
   - Usage frequency weighting

5. **Plugin System** (`plugins.py`)
   - Hook-based extensibility
   - Available hooks: `on_task_added`, `on_task_updated`, `on_task_completed`, `on_tag_added`, `on_query_executed`
   - Auto-discovery from plugin directory

6. **Concurrency & Caching** (`caching.py`)
   - TTL-based result caching
   - Thread-safe cache operations
   - Cache invalidation by prefix

7. **Validation & Metrics** (`validation.py`, `metrics.py`)
   - Input validation for tasks, tags, colors
   - Operation timing and success tracking
   - Performance metrics collection

8. **CLI Tools** (`cli.py`)
   - ANSI color output
   - Task and tag formatting
   - Fuzzy search
   - Pagination support

## API Reference

### Backward-Compatible Functions

All original API functions work identically:

```python
add_todo(task: str, tags: List[str]) -> None
list_todos() -> List[Dict]
filter_by_tags(tags: List[str], match_all: bool) -> List[Dict]
add_tag_to_task(index: int, tag: str) -> None
remove_tag_from_task(index: int, tag: str) -> None
show_tag_stats() -> Dict[str, int]
list_all_tags() -> List[str]
complete_task(index: int) -> None
```

### New Advanced API

```python
# Structured tags
add_structured_tag(
    name: str,
    description: str = "",
    color: str = "#CCCCCC",
    aliases: Optional[List[str]] = None
) -> None

list_tags_with_metadata() -> List[Dict]

# DSL queries
query_tasks_dsl(query: str) -> List[Dict]
# Example: query_tasks_dsl("tag:work AND NOT completed:true")

# Recommendations
recommend_tags(
    task_text: str,
    existing_tags: Optional[List[str]] = None,
    limit: int = 5
) -> List[Tuple[str, float]]

get_tag_metadata(tag_name: str) -> Optional[Dict]
get_related_tags(tag_name: str, limit: int = 5) -> List[Tuple[str, int]]
```

## DSL Query Language

### Syntax

```
query := expression
expression := or_expr
or_expr := and_expr (OR and_expr)*
and_expr := not_expr (AND not_expr)*
not_expr := NOT not_expr | atom
atom := TAG | LPAREN expression RPAREN

TAG := simple_tag | field_filter
simple_tag := identifier
field_filter := field ":" value
field := "tag" | "completed" | "task"
```

### Examples

```
# Simple tag
work

# Multiple tags (AND)
work AND urgent

# Alternatives (OR)
tag:work OR tag:office

# Negation
NOT archived
NOT completed:true

# Complex expressions
(tag:work OR tag:office) AND (urgent OR high-priority) AND NOT archived
```

## Data Model

### Task Record
```python
{
    "id": int,
    "task": str,
    "completed": bool,
    "tags": List[str],
    "created_at": str,  # ISO format
    "updated_at": str
}
```

### Tag Record
```python
{
    "name": str,
    "description": str,
    "color": str,  # hex code
    "aliases": List[str],
    "usage_count": int,
    "created_at": str,  # ISO format
    "updated_at": str
}
```

### Co-occurrence Graph
```
Bidirectional edges representing tag pairs that appear together
tag1 <-> tag2: count (frequency)
```

## Concurrency Model

- **Thread Safety**: All storage operations protected by `RLock`
- **Database Locking**: SQLite with 5.0 second timeout
- **Isolation**: READ_COMMITTED equivalent (SQLite default)
- **Atomicity**: Transaction-based for compound operations

## Performance Targets

- Load 10,000 tasks: < 80 ms
- Typical DSL queries: < 50 ms
- Tag co-occurrence updates: < 10 ms
- No data corruption under concurrent writes

## Testing Strategy

### Unit Tests
- Storage backend operations
- Tag management
- DSL lexer/parser/executor
- Recommendations engine
- Validation logic
- Plugin system

### Integration Tests
- API backward compatibility
- Query execution end-to-end
- Tag metadata persistence

### Concurrency Tests
- Concurrent task creation (200 tasks, 4 threads)
- Concurrent tag updates
- Co-occurrence recording races
- Mixed read/write operations

### Performance Tests
- 10,000 task loading
- Large dataset queries
- Tag operation scaling
- Recommendation latency

### Property-Based Tests
- Random query generation and execution
- Concurrent operation invariants
- Data consistency validation

## Deployment

### Database

- Default: `todo_advanced.db` (SQLite)
- Location: Current working directory
- Automatic initialization on first use
- Schema evolution support

### Plugins

- Location: `plugins/` directory
- Auto-discovery on startup
- Hook registration via `register_hooks()`

## Extension Points

### Custom Query Operators

Extend `QueryExecutor._evaluate_tag()` to support new field types:

```python
def _evaluate_tag(self, tag_spec: str, task: Dict) -> bool:
    if ":" in tag_spec:
        key, value = tag_spec.split(":", 1)
        if key.lower() == "custom":
            # Custom logic
            return self._evaluate_custom(value, task)
```

### Plugin Hooks

Subscribe to events in plugins:

```python
def register_hooks(plugin_manager):
    plugin_manager.subscribe("on_task_added", handle_new_task)
    plugin_manager.subscribe("on_tag_added", handle_new_tag)
```

## Configuration

Environment variables:

- `TODO_DB_PATH`: Override database location
- `TODO_CACHE_TTL`: Cache TTL in seconds (default: 300)
- `TODO_PLUGIN_DIR`: Plugin search directory (default: "plugins")

## Error Handling

- **Validation Errors**: Raised as `ValueError` with descriptive messages
- **Database Errors**: Wrapped and re-raised with context
- **Plugin Errors**: Logged but don't crash the system
- **Query Errors**: `ValueError` with parse/execution details

## Future Enhancements

- Full-text search on task content
- Tag hierarchies (parent-child relationships)
- Task templates with default tags
- Scheduled/recurring tasks
- Export to various formats (JSON, CSV, iCal)
- REST API wrapper
- Web UI

## References

- SQLite: https://www.sqlite.org/
- Python threading: https://docs.python.org/3/library/threading.html
- Plugin systems: https://en.wikipedia.org/wiki/Plug-in_(computing)
