# todo_advanced — Advanced Tag System for TODO Application

This repository adds a persistent, extensible tag system on top of the
existing `todo_original.py` API. `todo_advanced.py` is a drop-in wrapper that
preserves the original public functions while providing powerful new features:

Highlights
- SQLite persistence with WAL and concurrency safety
- Structured tags (aliases, usage counts, timestamps)
- Tag co-occurrence and recommendations
- Mini-DSL query language (tag:... AND/OR/NOT with parentheses)
- Plugin hooks and auto-discovery
- Enhanced CLI with fuzzy search and colorized output

Quick test
- Windows PowerShell: `./run_tests.ps1`
- Unix / Git Bash: `./run_tests.sh`

See `FEATURE_SPEC.md` for details.
