"""Mini DSL for querying tasks.

Supported grammar (informal):
    expr := term ( (AND|OR) term )*
    term := NOT? factor
    factor := tag:NAME | text:"..." | ( expr )

Operators: AND, OR, NOT, parentheses. Tag operand: `tag:NAME`.
Also supports `NOT` and `-` prefix synonyms.

The engine returns scored tasks (higher score = better match).
"""
from __future__ import annotations
from typing import Any, List, Tuple
import re
from todo_advanced_pkg import storage


_TOKEN_RE = re.compile(r'\s*(?:(AND|OR|NOT)|\(|\)|tag:([A-Za-z0-9_\-]+)|"([^"]+)"|([^\s()]+))', re.I)


class ParseError(Exception):
    pass


# --- Parser ---------------------------------------------------------------

def tokenize(s: str):
    # reject clearly malformed tag: tokens early
    if re.search(r"\btag:\s*(?:$|[()\s])", s, re.I):
        raise ParseError("malformed tag: token")
    pos = 0
    tokens = []
    while pos < len(s):
        m = _TOKEN_RE.match(s, pos)
        if not m:
            raise ParseError(f"cannot tokenize at: {s[pos:pos+20]!r}")
        tok_text = m.group(0).strip()
        pos = m.end()
        op, tag, text, word = m.group(1, 2, 3, 4)
        if op:
            tokens.append((op.upper(), op.upper()))
        elif tag:
            tokens.append(("TAG", tag))
        elif text:
            tokens.append(("TEXT", text))
        elif word:
            tokens.append(("TEXT", word))
        else:
            # parentheses were matched but not captured into groups — handle them
            if tok_text in ("(", ")"):
                tokens.append((tok_text, tok_text))
            else:
                raise ParseError(f"unexpected token: {tok_text!r}")
    tokens.append(("EOF", ""))
    return tokens


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0

    def peek(self):
        return self.tokens[self.i][0]

    def next(self):
        t = self.tokens[self.i]
        self.i += 1
        return t

    def parse(self):
        node = self.parse_or()
        if self.peek() != "EOF":
            raise ParseError("unexpected token after end")
        return node

    def parse_or(self):
        left = self.parse_and()
        while self.peek() == "OR":
            self.next()
            right = self.parse_and()
            left = ("OR", left, right)
        return left

    def parse_and(self):
        left = self.parse_not()
        while self.peek() in ("AND", "TEXT", "TAG", "("):
            if self.peek() == "AND":
                self.next()
            right = self.parse_not()
            left = ("AND", left, right)
        return left

    def parse_not(self):
        if self.peek() == "NOT":
            self.next()
            node = self.parse_atom()
            return ("NOT", node)
        return self.parse_atom()

    def parse_atom(self):
        if self.peek() == "(":
            self.next()
            node = self.parse_or()
            if self.peek() != ")":
                raise ParseError("expected )")
            self.next()
            return node
        t = self.next()
        if t[0] == "TAG":
            return ("TAG", t[1])
        if t[0] == "TEXT":
            return ("TEXT", t[1])
        raise ParseError(f"unexpected token {t}")


# --- Executor -------------------------------------------------------------

def _eval_node(node, task_row) -> Tuple[bool, int]:
    """Evaluate node against a single task_row.
    Return (matched, score).
    """
    typ = node[0]
    if typ == "TAG":
        name = node[1]
        matched = name in task_row.get("tags", [])
        return matched, 10 if matched else 0
    if typ == "TEXT":
        text = node[1].lower()
        in_text = text in task_row.get("task", "").lower()
        in_tags = any(text == t.lower() for t in task_row.get("tags", []))
        matched = in_text or in_tags
        # prefer tag-match score over plain text-match
        return matched, (8 if in_tags else 5) if matched else 0
    if typ == "AND":
        a_m, a_s = _eval_node(node[1], task_row)
        b_m, b_s = _eval_node(node[2], task_row)
        return (a_m and b_m), (a_s + b_s)
    if typ == "OR":
        a_m, a_s = _eval_node(node[1], task_row)
        b_m, b_s = _eval_node(node[2], task_row)
        if a_m and b_m:
            return True, (a_s + b_s)
        if a_m:
            return True, a_s
        if b_m:
            return True, b_s
        return False, 0
    if typ == "NOT":
        m, s = _eval_node(node[1], task_row)
        return (not m), 0
    raise RuntimeError("unknown node")


def execute(dsl: str, limit: int = 100) -> List[dict]:
    tokens = tokenize(dsl)
    p = Parser(tokens)
    tree = p.parse()
    tasks = storage.list_tasks()
    scored = []
    for t in tasks:
        m, s = _eval_node(tree, t)
        if m:
            scored.append((s, t))
    scored.sort(key=lambda x: -x[0])
    out = []
    for score, row in scored[:limit]:
        r = dict(row)
        r["score"] = score
        out.append(r)
    return out
