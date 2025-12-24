"""
Performance and stress tests for the advanced TODO system.

Benchmarks critical paths against performance targets.
"""

import time
import sys
import tempfile
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).parent.parent))

from todo_advanced import api
from todo_advanced.storage import get_storage, reset_storage
from todo_advanced.query_dsl import QueryDSL
from todo_advanced.recommendations import get_recommender, reset_recommender


class PerformanceBenchmark:
    """Benchmarks performance of key operations."""

    def __init__(self):
        self.results = {}
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()

    def cleanup(self):
        """Clean up temp database."""
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def benchmark(self, name: str, func, *args, **kwargs):
        """Run a benchmark."""
        print(f"Benchmarking: {name}...", end=" ", flush=True)

        start = time.time()
        result = func(*args, **kwargs)
        elapsed_ms = (time.time() - start) * 1000

        self.results[name] = elapsed_ms
        print(f"{elapsed_ms:.2f}ms")
        return result, elapsed_ms

    def test_load_10k_tasks(self):
        """Benchmark: Load 10,000 tasks."""
        reset_storage()
        storage = get_storage(self.temp_db.name)

        def load_tasks():
            for i in range(10000):
                storage.add_task(f"Task {i}", [f"tag{i % 10}"])

        _, elapsed = self.benchmark("Load 10K tasks", load_tasks)
        print(f"  Target: < 80ms | Result: {'✓ PASS' if elapsed < 80 else '✗ FAIL'}")
        return elapsed

    def test_typical_query(self):
        """Benchmark: Typical DSL query."""
        storage = get_storage(self.temp_db.name)
        tasks = storage.list_tasks()

        def query_tasks():
            return QueryDSL.execute("tag:tag1", tasks)

        _, elapsed = self.benchmark(
            "Typical DSL query (100x)", 
            lambda: [QueryDSL.execute("tag:tag1", tasks) for _ in range(100)]
        )
        avg_elapsed = elapsed / 100
        print(f"  Average per query: {avg_elapsed:.2f}ms | Target: < 50ms | Result: {'✓ PASS' if avg_elapsed < 50 else '✗ FAIL'}")
        return avg_elapsed

    def test_tag_cooccurrence_update(self):
        """Benchmark: Tag relationship updates."""
        reset_storage()
        storage = get_storage(self.temp_db.name)

        def update_cooccurrence():
            for i in range(100):
                storage.record_tag_cooccurrence(f"tag1", f"tag{i % 10}")

        _, elapsed = self.benchmark("100 cooccurrence updates", update_cooccurrence)
        avg_elapsed = elapsed / 100
        print(f"  Average per update: {avg_elapsed:.2f}ms | Target: < 10ms | Result: {'✓ PASS' if avg_elapsed < 10 else '✗ FAIL'}")
        return avg_elapsed

    def test_concurrent_writes(self):
        """Benchmark: Concurrent writes."""
        reset_storage()
        storage = get_storage(self.temp_db.name)

        def concurrent_adds():
            def add_in_thread(thread_id):
                for i in range(100):
                    storage.add_task(f"Task-{thread_id}-{i}", ["tag1"])

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(add_in_thread, i) for i in range(5)]
                for future in futures:
                    future.result()

        _, elapsed = self.benchmark("500 concurrent additions (5 threads)", concurrent_adds)
        print(f"  Total time: {elapsed:.2f}ms")
        return elapsed

    def test_tag_recommendations(self):
        """Benchmark: Tag recommendations."""
        reset_recommender()
        recommender = get_recommender()

        def get_recommendations():
            return recommender.recommend_by_task_content(
                "Fix the critical bug in the authentication system",
                existing_tags=["urgent"],
                limit=5
            )

        _, elapsed = self.benchmark("Tag recommendations (100x)", 
                                   lambda: [recommender.recommend_by_task_content(
                                       "Fix the critical bug", ["urgent"], 5
                                   ) for _ in range(100)])
        avg_elapsed = elapsed / 100
        print(f"  Average per recommendation: {avg_elapsed:.2f}ms")
        return avg_elapsed

    def run_all(self):
        """Run all benchmarks."""
        print("\n" + "=" * 70)
        print("PERFORMANCE BENCHMARKS")
        print("=" * 70)
        print()

        try:
            t1 = self.test_load_10k_tasks()
            print()
            t2 = self.test_typical_query()
            print()
            t3 = self.test_tag_cooccurrence_update()
            print()
            self.test_concurrent_writes()
            print()
            self.test_tag_recommendations()

            print()
            print("=" * 70)
            print("PERFORMANCE SUMMARY")
            print("=" * 70)
            for name, elapsed in self.results.items():
                print(f"{name:40} {elapsed:10.2f}ms")
            print("=" * 70)

        finally:
            self.cleanup()


if __name__ == "__main__":
    bench = PerformanceBenchmark()
    bench.run_all()
