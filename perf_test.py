"""Basic performance smoke tests (not a replacement for benchmarking infra)."""
import time
from todo_advanced import add_todo, list_todos


def generate(n=10000):
    for i in range(n):
        add_todo(f"task {i}", ["perf", f"batch-{i%10}"])


if __name__ == "__main__":
    t0 = time.perf_counter()
    generate(10000)
    t1 = time.perf_counter()
    rows = list_todos()
    t2 = time.perf_counter()
    print(f"created 10k tasks in {(t1-t0):.3f}s; load {len(rows)} tasks in {(t2-t1):.3f}s")
