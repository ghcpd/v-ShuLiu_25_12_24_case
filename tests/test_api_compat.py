import os
import tempfile
import shutil
from todo_advanced import add_todo, list_todos, filter_by_tags, add_tag_to_task, remove_tag_from_task, show_tag_stats, list_all_tags, complete_task


def test_basic_compatibility(tmp_path):
    # use a temporary DB file so tests are isolated
    db = tmp_path / "test.db"
    # create a local instance by importing module and replacing the _store
    import todo_advanced as ta
    ta._store = ta.AdvancedTodo(str(db))

    # behave like original API
    add_todo("task1", ["work"])
    add_todo("task2", ["home", "urgent"])
    todos = list_todos()
    assert len(todos) == 2

    # filter
    res = filter_by_tags(["work"])
    assert len(res) == 1

    # add/remove tags by index
    add_tag_to_task(0, "important")
    assert "important" in list_todos()[0]["tags"]
    remove_tag_from_task(0, "important")
    assert "important" not in list_todos()[0]["tags"]

    stats = show_tag_stats()
    assert stats.get("work", 0) >= 1
    tags = list_all_tags()
    assert "work" in tags

    # complete
    complete_task(0)
    assert list_todos()[0]["completed"] is True
