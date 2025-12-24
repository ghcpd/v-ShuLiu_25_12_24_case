import threading

from todo_advanced_pkg import storage
import todo_advanced as ta


def worker(n):
    for i in range(n):
        ta.add_todo(f"t-{threading.get_ident()}-{i}", ["c"])


def test_concurrent_writes(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_FILE", tmp_path / "con.db")
    storage.initialize()
    threads = [threading.Thread(target=worker, args=(200,)) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    rows = ta.list_todos()
    assert len(rows) == 800
    stats = ta.show_tag_stats()
    assert stats.get("c", 0) == 800
