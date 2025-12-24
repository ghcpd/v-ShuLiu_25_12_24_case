"""A minimal DSL for boolean tag queries.

Supports expressions like:
  tag:work AND (urgent OR personal) AND NOT archived

This module tokenizes, parses into an AST, and evaluates against a list of
task dicts (as returned by storage.list_tasks()). The operator set is
extensible by adding functions to OP_HANDLERS.
"""
import re
from typing import List, Any, Dict

TOKEN_RE = re.compile(r"\s*(\(|\)|AND|OR|NOT|tag:[A-Za-z0-9_\-]+|[A-Za-z0-9_\-]+)\s*", re.IGNORECASE)


class ParseError(Exception):
    pass


def tokenize(expr: str) -> List[str]:
    tokens = [t for t in TOKEN_RE.findall(expr) if t.strip()]
    # normalize
    return [t.upper() if t in ("AND", "OR", "NOT") else t for t in tokens]


# Simple recursive-descent parser

def parse(tokens: List[str]) -> Any:
    pos = 0

    def parse_primary():
        nonlocal pos
        if pos >= len(tokens):
            raise ParseError("unexpected end")
        tok = tokens[pos]
        if tok == "(":
            pos += 1
            node = parse_expr()
            if pos >= len(tokens) or tokens[pos] != ")":
                raise ParseError("missing )")
            pos += 1
            return node
        elif tok == "NOT":
            pos += 1
            return ("NOT", parse_primary())
        elif tok.lower().startswith("tag:"):
            pos += 1
            return ("TAG", tok.split(":", 1)[1])
        elif re.match(r"^[A-Za-z0-9_\-]+$", tok):
            # treat bare identifier as a tag name for convenience
            pos += 1
            return ("TAG", tok)
        else:
            raise ParseError(f"unexpected token: {tok}")

    def parse_and():
        nonlocal pos
        left = parse_primary()
        while pos < len(tokens) and tokens[pos] == "AND":
            pos += 1
            right = parse_primary()
            left = ("AND", left, right)
        return left

    def parse_expr():
        nonlocal pos
        left = parse_and()
        while pos < len(tokens) and tokens[pos] == "OR":
            pos += 1
            right = parse_and()
            left = ("OR", left, right)
        return left

    node = parse_expr()
    if pos != len(tokens):
        raise ParseError("extra tokens")
    return node


def eval_ast(ast: Any, tasks: List[Dict]) -> List[Dict]:
    """Evaluate AST against provided tasks (each task must include 'tags')."""
    if ast[0] == "TAG":
        tagname = ast[1]
        return [t for t in tasks if tagname in (t.get("tags") or [])]
    if ast[0] == "NOT":
        sub = eval_ast(ast[1], tasks)
        sub_ids = {id(t) for t in sub}
        return [t for t in tasks if id(t) not in sub_ids]
    if ast[0] == "AND":
        left = eval_ast(ast[1], tasks)
        right = eval_ast(ast[2], tasks)
        left_ids = {id(t) for t in left}
        return [t for t in right if id(t) in left_ids]
    if ast[0] == "OR":
        a = eval_ast(ast[1], tasks)
        b = eval_ast(ast[2], tasks)
        seen = set()
        out = []
        for t in a + b:
            tid = id(t)
            if tid not in seen:
                seen.add(tid)
                out.append(t)
        return out
    raise ParseError("unknown ast node")


def run_query(expr: str, tasks: List[Dict]) -> List[Dict]:
    tokens = tokenize(expr)
    ast = parse(tokens)
    return eval_ast(ast, tasks)
