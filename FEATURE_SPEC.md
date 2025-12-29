# Feature spec — Advanced Tag System (summary)

Goals
- Persistent, concurrent-safe tag & task storage
- Structured tag model (aliases, colors, metadata)
- Tag recommendations + co-occurrence graph
- Mini-DSL for expressive queries
- Plugin system + CLI improvements
- Backward compatibility with `todo_original.py`

Storage
- SQLite (WAL), simple migrations, thread-local connections
- Tables: tasks, tags, task_tags, tag_cooccurrence, metadata

Tag model
- name, aliases (JSON), color, description, timestamps, usage_count
- co-occurrence stored in `tag_cooccurrence` table

Query language
- boolean operators, parentheses, tag:NAME and free text
- scored results and extensible operator registry

Concurrency
- write lock + SQLite transactions -> safe concurrent access

Extensibility
- plugin discovery in `todo_advanced_plugins` or by module name
- hooks: on_task_added, on_tag_added, on_task_completed

Compatibility
- `todo_advanced.py` exposes the original API unchanged

Performance targets
- 10k tasks load < 80ms (cold/warm depends on machine)
- typical queries < 50ms
- tag updates < 10ms

Testing
- unit, concurrency, property-based (Hypothesis), perf smoke tests
