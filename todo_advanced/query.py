"""Mini query language parser & evaluator (initial stub).

Supports expressions like: tag:work AND (urgent OR personal) AND NOT archived
This module provides a tokenizer and a parser that builds a simple AST; evaluation
will be provided against a storage-provided task/tag index.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Union, Optional


TOKEN_RE = re.compile(r"(AND|OR|NOT|\(|\)|tag:[A-Za-z0-9_\-]+|\S+)")


@dataclass
class Node:
    pass


@dataclass
class TagNode(Node):
    tag: str


@dataclass
class AndNode(Node):
    left: Node
    right: Node


@dataclass
class OrNode(Node):
    left: Node
    right: Node


@dataclass
class NotNode(Node):
    node: Node


class ParserError(Exception):
    pass


def tokenize(expr: str) -> List[str]:
    # Simpler tokenizer that preserves parentheses and operators reliably
    s = expr.replace("(", " ( ").replace(")", " ) ")
    return [tok for tok in s.split() if tok.strip()]


# Very small recursive-descent parser
class Parser:
    def __init__(self, tokens: List[str]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Optional[str]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def eat(self, expected: Optional[str] = None) -> str:
        t = self.peek()
        if t is None:
            raise ParserError("Unexpected end of input")
        if expected and t != expected:
            raise ParserError(f"Expected {expected} got {t}")
        self.pos += 1
        return t

    def parse(self) -> Node:
        node = self.parse_term()
        while self.peek() in ("AND", "OR"):
            op = self.eat()
            right = self.parse_term()
            if op == "AND":
                node = AndNode(node, right)
            else:
                node = OrNode(node, right)
        return node

    def parse_term(self) -> Node:
        t = self.peek()
        if t == "NOT":
            self.eat("NOT")
            return NotNode(self.parse_term())
        if t == "(":
            self.eat("(")
            node = self.parse()
            self.eat(")")
            return node
        # tag token or bareword
        tok = self.eat()
        if tok.startswith("tag:"):
            return TagNode(tok.split(":", 1)[1])
        else:
            # treat bare word as tag
            return TagNode(tok)


def parse_expression(expr: str) -> Node:
    tokens = tokenize(expr)
    p = Parser(tokens)
    node = p.parse()
    if p.peek() is not None:
        raise ParserError("Extra input after valid expression")
    return node


# Evaluation will be implemented to interact with storage. This is a stub here.
