from todo_advanced.query import parse_expression, TagNode, AndNode, OrNode, NotNode


def test_parser_basic():
    n = parse_expression("tag:work AND (urgent OR personal) AND NOT archived")
    assert isinstance(n, AndNode)
