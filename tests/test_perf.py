import time
from todo_advanced.storage import SQLiteStore


def test_perf_load_10k_tasks(tmp_path):
    db = tmp_path / "p.db"
    store = SQLiteStore(str(db))
    n = 10000
    titles = [f"task {i}" for i in range(n)]
    start = time.time()
    store.add_tasks_bulk(titles)
    duration = (time.time() - start) * 1000.0
    # Very loose check for now to ensure it runs quickly in CI (allow 60s here)
    assert duration < 60000
