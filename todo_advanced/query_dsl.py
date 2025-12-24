"""
Query DSL (Domain-Specific Language) for advanced task filtering.

Supports expressions like: tag:work AND (urgent OR personal) AND NOT archived
"""

import re
from typing import List, Dict, Callable, Any
from enum import Enum


class TokenType(Enum):
    """Token types for DSL lexer."""
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    TAG = "TAG"
    FIELD = "FIELD"
    COMPARISON = "COMPARISON"
    STRING = "STRING"
    EOF = "EOF"


class Token:
    """Represents a token in the DSL."""

    def __init__(self, type_: TokenType, value: Any):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"


class Lexer:
    """Tokenizes DSL query strings."""

    def __init__(self, query: str):
        self.query = query
        self.pos = 0
        self.current_char = self.query[0] if query else None

    def advance(self):
        """Move to next character."""
        self.pos += 1
        self.current_char = self.query[self.pos] if self.pos < len(self.query) else None

    def peek(self, offset=1):
        """Look ahead without advancing."""
        peek_pos = self.pos + offset
        return self.query[peek_pos] if peek_pos < len(self.query) else None

    def skip_whitespace(self):
        """Skip whitespace characters."""
        while self.current_char and self.current_char.isspace():
            self.advance()

    def read_string(self, quote_char):
        """Read a quoted string."""
        result = ""
        self.advance()  # Skip opening quote
        while self.current_char and self.current_char != quote_char:
            if self.current_char == "\\":
                self.advance()
                if self.current_char:
                    result += self.current_char
                    self.advance()
            else:
                result += self.current_char
                self.advance()
        if self.current_char == quote_char:
            self.advance()  # Skip closing quote
        return result

    def read_identifier(self):
        """Read an identifier (tag name, keyword, etc.)."""
        result = ""
        while self.current_char and (self.current_char.isalnum() or self.current_char in "_:-"):
            result += self.current_char
            self.advance()
        return result

    def tokenize(self) -> List[Token]:
        """Tokenize the entire query."""
        tokens = []

        while self.current_char:
            self.skip_whitespace()

            if not self.current_char:
                break

            # Parentheses
            if self.current_char == "(":
                tokens.append(Token(TokenType.LPAREN, "("))
                self.advance()
            elif self.current_char == ")":
                tokens.append(Token(TokenType.RPAREN, ")"))
                self.advance()

            # Quoted strings
            elif self.current_char in ('"', "'"):
                quote = self.current_char
                value = self.read_string(quote)
                tokens.append(Token(TokenType.STRING, value))

            # Identifiers and keywords
            elif self.current_char.isalpha() or self.current_char == "_":
                ident = self.read_identifier()
                upper = ident.upper()

                if upper == "AND":
                    tokens.append(Token(TokenType.AND, "AND"))
                elif upper == "OR":
                    tokens.append(Token(TokenType.OR, "OR"))
                elif upper == "NOT":
                    tokens.append(Token(TokenType.NOT, "NOT"))
                elif ":" in ident:
                    # tag:value or field:value syntax
                    parts = ident.split(":", 1)
                    tokens.append(Token(TokenType.TAG, ident))
                else:
                    # Plain tag name
                    tokens.append(Token(TokenType.TAG, ident))

            # Comparison operators
            elif self.current_char in "=<>!":
                op = self.current_char
                self.advance()
                if self.current_char == "=":
                    op += self.current_char
                    self.advance()
                tokens.append(Token(TokenType.COMPARISON, op))

            else:
                self.advance()

        tokens.append(Token(TokenType.EOF, None))
        return tokens


class ASTNode:
    """Base class for AST nodes."""
    pass


class AndNode(ASTNode):
    """Represents AND operation."""
    def __init__(self, left, right):
        self.left = left
        self.right = right


class OrNode(ASTNode):
    """Represents OR operation."""
    def __init__(self, left, right):
        self.left = left
        self.right = right


class NotNode(ASTNode):
    """Represents NOT operation."""
    def __init__(self, expr):
        self.expr = expr


class TagNode(ASTNode):
    """Represents a tag condition."""
    def __init__(self, tag_name: str):
        self.tag_name = tag_name


class Parser:
    """Parses tokenized DSL into an AST."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current_token(self) -> Token:
        """Get current token."""
        return self.tokens[self.pos]

    def advance(self):
        """Move to next token."""
        self.pos += 1

    def parse(self) -> ASTNode:
        """Parse tokens into AST."""
        return self.parse_or()

    def parse_or(self) -> ASTNode:
        """Parse OR expressions (lowest precedence)."""
        left = self.parse_and()

        while self.current_token().type == TokenType.OR:
            self.advance()
            right = self.parse_and()
            left = OrNode(left, right)

        return left

    def parse_and(self) -> ASTNode:
        """Parse AND expressions."""
        left = self.parse_not()

        while self.current_token().type == TokenType.AND:
            self.advance()
            right = self.parse_not()
            left = AndNode(left, right)

        return left

    def parse_not(self) -> ASTNode:
        """Parse NOT expressions."""
        if self.current_token().type == TokenType.NOT:
            self.advance()
            expr = self.parse_not()
            return NotNode(expr)

        return self.parse_atom()

    def parse_atom(self) -> ASTNode:
        """Parse atomic expressions (tags or parenthesized expressions)."""
        if self.current_token().type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_or()
            if self.current_token().type == TokenType.RPAREN:
                self.advance()
            return expr

        if self.current_token().type == TokenType.TAG:
            tag = self.current_token().value
            self.advance()
            return TagNode(tag)

        raise SyntaxError(f"Unexpected token: {self.current_token()}")


class QueryExecutor:
    """Executes a parsed query AST against tasks."""

    def __init__(self, tasks: List[Dict]):
        self.tasks = tasks

    def evaluate(self, node: ASTNode, task: Dict) -> bool:
        """Evaluate an AST node against a task."""
        if isinstance(node, TagNode):
            return self._evaluate_tag(node.tag_name, task)
        elif isinstance(node, AndNode):
            return self.evaluate(node.left, task) and self.evaluate(node.right, task)
        elif isinstance(node, OrNode):
            return self.evaluate(node.left, task) or self.evaluate(node.right, task)
        elif isinstance(node, NotNode):
            return not self.evaluate(node.expr, task)
        else:
            raise ValueError(f"Unknown node type: {type(node)}")

    def _evaluate_tag(self, tag_spec: str, task: Dict) -> bool:
        """Evaluate a tag specification against a task."""
        task_tags = task.get("tags", [])

        # Handle tag:value syntax
        if ":" in tag_spec:
            key, value = tag_spec.split(":", 1)
            if key.lower() == "tag":
                return value in task_tags
            elif key.lower() == "completed":
                return str(task.get("completed", False)).lower() == value.lower()
            elif key.lower() == "task":
                return value.lower() in task.get("task", "").lower()
        else:
            # Plain tag name
            return tag_spec in task_tags

        return False

    def execute(self, node: ASTNode) -> List[Dict]:
        """Execute query against all tasks."""
        return [task for task in self.tasks if self.evaluate(node, task)]


class QueryDSL:
    """High-level DSL query interface."""

    @staticmethod
    def parse(query: str) -> ASTNode:
        """Parse a query string into an AST."""
        lexer = Lexer(query)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        return parser.parse()

    @staticmethod
    def execute(query: str, tasks: List[Dict]) -> List[Dict]:
        """Execute a DSL query against tasks."""
        try:
            ast = QueryDSL.parse(query)
            executor = QueryExecutor(tasks)
            return executor.execute(ast)
        except Exception as e:
            raise ValueError(f"Query execution failed: {e}")
