from hypothesis import given, strategies as st
from todo_advanced_pkg import query

# small tokens to keep generated expressions manageable
simple_token = st.sampled_from(["AND", "OR", "NOT", "(", ")", "tag:work", "tag:home", "urgent", "foo"])

@given(st.lists(simple_token, min_size=1, max_size=12))
def test_tokenize_and_parse_roundtrip(tokens):
    s = " ".join(tokens)
    try:
        toks = query.tokenize(s)
        # parsing should either succeed or raise a controlled ParseError
        p = query.Parser(toks)
        p.parse()
    except query.ParseError:
        pass
