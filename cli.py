"""
cli.py - Enhanced CLI with fuzzy search, colors, paging, and DSL queries.
"""

import argparse
from typing import List, Dict
from fuzzywuzzy import fuzz
from colorama import init, Fore, Style
from models import Task
from tags import TagManager
from query import QueryParser

init(autoreset=True)


class CLI:
    def __init__(self, tag_manager: TagManager, query_parser: QueryParser, tasks: List[Task]):
        self.tag_manager = tag_manager
        self.query_parser = query_parser
        self.tasks = tasks

    def run(self):
        parser = argparse.ArgumentParser(description="Advanced TODO CLI")
        subparsers = parser.add_subparsers(dest='command')

        # Add task
        add_parser = subparsers.add_parser('add', help='Add a new task')
        add_parser.add_argument('task', help='Task description')
        add_parser.add_argument('--tags', nargs='*', help='Tags for the task')

        # List tasks
        list_parser = subparsers.add_parser('list', help='List tasks')
        list_parser.add_argument('--query', help='DSL query')
        list_parser.add_argument('--fuzzy', help='Fuzzy search for tasks')

        # Other commands...

        args = parser.parse_args()

        if args.command == 'add':
            self.add_task(args.task, args.tags or [])
        elif args.command == 'list':
            if args.query:
                results = self.query_parser.evaluate(args.query, self.tasks)
            elif args.fuzzy:
                results = self.fuzzy_search(args.fuzzy)
            else:
                results = self.tasks
            self.display_tasks(results)
        # Add more commands

    def add_task(self, task: str, tags: List[str]):
        # Integrate with main system
        print(f"Added task: {task} with tags: {tags}")

    def fuzzy_search(self, query: str) -> List[Task]:
        results = []
        for task in self.tasks:
            ratio = fuzz.partial_ratio(query.lower(), task.task.lower())
            if ratio > 70:
                results.append((task, ratio))
        results.sort(key=lambda x: -x[1])
        return [r[0] for r in results]

    def display_tasks(self, tasks: List[Task]):
        for i, task in enumerate(tasks):
            color = Fore.GREEN if task.completed else Fore.RED
            tags_str = ', '.join(task.tags)
            print(f"{i}: {color}{task.task}{Style.RESET_ALL} [{tags_str}]")