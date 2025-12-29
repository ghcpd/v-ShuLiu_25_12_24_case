import tempfile
from todo_advanced.storage import SQLiteStore


def test_task_and_tag_linking(tmp_path):
    db = tmp_path / "s.db"
    store = SQLiteStore(str(db))
    tid = store.add_task("hello", "body")
    store.create_or_update_tag("x")
    store.add_tag_to_task(tid, "x")
    tags = store.list_tags()
    assert any(r["name"] == "x" for r in tags)

