"""Tests for DSL query engine."""

import unittest

from todo_advanced.query_dsl import (
    Lexer, Parser, QueryDSL, TokenType, QueryExecutor
)


class TestLexer(unittest.TestCase):
    """Test DSL lexer."""

    def test_tokenize_simple_tag(self):
        """Test tokenizing simple tag."""
        lexer = Lexer("work")
        tokens = lexer.tokenize()

        self.assertEqual(len(tokens), 2)  # TAG + EOF
        self.assertEqual(tokens[0].type, TokenType.TAG)
        self.assertEqual(tokens[0].value, "work")

    def test_tokenize_with_operators(self):
        """Test tokenizing with operators."""
        lexer = Lexer("work AND urgent")
        tokens = lexer.tokenize()

        types = [t.type for t in tokens]
        self.assertIn(TokenType.TAG, types)
        self.assertIn(TokenType.AND, types)

    def test_tokenize_parentheses(self):
        """Test tokenizing parentheses."""
        lexer = Lexer("(work OR personal)")
        tokens = lexer.tokenize()

        self.assertEqual(tokens[0].type, TokenType.LPAREN)
        self.assertEqual(tokens[-2].type, TokenType.RPAREN)

    def test_tokenize_not_operator(self):
        """Test tokenizing NOT operator."""
        lexer = Lexer("NOT completed")
        tokens = lexer.tokenize()

        self.assertEqual(tokens[0].type, TokenType.NOT)

    def test_tokenize_tag_with_value(self):
        """Test tokenizing tag:value syntax."""
        lexer = Lexer("tag:work")
        tokens = lexer.tokenize()

        self.assertEqual(tokens[0].type, TokenType.TAG)
        self.assertEqual(tokens[0].value, "tag:work")


class TestParser(unittest.TestCase):
    """Test DSL parser."""

    def test_parse_simple_tag(self):
        """Test parsing simple tag."""
        query = QueryDSL.parse("work")
        self.assertIsNotNone(query)

    def test_parse_and_expression(self):
        """Test parsing AND expression."""
        query = QueryDSL.parse("work AND urgent")
        self.assertIsNotNone(query)

    def test_parse_or_expression(self):
        """Test parsing OR expression."""
        query = QueryDSL.parse("work OR personal")
        self.assertIsNotNone(query)

    def test_parse_complex_expression(self):
        """Test parsing complex expression."""
        query = QueryDSL.parse("(tag:work OR tag:office) AND NOT archived")
        self.assertIsNotNone(query)

    def test_parse_with_parentheses(self):
        """Test parsing with parentheses."""
        query = QueryDSL.parse("(work OR urgent) AND personal")
        self.assertIsNotNone(query)


class TestQueryExecutor(unittest.TestCase):
    """Test query executor."""

    def setUp(self):
        """Set up test tasks."""
        self.tasks = [
            {
                "id": 1,
                "task": "Finish report",
                "completed": False,
                "tags": ["work", "urgent"]
            },
            {
                "id": 2,
                "task": "Buy groceries",
                "completed": False,
                "tags": ["shopping", "personal"]
            },
            {
                "id": 3,
                "task": "Call mom",
                "completed": True,
                "tags": ["personal"]
            },
        ]

    def test_execute_simple_tag_query(self):
        """Test executing simple tag query."""
        results = QueryDSL.execute("work", self.tasks)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["task"], "Finish report")

    def test_execute_and_query(self):
        """Test executing AND query."""
        results = QueryDSL.execute("work AND urgent", self.tasks)
        self.assertEqual(len(results), 1)

    def test_execute_or_query(self):
        """Test executing OR query."""
        results = QueryDSL.execute("work OR shopping", self.tasks)
        self.assertEqual(len(results), 2)

    def test_execute_not_query(self):
        """Test executing NOT query."""
        results = QueryDSL.execute("NOT work", self.tasks)
        self.assertEqual(len(results), 2)

    def test_execute_tag_value_query(self):
        """Test executing tag:value query."""
        results = QueryDSL.execute("tag:work", self.tasks)
        self.assertEqual(len(results), 1)

    def test_execute_completed_query(self):
        """Test executing completed status query."""
        results = QueryDSL.execute("completed:true", self.tasks)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["completed"])

    def test_execute_complex_query(self):
        """Test executing complex query."""
        results = QueryDSL.execute("(tag:work OR tag:shopping) AND NOT completed:true", self.tasks)
        self.assertEqual(len(results), 2)
        self.assertFalse(any(t["completed"] for t in results))


if __name__ == "__main__":
    unittest.main()
