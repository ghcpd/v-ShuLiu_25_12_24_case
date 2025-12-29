"""Small CLI to exercise the advanced tag system.

Features:
- Backward-compatible commands similar to the original demo
- DSL query execution
- Tag recommendations
- Colorized, paged output
"""
from __future__ import annotations
import argparse
import shutil
import sys
from todo_advanced_pkg import api, tags
from colorama import Fore, Style, init as _color_init

_color_init()


def _print_task_row(r: dict):
    tags = ", ".join([f"{Fore.CYAN}{t}{Style.RESET_ALL}" for t in r.get("tags", [])])
    status = f"{Fore.GREEN}✓{Style.RESET_ALL}" if r.get("completed") else " "
    print(f"[{r.get('id')}] {status} {r.get('task')} {tags}")


def _pager(lines: list[str]):
    cols = shutil.get_terminal_size((80, 20)).lines
    if len(lines) <= cols:
        print("\n".join(lines))
        return
    # simple paging
    for i in range(0, len(lines), cols - 2):
        chunk = lines[i : i + cols - 2]
        print("\n".join(chunk))
        if i + cols - 2 < len(lines):
            input("--More--")


def main(argv=None):
    p = argparse.ArgumentParser(prog="todo")
    sub = p.add_subparsers(dest="cmd")
    a = sub.add_parser("add")
    a.add_argument("task")
    a.add_argument("-t", "--tag", action="append", default=[])

    sub.add_parser("list")

    q = sub.add_parser("query")
    q.add_argument("dsl")

    s = sub.add_parser("suggest-tags")
    s.add_argument("text")

    args = p.parse_args(argv)
    if args.cmd == "add":
        api.add_todo(args.task, args.tag)
        print("added")
    elif args.cmd == "list":
        rows = api.list_todos()
        lines = []
        for r in rows:
            lines.append(f"[{r.get('task')}] tags={r.get('tags')}")
        _pager(lines)
    elif args.cmd == "query":
        rows = api.query_tasks(args.dsl)
        for r in rows:
            _print_task_row(r)
    elif args.cmd == "suggest-tags":
        for rec in api.recommend_tags(args.text):
            print(f"{rec['tag']} (score={rec['score']:.1f})")
    else:
        p.print_help()


if __name__ == "__main__":
    main()
