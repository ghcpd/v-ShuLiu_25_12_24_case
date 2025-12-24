"""A tiny example plugin used in tests.

Hooks implemented:
- on_task_added
- on_tag_added
"""
_called = {"tasks": [], "tags": []}


def on_task_added(task):
    _called["tasks"].append(task)


def on_tag_added(tag):
    _called["tags"].append(tag)


def _reset():
    _called["tasks"].clear()
    _called["tags"].clear()


def _called_state():
    return dict(_called)
