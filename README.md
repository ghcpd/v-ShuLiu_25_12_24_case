# TODO Advanced - Advanced Tag System (Prototype)

This repository contains a prototype implementation of an advanced tag system for a TODO app.

Key points:
- Persistent storage using SQLite (basic migrations and locking)
- Structured tag model with aliases, colors, descriptions and usage counts (initial)
- Mini DSL parser for queries (tokenizer + parser)
- Plugin discovery and hook stubs
- Compatibility wrapper `todo_advanced.py` exposing the same API as `todo_original.py`

Run tests:
- POSIX: `./run_tests.sh`
- PowerShell: `./run_tests.ps1`
