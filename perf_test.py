"""
Performance testing suite for todo_advanced.
"""

import time
import tempfile
import os
from pathlib import Path

from todo_advanced.storage import SQLiteBackend, reset_storage
from todo_advanced.tags import TagManager
from todo_advanced.query_dsl import QueryDSL
from todo_advanced.recommendations import TagRecommender


class PerformanceTester:
    """Measure performance metrics."""

    def __init__(self):
        self.results = {}

    def measure(self, name: str, func, *args, **kwargs):
        """Measure execution time of a function."""
        start = time.time()
        result = func(*args, **kwargs)
        elapsed_ms = (time.time() - start) * 1000
        self.results[name] = elapsed_ms
        return result, elapsed_ms

    def print_results(self):
        """Print performance results."""
        print("\n" + "=" * 60)
        print("PERFORMANCE METRICS")
        print("=" * 60)
        for name, elapsed_ms in sorted(self.results.items()):
            print(f"{name:40s} {elapsed_ms:10.2f} ms")
        print("=" * 60 + "\n")


def benchmark_storage():
    """Benchmark storage operations."""
    print("\n### STORAGE BENCHMARKS ###\n")
    tester = PerformanceTester()

    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_path = temp_db.name
    temp_db.close()

    try:
        storage = SQLiteBackend(db_path)

        # Add 10k tasks
        def add_10k_tasks():
            for i in range(10000):
                storage.add_task(f"Task {i}", [f"tag-{i % 100}"])

        result, elapsed = tester.measure("Load 10,000 tasks", add_10k_tasks)
        print(f"✓ Loaded 10,000 tasks in {elapsed:.2f}ms (target: < 80ms)")

        # List all tasks
        def list_tasks():
            return storage.list_tasks()

        result, elapsed = tester.measure("List all 10,000 tasks", list_tasks)
        print(f"✓ Listed 10,000 tasks in {elapsed:.2f}ms")

        # Get single task
        def get_task():
            return storage.get_task(5000)

        result, elapsed = tester.measure("Get single task (ID 5000)", get_task)
        print(f"✓ Retrieved single task in {elapsed:.2f}ms")

        # Update task
        def update_task():
            return storage.update_task(5000, tags=["updated"])

        result, elapsed = tester.measure("Update single task", update_task)
        print(f"✓ Updated task in {elapsed:.2f}ms")

        # Tag metadata operations
        def add_tag_metadata():
            for i in range(100):
                storage.add_tag_metadata(f"tag-{i}", usage_count=0)

        result, elapsed = tester.measure("Add 100 tags metadata", add_tag_metadata)

        def record_usage():
            for i in range(1000):
                storage.record_tag_usage(f"tag-{i % 100}")

        result, elapsed = tester.measure("Record 1000 tag usages", record_usage)

        tester.print_results()

    finally:
        reset_storage()
        if os.path.exists(db_path):
            os.unlink(db_path)


def benchmark_query():
    """Benchmark query operations."""
    print("\n### QUERY DSL BENCHMARKS ###\n")
    tester = PerformanceTester()

    # Create test data
    tasks = []
    for i in range(10000):
        tasks.append({
            "id": i,
            "task": f"Task {i}",
            "completed": i % 2 == 0,
            "tags": [f"tag-{j}" for j in range(i % 10)],
        })

    # Simple tag query
    def simple_query():
        return QueryDSL.execute("tag-1", tasks)

    result, elapsed = tester.measure("Simple tag query", simple_query)
    print(f"✓ Simple query (10k tasks) in {elapsed:.2f}ms (target: < 50ms)")

    # AND query
    def and_query():
        return QueryDSL.execute("tag-1 AND tag-2", tasks)

    result, elapsed = tester.measure("AND query", and_query)

    # Complex query
    def complex_query():
        return QueryDSL.execute("(tag-1 OR tag-2) AND NOT completed:true", tasks)

    result, elapsed = tester.measure("Complex query with NOT", complex_query)

    tester.print_results()


def benchmark_tags():
    """Benchmark tag operations."""
    print("\n### TAG MANAGEMENT BENCHMARKS ###\n")
    tester = PerformanceTester()

    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_path = temp_db.name
    temp_db.close()

    try:
        storage = SQLiteBackend(db_path)
        manager = TagManager()
        manager.storage = storage

        # Create tags
        def create_tags():
            for i in range(100):
                manager.create_tag(f"tag-{i}", description=f"Tag {i}")

        result, elapsed = tester.measure("Create 100 tags", create_tags)

        # Record co-occurrences
        def record_cooccurrences():
            for i in range(1000):
                tag1 = f"tag-{i % 50}"
                tag2 = f"tag-{(i + 1) % 50}"
                manager.record_cooccurrence(tag1, tag2)

        result, elapsed = tester.measure("Record 1000 co-occurrences", record_cooccurrences)
        print(f"✓ Tag co-occurrence updates in {elapsed:.2f}ms (target: < 10ms per update)")

        # Get related tags
        def get_related():
            return manager.get_related_tags("tag-0", limit=10)

        result, elapsed = tester.measure("Get related tags", get_related)

        tester.print_results()

    finally:
        reset_storage()
        if os.path.exists(db_path):
            os.unlink(db_path)


def benchmark_recommendations():
    """Benchmark recommendation engine."""
    print("\n### RECOMMENDATION ENGINE BENCHMARKS ###\n")
    tester = PerformanceTester()

    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_path = temp_db.name
    temp_db.close()

    try:
        storage = SQLiteBackend(db_path)
        manager = TagManager()
        manager.storage = storage
        recommender = TagRecommender()
        recommender.tag_manager = manager
        recommender.storage = storage

        # Create test tags
        for i in range(100):
            manager.create_tag(f"tag-{i}")

        # Record co-occurrences
        for i in range(1000):
            tag1 = f"tag-{i % 50}"
            tag2 = f"tag-{(i + 1) % 50}"
            manager.record_cooccurrence(tag1, tag2)

        # Keyword-based recommendation
        def keyword_rec():
            return recommender.recommend_by_keyword("tag", limit=5)

        result, elapsed = tester.measure("Recommend by keyword", keyword_rec)

        # Task content recommendation
        def task_rec():
            return recommender.recommend_by_task_content("work email urgent meeting")

        result, elapsed = tester.measure("Recommend by task content", task_rec)

        # Co-occurrence recommendation
        def cooccurrence_rec():
            return recommender.recommend_by_cooccurrence(["tag-0", "tag-1"])

        result, elapsed = tester.measure("Recommend by co-occurrence", cooccurrence_rec)

        tester.print_results()

    finally:
        reset_storage()
        if os.path.exists(db_path):
            os.unlink(db_path)


def main():
    """Run all benchmarks."""
    print("\n" + "=" * 60)
    print("TODO ADVANCED - PERFORMANCE BENCHMARK SUITE")
    print("=" * 60)

    benchmark_storage()
    benchmark_query()
    benchmark_tags()
    benchmark_recommendations()

    print("\n" + "=" * 60)
    print("BENCHMARK COMPLETE")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
