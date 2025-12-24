# Advanced TODO — Tag System

This workspace adds a persistent, concurrent-safe, extensible tag system
for the original minimal `todo_original.py` API. The original module is
left unchanged and `todo_advanced.py` provides a backward-compatible
wrapper.

Quick start

- Add a task (persistent):
  python -c "from todo_advanced import add_todo; add_todo('buy milk', ['personal'])"
- List tasks:
  python -c "from todo_advanced import list_todos; print(list_todos())"
- Run DSL query:
  python -m todo_advanced_pkg.cli query "tag:personal AND NOT archived"

Testing

- One-click: `./run_tests.sh` (Linux/macOS) or `./run_tests.ps1` (Windows)

Files of interest

- `todo_advanced.py` — backward-compatible wrapper (preserves public API)
- `todo_advanced_pkg/` — implementation (storage, DSL, plugins, CLI)
- `tests/` — automated tests including performance checks
