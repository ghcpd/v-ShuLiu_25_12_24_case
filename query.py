"""
query.py - Query language parser and evaluator for advanced filtering.
"""

import re
from typing import List, Callable
from models import Task


class QueryParser:
    def __init__(self):
        self.operators = {
            'AND': lambda a, b: a and b,
            'OR': lambda a, b: a or b,
            'NOT': lambda a: not a,
        }
        self.custom_operators = {}

    def add_operator(self, name: str, func: Callable):
        self.custom_operators[name] = func

    def parse(self, query: str) -> Callable[[Task], bool]:
        # Simple parser: split by spaces, assume AND between terms
        terms = query.split()
        conditions = []
        for term in terms:
            if term.startswith('tag:'):
                tag = term[4:]
                conditions.append(lambda t, tag=tag: tag in t.tags)
            elif term == 'completed':
                conditions.append(lambda t: t.completed)
            elif term == 'NOT':
                # Simple NOT, assume next term
                pass  # Not implemented
            else:
                conditions.append(lambda t, term=term: term in t.tags)
        def evaluator(task: Task) -> bool:
            for cond in conditions:
                if not cond(task):
                    return False
            return True
        return evaluator

    def evaluate(self, query: str, tasks: List[Task]) -> List[Task]:
        if not query.strip():
            return tasks
        evaluator = self.parse(query)
        return [t for t in tasks if evaluator(t)]