"""
perf_test.py - Performance validation.
"""

import time
from todo_advanced import add_todo, list_todos, query_tasks


def test_load_performance():
    start = time.time()
    for i in range(10000):
        add_todo(f"Task {i}", ["tag{i%10}"])
    load_time = time.time() - start
    print(f"Loaded 10k tasks in {load_time:.2f}s")
    assert load_time < 0.08


def test_query_performance():
    start = time.time()
    results = query_tasks("tag:tag1")
    query_time = time.time() - start
    print(f"Query in {query_time:.2f}s")
    assert query_time < 0.05


if __name__ == "__main__":
    test_load_performance()
    test_query_performance()