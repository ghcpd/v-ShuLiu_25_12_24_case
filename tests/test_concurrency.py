import threading
from todo_advanced_pkg.core import AdvancedTodo


def test_concurrent_writes(tmp_path):
    db = tmp_path / "con.db"
    store = AdvancedTodo(str(db))

    def worker(i):
        store.add_task(f"task-{i}", ["t"])

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    tasks = store.list_tasks()
    assert len(tasks) == 50
    # usage count for tag 't' should be 50
    stats = store.tag_stats()
    assert stats.get("t", 0) >= 50
