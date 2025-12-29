import time
from todo_advanced_pkg import storage
import todo_advanced as ta


def test_perf_smoke(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_FILE", tmp_path / "perf.db")
    storage.initialize()
    n = 1000
    t0 = time.perf_counter()
    for i in range(n):
        ta.add_todo(f"task-{i}", [f"batch-{i%10}"])
    t1 = time.perf_counter()
    rows = ta.list_todos()
    t2 = time.perf_counter()
    print(f"insert {n} in {(t1-t0):.3f}s; load {len(rows)} in {(t2-t1):.3f}s")
    assert len(rows) == n
