from todo_advanced_pkg.query import tokenize, parse, run_query


def test_tokenize_and_parse():
    expr = "tag:work AND (urgent OR personal) AND NOT archived"
    tokens = tokenize(expr)
    assert "tag:work" in tokens[0].lower()
    ast = parse(tokens)
    assert ast is not None


def test_run_query_basic():
    tasks = [
        {"task": "a", "tags": ["work", "urgent"]},
        {"task": "b", "tags": ["work"]},
        {"task": "c", "tags": ["personal"]},
    ]
    res = run_query("tag:work AND (tag:urgent OR tag:personal)", tasks)
    assert len(res) == 1
    assert res[0]["task"] == "a"

    res2 = run_query("tag:work OR tag:personal", tasks)
    assert len(res2) == 3
