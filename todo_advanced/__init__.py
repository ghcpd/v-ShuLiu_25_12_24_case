"""todo_advanced package - high level facade will be exposed via `todo_advanced.py`.

This package is intentionally minimal at first: it provides a storage backend, a tag model,
a query engine stub, a plugin loader stub and a CLI entry point. Each module is documented
and designed to be unit-testable. See `FEATURE_SPEC.md` for the detailed spec.
"""

from . import api as todo_advanced

__all__ = ["storage", "tags", "query", "plugins", "cli", "todo_advanced"]
