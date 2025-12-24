import time
from todo_advanced_pkg.core import AdvancedTodo


def test_perf_load_many(tmp_path):
    db = tmp_path / "perf.db"
    store = AdvancedTodo(str(db))
    N = 10000
    start = time.time()
    for i in range(N):
        store.add_task(f"task-{i}", ["tag1", f"tag{i%10}"])
    dur = (time.time() - start) * 1000
    # we allow a relaxed upper bound in CI environments
    assert dur < 20000, f"insertion too slow: {dur}ms"

    start = time.time()
    tasks = store.list_tasks()
    load_ms = (time.time() - start) * 1000
    assert load_ms < 5000, f"load too slow: {load_ms}ms"
