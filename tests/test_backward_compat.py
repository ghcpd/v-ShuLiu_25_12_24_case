import tempfile
import os
import shutil
import threading

import pytest

from todo_advanced_pkg import storage
import todo_advanced as ta


@pytest.fixture(autouse=True)
def isolate_db(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    monkeypatch.setattr(storage, "DB_FILE", db)
    # re-initialize
    storage.initialize()
    yield


def test_add_and_list_and_complete():
    ta.add_todo("x", ["a"])
    ta.add_todo("y")
    l = ta.list_todos()
    assert len(l) == 2
    assert l[0]["task"] == "x"
    ta.complete_task(0)
    assert ta.list_todos()[0]["completed"] is True


def test_tagging_and_stats_and_list_all_tags():
    ta.add_todo("t1", ["work"])
    ta.add_todo("t2", ["work", "urgent"])
    ta.add_tag_to_task(0, "urgent")
    assert set(ta.list_all_tags()) == {"urgent", "work"}
    stats = ta.show_tag_stats()
    assert stats.get("work", 0) >= 2


def test_filter_by_tags():
    ta.add_todo("a", ["x"])
    ta.add_todo("b", ["y", "x"])
    res_or = ta.filter_by_tags(["x"], match_all=False)
    assert len(res_or) == 2
    res_and = ta.filter_by_tags(["x", "y"], match_all=True)
    assert len(res_and) == 1
