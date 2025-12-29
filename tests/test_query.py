import pytest

from todo_advanced_pkg import query
from todo_advanced_pkg import storage


def test_simple_tag_and_text_queries(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_FILE", tmp_path / "q.db")
    storage.initialize()
    storage.add_task("buy milk", ["personal"])
    storage.add_task("finish report", ["work", "urgent"])
    out = query.execute("tag:work AND (urgent OR personal)")
    assert len(out) == 1
    assert out[0]["task"] == "finish report"


def test_parser_errors():
    with pytest.raises(query.ParseError):
        query.tokenize("tag:")
