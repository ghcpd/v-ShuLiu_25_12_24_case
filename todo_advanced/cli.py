"""Command-line interface for the advanced TODO app.

This is an initial CLI using argparse. We'll add fuzzy search, paged output, and colorized
printing later. The CLI exposes a `run` entry point for use in scripts.
"""
from __future__ import annotations

import argparse
import sys
from .storage import SQLiteStore


def _print_task_row(row):
    status = "✓" if row["completed"] else " "
    print(f"[{status}] {row['id']}: {row['title']}")


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="todo-advanced")
    parser.add_argument("--db", default=".data/todo.db")
    sub = parser.add_subparsers(dest="cmd")
    add = sub.add_parser("add")
    add.add_argument("title")
    add.add_argument("--body")
    sub.add_parser("list")

    args = parser.parse_args(argv)
    store = SQLiteStore(args.db)
    if args.cmd == "add":
        tid = store.add_task(args.title, args.body)
        print("Added", tid)
        return 0
    if args.cmd == "list":
        for row in store.list_tasks():
            _print_task_row(row)
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(run())
