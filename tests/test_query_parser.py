"""
Tests for the Lisp-like query parser and formatter.
"""

import unittest
from fuzzy_logic_search.query_parser import (
    FuzzyQueryParser,
    FuzzyQueryFormatter,
    parse_fuzzy_query,
    format_fuzzy_query,
    validate_query_syntax,
    convert_field_shortcuts,
    FuzzyQueryBuilder
)


class TestFuzzyQueryParser(unittest.TestCase):
    """Test the Lisp query parser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = FuzzyQueryParser()
    
    def test_parse_simple_comparison(self):
        """Test parsing simple comparisons."""
        # Greater than or equal
        result = self.parser.parse("(>= :age 25)")
        self.assertEqual(result, [">=", ":age", 25])
        
        # Equality
        result = self.parser.parse("(== :name \"Alice\")")
        self.assertEqual(result, ["==", ":name", "Alice"])
        
        # Less than
        result = self.parser.parse("(< :score 100)")
        self.assertEqual(result, ["<", ":score", 100])
    
    def test_parse_logical_operations(self):
        """Test parsing logical operations."""
        # AND
        result = self.parser.parse("(and (>= :age 25) (< :age 65))")
        self.assertEqual(result, ["and", [">=", ":age", 25], ["<", ":age", 65]])
        
        # OR
        result = self.parser.parse("(or (== :status \"active\") (== :status \"pending\"))")
        self.assertEqual(result, ["or", ["==", ":status", "active"], ["==", ":status", "pending"]])
        
        # NOT
        result = self.parser.parse("(not (== :deleted true))")
        self.assertEqual(result, ["not", ["==", ":deleted", True]])
    
    def test_parse_fuzzy_modifiers(self):
        """Test parsing fuzzy modifiers."""
        # Very
        result = self.parser.parse("(very (>= :score 80))")
        self.assertEqual(result, ["very", [">=", ":score", 80]])
        
        # Somewhat
        result = self.parser.parse("(somewhat (contains? :description \"important\"))")
        self.assertEqual(result, ["somewhat", ["contains?", ":description", "important"]])
        
        # Nested modifiers
        result = self.parser.parse("(very (somewhat (>= :score 80)))")
        self.assertEqual(result, ["very", ["somewhat", [">=", ":score", 80]]])
    
    def test_parse_string_operations(self):
        """Test parsing string operations."""
        # Contains
        result = self.parser.parse("(contains? :name smith)")
        self.assertEqual(result, ["contains?", ":name", "smith"])
        
        # Starts with
        result = self.parser.parse("(starts-with? :email \"admin@\")")
        self.assertEqual(result, ["starts-with?", ":email", "admin@"])
        
        # Regex
        result = self.parser.parse("(regex? :phone \"^\\d{3}-\\d{4}$\")")
        self.assertEqual(result, ["regex?", ":phone", "^\\d{3}-\\d{4}$"])
    
    def test_parse_field_accessors(self):
        """Test parsing field accessors."""
        # Colon prefix
        result = self.parser.parse("(exists? :username)")
        self.assertEqual(result, ["exists?", ":username"])
        
        # At-sign prefix for paths
        result = self.parser.parse("(>= @user.profile.age 18)")
        self.assertEqual(result, [">=", "@user.profile.age", 18])
        
        # Dotted field names
        result = self.parser.parse("(== :user.name \"Bob\")")
        self.assertEqual(result, ["==", ":user.name", "Bob"])
    
    def test_parse_complex_queries(self):
        """Test parsing complex nested queries."""
        query = """
        (and 
            (>= :age 25)
            (or 
                (== :department "engineering")
                (== :department "research"))
            (very (contains? :skills "python")))
        """
        result = self.parser.parse(query)
        
        expected = [
            "and",
            [">=", ":age", 25],
            ["or",
                ["==", ":department", "engineering"],
                ["==", ":department", "research"]
            ],
            ["very", ["contains?", ":skills", "python"]]
        ]
        self.assertEqual(result, expected)
    
    def test_parse_numbers(self):
        """Test parsing different number formats."""
        # Integer
        result = self.parser.parse("(== :count 42)")
        self.assertEqual(result, ["==", ":count", 42])
        
        # Float
        result = self.parser.parse("(>= :score 85.5)")
        self.assertEqual(result, [">=", ":score", 85.5])
        
        # Negative
        result = self.parser.parse("(< :balance -100)")
        self.assertEqual(result, ["<", ":balance", -100])
    
    def test_parse_booleans_and_null(self):
        """Test parsing boolean and null values."""
        # Boolean true
        result = self.parser.parse("(== :active true)")
        self.assertEqual(result, ["==", ":active", True])
        
        # Boolean false
        result = self.parser.parse("(== :deleted false)")
        self.assertEqual(result, ["==", ":deleted", False])
        
        # Null/nil
        result = self.parser.parse("(== :parent null)")
        self.assertEqual(result, ["==", ":parent", None])
    
    def test_parse_errors(self):
        """Test parsing errors."""
        # Missing closing paren
        with self.assertRaises(SyntaxError):
            self.parser.parse("(>= :age 25")
        
        # Extra closing paren
        with self.assertRaises(SyntaxError):
            self.parser.parse("(>= :age 25))")
        
        # Empty input
        result = self.parser.parse("")
        self.assertEqual(result, [])


class TestFuzzyQueryFormatter(unittest.TestCase):
    """Test the query formatter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.formatter = FuzzyQueryFormatter()
    
    def test_format_simple_comparison(self):
        """Test formatting simple comparisons."""
        # Greater than or equal
        result = self.formatter.format([">=", ":age", 25])
        self.assertEqual(result, "(>= :age 25)")
        
        # String value
        result = self.formatter.format(["==", ":name", "Alice"])
        self.assertEqual(result, "(== :name Alice)")
        
        # Quoted string (with space)
        result = self.formatter.format(["==", ":name", "Alice Smith"])
        self.assertEqual(result, "(== :name \"Alice Smith\")")
    
    def test_format_logical_operations(self):
        """Test formatting logical operations."""
        # AND
        ast = ["and", [">=", ":age", 25], ["<", ":age", 65]]
        result = self.formatter.format(ast)
        self.assertEqual(result, "(and (>= :age 25) (< :age 65))")
        
        # OR
        ast = ["or", ["==", ":status", "active"], ["==", ":status", "pending"]]
        result = self.formatter.format(ast)
        self.assertEqual(result, "(or (== :status active) (== :status pending))")
    
    def test_format_modifiers(self):
        """Test formatting fuzzy modifiers."""
        # Very
        ast = ["very", [">=", ":score", 80]]
        result = self.formatter.format(ast)
        self.assertEqual(result, "(very (>= :score 80))")
        
        # Nested modifiers
        ast = ["very", ["somewhat", [">=", ":score", 80]]]
        result = self.formatter.format(ast)
        self.assertEqual(result, "(very (somewhat (>= :score 80)))")
    
    def test_format_pretty_printing(self):
        """Test pretty printing with indentation."""
        ast = [
            "and",
            [">=", ":age", 25],
            ["or",
                ["==", ":department", "engineering"],
                ["==", ":department", "research"]
            ],
            ["very", ["contains?", ":skills", "python"]]
        ]
        
        result = self.formatter.format(ast, pretty=True)
        
        # Check that it's multi-line
        self.assertIn("\n", result)
        # Check indentation
        self.assertIn("  ", result)
    
    def test_format_special_values(self):
        """Test formatting special values."""
        # Boolean
        result = self.formatter.format(["==", ":active", True])
        self.assertEqual(result, "(== :active true)")
        
        # Null
        result = self.formatter.format(["==", ":parent", None])
        self.assertEqual(result, "(== :parent nil)")
        
        # Empty list
        result = self.formatter.format([])
        self.assertEqual(result, "()")
    
    def test_roundtrip_conversion(self):
        """Test that parse->format->parse preserves structure."""
        queries = [
            "(>= :age 25)",
            "(and (>= :age 25) (< :age 65))",
            "(very (contains? :name \"smith\"))",
            "(or (== :status active) (== :status pending))",
        ]
        
        parser = FuzzyQueryParser()
        
        for original in queries:
            # Parse to AST
            ast = parser.parse(original)
            # Format back to string
            formatted = self.formatter.format(ast)
            # Parse again
            ast2 = parser.parse(formatted)
            
            # ASTs should be identical
            self.assertEqual(ast, ast2)


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions."""
    
    def test_parse_fuzzy_query(self):
        """Test the convenience parse function."""
        result = parse_fuzzy_query("(>= :age 25)")
        self.assertEqual(result, [">=", ":age", 25])
    
    def test_format_fuzzy_query(self):
        """Test the convenience format function."""
        result = format_fuzzy_query([">=", ":age", 25])
        self.assertEqual(result, "(>= :age 25)")
    
    def test_validate_query_syntax(self):
        """Test query validation."""
        # Valid query
        valid, error = validate_query_syntax("(>= :age 25)")
        self.assertTrue(valid)
        self.assertEqual(error, "")
        
        # Invalid query
        valid, error = validate_query_syntax("(>= :age 25")
        self.assertFalse(valid)
        self.assertIn("Missing closing parenthesis", error)
    
    def test_convert_field_shortcuts(self):
        """Test field shortcut conversion."""
        # Colon shortcut
        result = convert_field_shortcuts(":name")
        self.assertEqual(result, ["field", "name"])
        
        # At-sign shortcut
        result = convert_field_shortcuts("@user.profile.age")
        self.assertEqual(result, ["path", "user.profile.age"])
        
        # Nested in list
        result = convert_field_shortcuts([">=", ":age", 25])
        self.assertEqual(result, [">=", ["field", "age"], 25])
        
        # No conversion needed
        result = convert_field_shortcuts([">=", "age", 25])
        self.assertEqual(result, [">=", "age", 25])


class TestFuzzyQueryBuilder(unittest.TestCase):
    """Test the query builder API."""
    
    def test_simple_query(self):
        """Test building a simple query."""
        q = FuzzyQueryBuilder()
        query = q.gte("age", 25).build()
        
        self.assertEqual(query, [">=", ":age", 25])
    
    def test_and_query(self):
        """Test building an AND query."""
        q = FuzzyQueryBuilder()
        query = (q
            .and_()
            .gte("age", 25)
            .lte("age", 65)
            .end()
            .build())
        
        self.assertEqual(query, ["and", [">=", ":age", 25], ["<=", ":age", 65]])
    
    def test_or_query(self):
        """Test building an OR query."""
        q = FuzzyQueryBuilder()
        query = (q
            .or_()
            .eq("status", "active")
            .eq("status", "pending")
            .end()
            .build())
        
        self.assertEqual(query, ["or", ["==", ":status", "active"], ["==", ":status", "pending"]])
    
    def test_modifier_query(self):
        """Test building queries with modifiers."""
        q = FuzzyQueryBuilder()
        query = q.gte("score", 80).very().build()
        
        # Note: modifier applies to last expression
        self.assertEqual(query[0], "very")
    
    def test_nested_query(self):
        """Test building nested queries."""
        q = FuzzyQueryBuilder()
        query = (q
            .and_()
            .gte("age", 25)
            .or_()
            .eq("department", "engineering")
            .eq("department", "research")
            .end()
            .end()
            .build())
        
        expected = [
            "and",
            [">=", ":age", 25],
            ["or", ["==", ":department", "engineering"], ["==", ":department", "research"]]
        ]
        self.assertEqual(query, expected)
    
    def test_string_operations(self):
        """Test string operation builders."""
        q = FuzzyQueryBuilder()
        query = q.contains("description", "important").build()
        
        self.assertEqual(query, ["contains?", ":description", "important"])
    
    def test_existence_check(self):
        """Test field existence check."""
        q = FuzzyQueryBuilder()
        query = q.exists("email").build()
        
        self.assertEqual(query, ["exists?", ":email"])


if __name__ == "__main__":
    unittest.main()