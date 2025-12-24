"""Simple performance validator for basic targets described in the spec."""
import time
from todo_advanced_pkg.core import AdvancedTodo


def perf_run(n=10000):
    store = AdvancedTodo(":memory:")
    start = time.time()
    for i in range(n):
        store.add_task(f"task-{i}", ["tag1", f"t{i%20}"])
    dur = (time.time() - start) * 1000
    print(f"insert {n} tasks: {dur:.1f} ms")
    start = time.time()
    _ = store.list_tasks()
    dur2 = (time.time() - start) * 1000
    print(f"load {n} tasks: {dur2:.1f} ms")


if __name__ == "__main__":
    perf_run(10000)
