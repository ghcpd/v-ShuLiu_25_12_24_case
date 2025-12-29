from todo_advanced.plugins import discover_plugins


def test_discover_no_plugins():
    # In a clean env, no plugins should be found and no error raised
    assert isinstance(discover_plugins(), list)
