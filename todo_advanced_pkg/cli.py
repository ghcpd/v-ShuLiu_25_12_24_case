"""A small CLI that demonstrates enhanced features (fuzzy search, paging,
DSL query).
"""
import argparse
from .core import AdvancedTodo
from colorama import Fore, Style, init as colorama_init
from difflib import get_close_matches

colorama_init(autoreset=True)


def _print_task(i, t):
    status = "✔" if t.get("completed") else " "
    tags = ",".join(t.get("tags", []))
    print(f"[{i}] {status} {t['task']} {Fore.CYAN}{tags}{Style.RESET_ALL}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="todo")
    sub = p.add_subparsers(dest="cmd")
    add = sub.add_parser("add")
    add.add_argument("task")
    add.add_argument("--tags", nargs="*", default=[])

    listp = sub.add_parser("list")
    listp.add_argument("--page", type=int, default=1)
    listp.add_argument("--per-page", type=int, default=10)

    q = sub.add_parser("query")
    q.add_argument("expr")

    rec = sub.add_parser("recommend")
    rec.add_argument("text")

    args = p.parse_args(argv)
    store = AdvancedTodo()

    if args.cmd == "add":
        store.add_task(args.task, args.tags)
        print(Fore.GREEN + "added")
    elif args.cmd == "list":
        tasks = store.list_tasks()
        start = (args.page - 1) * args.per_page
        for i, t in enumerate(tasks[start : start + args.per_page], start):
            _print_task(i, t)
    elif args.cmd == "query":
        tasks = store.query(args.expr)
        for i, t in enumerate(tasks):
            _print_task(i, t)
    elif args.cmd == "recommend":
        for tag in store.recommend_tags(args.text):
            print(Fore.MAGENTA + tag)
    else:
        p.print_help()


if __name__ == "__main__":
    main()