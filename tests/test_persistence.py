import tempfile
from todo_advanced_pkg.core import AdvancedTodo


def test_persistence_between_instances(tmp_path):
    db = tmp_path / "persist.db"
    s1 = AdvancedTodo(str(db))
    s1.add_task("persist-me", ["p1", "p2"])
    tasks1 = s1.list_tasks()
    assert len(tasks1) == 1
    # new instance should see the same data
    s2 = AdvancedTodo(str(db))
    tasks2 = s2.list_tasks()
    assert len(tasks2) == 1
    assert tasks2[0]["task"] == "persist-me"
