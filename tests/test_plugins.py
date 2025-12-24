from todo_advanced_pkg.core import AdvancedTodo
import todo_plugins.plugin_sample as ps


def test_plugin_hooks(tmp_path):
    db = tmp_path / "pl.db"
    ps._reset()
    store = AdvancedTodo(str(db))
    store.add_task("t1", ["x"])
    # plugin_sample should have recorded calls
    state = ps._called_state()
    assert len(state["tasks"]) == 1
    assert "x" in state["tags"]
