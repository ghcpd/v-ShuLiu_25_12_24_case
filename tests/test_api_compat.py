import os
import tempfile
from todo_advanced import todo_advanced as adv


def test_add_and_list_todos(tmp_path):
    db = tmp_path / "test.db"
    adv._store = adv.SQLiteStore(str(db))  # swap to temp DB
    adv.add_todo("write tests", tags=["testing", "urgent"])
    out = adv.list_todos()
    assert any("write tests" == t["task"] for t in out)


def test_filter_by_tags(tmp_path):
    db = tmp_path / "test2.db"
    adv._store = adv.SQLiteStore(str(db))
    adv.add_todo("task1", tags=["a", "b"])
    adv.add_todo("task2", tags=["b"])    
    res_or = adv.filter_by_tags(["b"], match_all=False)
    assert len(res_or) == 2
    res_and = adv.filter_by_tags(["a", "b"], match_all=True)
    assert len(res_and) == 1
