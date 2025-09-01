"""
Parser and formatter for Lisp-like fuzzy query syntax.

This module provides conversion between human-readable Lisp syntax and
the JSON-based AST format used internally.

Examples:
    Lisp syntax:  (and (>= :age 25) (very (contains? :name "smith")))
    JSON AST:     ["and", [">=", ":age", 25], ["very", ["contains?", ":name", "smith"]]]
    
    Field access shortcuts:
    :field-name  ->  Field access
    @field.path  ->  Nested field path
"""

import re
import json
from typing import Any, List, Union


class FuzzyQueryParser:
    """
    Parser for Lisp-like fuzzy query syntax.
    """
    
    def __init__(self):
        """Initialize the parser."""
        self.tokens = []
        self.current = 0
    
    def parse(self, query_string: str) -> List:
        """
        Parse a Lisp-like query string into JSON AST.
        
        Args:
            query_string: Query in Lisp syntax
            
        Returns:
            JSON-compatible AST (nested lists)
            
        Examples:
            >>> parser = FuzzyQueryParser()
            >>> parser.parse("(>= :age 25)")
            [">=", ":age", 25]
            >>> parser.parse("(and (>= :age 25) (contains? :name smith))")
            ["and", [">=", ":age", 25], ["contains?", ":name", "smith"]]
        """
        self.tokens = self._tokenize(query_string)
        self.current = 0
        
        if not self.tokens:
            return []
        
        result = self._parse_expression()
        
        # Ensure we consumed all tokens
        if self.current < len(self.tokens):
            raise SyntaxError(f"Unexpected tokens after expression: {self.tokens[self.current:]}")
        
        return result
    
    def _tokenize(self, query_string: str) -> List[str]:
        """
        Tokenize a query string.
        
        Args:
            query_string: Input string
            
        Returns:
            List of tokens
        """
        # Token patterns
        patterns = [
            r'\(',                    # Left paren
            r'\)',                    # Right paren
            r'"[^"]*"',              # Quoted string
            r"'[^']*'",              # Single-quoted string
            r':[a-zA-Z_][\w\-\.]*',  # Field accessor :field-name
            r'@[a-zA-Z_][\w\-\.]*',  # Path accessor @field.path
            r'-?\d+\.\d+',           # Float numbers (must come before int)
            r'-?\d+',                # Integer numbers
            r'[\w\-\?\!]+',          # Identifiers and operators
            r'[<>=]+',               # Comparison operators
        ]
        
        token_regex = '|'.join(f'({p})' for p in patterns)
        tokens = []
        
        for match in re.finditer(token_regex, query_string):
            token = match.group(0)
            if token:
                tokens.append(token)
        
        return tokens
    
    def _parse_expression(self) -> Any:
        """
        Parse a single expression (atom or list).
        
        Returns:
            Parsed expression
        """
        if self.current >= len(self.tokens):
            raise SyntaxError("Unexpected end of input")
        
        token = self.tokens[self.current]
        
        if token == '(':
            # Parse list expression
            return self._parse_list()
        else:
            # Parse atom
            return self._parse_atom()
    
    def _parse_list(self) -> List:
        """
        Parse a list expression (op arg1 arg2 ...).
        
        Returns:
            List representing the expression
        """
        # Consume opening paren
        if self.tokens[self.current] != '(':
            raise SyntaxError(f"Expected '(' but got {self.tokens[self.current]}")
        self.current += 1
        
        result = []
        
        # Parse elements until closing paren
        while self.current < len(self.tokens) and self.tokens[self.current] != ')':
            result.append(self._parse_expression())
        
        # Consume closing paren
        if self.current >= len(self.tokens):
            raise SyntaxError("Missing closing parenthesis")
        if self.tokens[self.current] != ')':
            raise SyntaxError(f"Expected ')' but got {self.tokens[self.current]}")
        self.current += 1
        
        return result
    
    def _parse_atom(self) -> Any:
        """
        Parse an atomic value (number, string, identifier).
        
        Returns:
            Parsed atomic value
        """
        if self.current >= len(self.tokens):
            raise SyntaxError("Unexpected end of input")
        
        token = self.tokens[self.current]
        self.current += 1
        
        # Quoted string
        if token.startswith('"') and token.endswith('"'):
            return token[1:-1]  # Remove quotes
        elif token.startswith("'") and token.endswith("'"):
            return token[1:-1]  # Remove quotes
        
        # Field accessor (:field-name)
        elif token.startswith(':'):
            return token  # Keep the : prefix
        
        # Path accessor (@field.path)
        elif token.startswith('@'):
            return token  # Keep the @ prefix
        
        # Number - try float first, then int
        elif re.match(r'^-?\d+\.\d+$', token):
            return float(token)
        elif re.match(r'^-?\d+$', token):
            return int(token)
        
        # Boolean
        elif token.lower() == 'true':
            return True
        elif token.lower() == 'false':
            return False
        
        # Null/nil
        elif token.lower() in ('null', 'nil'):
            return None
        
        # Operator or identifier
        else:
            return token


class FuzzyQueryFormatter:
    """
    Formatter to convert JSON AST to Lisp-like syntax.
    """
    
    def format(self, ast: Any, pretty: bool = False, indent: int = 0) -> str:
        """
        Format a JSON AST as Lisp-like syntax.
        
        Args:
            ast: JSON AST (nested lists)
            pretty: If True, format with indentation
            indent: Current indentation level (for pretty printing)
            
        Returns:
            Lisp-syntax string
            
        Examples:
            >>> formatter = FuzzyQueryFormatter()
            >>> formatter.format([">=", ":age", 25])
            '(>= :age 25)'
            >>> formatter.format(["and", [">=", ":age", 25], ["contains?", ":name", "smith"]])
            '(and (>= :age 25) (contains? :name smith))'
        """
        if ast is None:
            return "nil"
        elif isinstance(ast, bool):
            return "true" if ast else "false"
        elif isinstance(ast, (int, float)):
            return str(ast)
        elif isinstance(ast, str):
            # Check if it's a field/path accessor or operator
            if ast.startswith(':') or ast.startswith('@') or self._is_operator(ast):
                return ast
            # Check if string needs quoting
            elif ' ' in ast or any(c in ast for c in '()[]{}"\','):
                return f'"{ast}"'
            else:
                return ast
        elif isinstance(ast, list):
            if not ast:
                return "()"
            
            if pretty:
                # Pretty printing with indentation
                indent_str = "  " * indent
                next_indent_str = "  " * (indent + 1)
                
                # Check if it's a simple expression that fits on one line
                if self._is_simple_expr(ast):
                    elements = [self.format(e, pretty=False) for e in ast]
                    return f"({' '.join(elements)})"
                else:
                    # Multi-line formatting
                    lines = []
                    lines.append("(")
                    
                    # First element (operator) on same line
                    if ast:
                        lines[-1] += self.format(ast[0], pretty=False)
                    
                    # Rest of elements indented
                    for elem in ast[1:]:
                        formatted = self.format(elem, pretty=True, indent=indent+1)
                        lines.append(f"{next_indent_str}{formatted}")
                    
                    lines.append(f"{indent_str})")
                    return "\n".join(lines)
            else:
                # Compact formatting
                elements = [self.format(e, pretty=False) for e in ast]
                return f"({' '.join(elements)})"
        else:
            # Fallback to JSON for unknown types
            return json.dumps(ast)
    
    def _is_operator(self, s: str) -> bool:
        """Check if a string is an operator."""
        operators = {
            # Logical
            "and", "or", "not",
            # Comparison
            "==", "!=", ">", "<", ">=", "<=",
            "eq?", "neq?", "gt?", "lt?", "gte?", "lte?",
            # String
            "contains?", "starts-with?", "ends-with?", "regex?", "in?",
            # Fuzzy modifiers
            "very", "somewhat", "slightly", "extremely",
            # Field operations
            "field", "path", "exists?",
            # Quantifiers
            "all", "any", "none"
        }
        return s in operators
    
    def _is_simple_expr(self, ast: List) -> bool:
        """Check if expression is simple enough for one line."""
        if len(ast) <= 3:
            # Short expressions can go on one line
            return all(not isinstance(e, list) for e in ast)
        return False


# Convenience functions

def parse_fuzzy_query(query_string: str) -> List:
    """
    Parse a Lisp-like fuzzy query string to JSON AST.
    
    Args:
        query_string: Query in Lisp syntax
        
    Returns:
        JSON AST
        
    Examples:
        >>> parse_fuzzy_query("(>= :age 25)")
        [">=", ":age", 25]
        >>> parse_fuzzy_query("(very (contains? :name smith))")
        ["very", ["contains?", ":name", "smith"]]
    """
    parser = FuzzyQueryParser()
    return parser.parse(query_string)


def format_fuzzy_query(ast: Any, pretty: bool = False) -> str:
    """
    Format a JSON AST as Lisp-like syntax.
    
    Args:
        ast: JSON AST
        pretty: If True, use pretty printing with indentation
        
    Returns:
        Lisp syntax string
        
    Examples:
        >>> format_fuzzy_query([">=", ":age", 25])
        '(>= :age 25)'
        >>> format_fuzzy_query(["and", [">=", ":age", 25], ["contains?", ":name", "smith"]])
        '(and (>= :age 25) (contains? :name smith))'
    """
    formatter = FuzzyQueryFormatter()
    return formatter.format(ast, pretty=pretty)


def validate_query_syntax(query_string: str) -> tuple[bool, str]:
    """
    Validate a Lisp-like query string.
    
    Args:
        query_string: Query to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        parse_fuzzy_query(query_string)
        return (True, "")
    except SyntaxError as e:
        return (False, str(e))
    except Exception as e:
        return (False, f"Unexpected error: {e}")


def convert_field_shortcuts(ast: Any) -> Any:
    """
    Convert field shortcuts in AST to standard form.
    
    Converts:
        :field -> ["field", "field", ...]
        @path.to.field -> ["path", "path.to.field"]
        
    Args:
        ast: AST with possible shortcuts
        
    Returns:
        AST with expanded field operations
    """
    if isinstance(ast, str):
        if ast.startswith(':'):
            # Convert :field to field access
            return ["field", ast[1:]]
        elif ast.startswith('@'):
            # Convert @path to path access
            return ["path", ast[1:]]
        else:
            return ast
    elif isinstance(ast, list):
        return [convert_field_shortcuts(e) for e in ast]
    else:
        return ast


# Query builder helpers

class FuzzyQueryBuilder:
    """
    Fluent API for building fuzzy queries.
    
    Example:
        >>> q = FuzzyQueryBuilder()
        >>> query = (q
        ...     .and_()
        ...     .gte("age", 25)
        ...     .very()
        ...     .contains("name", "smith")
        ...     .end()
        ...     .build())
    """
    
    def __init__(self):
        """Initialize query builder."""
        self.stack = []
        self.current = []
    
    def and_(self) -> "FuzzyQueryBuilder":
        """Start an AND expression."""
        self.stack.append(self.current)
        self.current = ["and"]
        return self
    
    def or_(self) -> "FuzzyQueryBuilder":
        """Start an OR expression."""
        self.stack.append(self.current)
        self.current = ["or"]
        return self
    
    def not_(self) -> "FuzzyQueryBuilder":
        """Start a NOT expression."""
        self.stack.append(self.current)
        self.current = ["not"]
        return self
    
    def very(self) -> "FuzzyQueryBuilder":
        """Apply VERY modifier."""
        if self.current and isinstance(self.current, list):
            if len(self.current) == 1 and isinstance(self.current[0], list):
                # Single expression - wrap it
                self.current = ["very", self.current[0]]
            elif len(self.current) > 0 and self.current[0] not in ["and", "or", "not"]:
                # Not a logical operator, wrap the whole thing
                self.current = ["very", self.current]
            else:
                # Logical operator, apply to last item
                last = self.current.pop()
                self.current.append(["very", last])
        return self
    
    def somewhat(self) -> "FuzzyQueryBuilder":
        """Apply SOMEWHAT modifier."""
        if self.current and isinstance(self.current, list):
            if len(self.current) == 1 and isinstance(self.current[0], list):
                # Single expression - wrap it
                self.current = ["somewhat", self.current[0]]
            elif len(self.current) > 0 and self.current[0] not in ["and", "or", "not"]:
                # Not a logical operator, wrap the whole thing
                self.current = ["somewhat", self.current]
            else:
                # Logical operator, apply to last item
                last = self.current.pop()
                self.current.append(["somewhat", last])
        return self
    
    def eq(self, field: str, value: Any) -> "FuzzyQueryBuilder":
        """Add equality comparison."""
        expr = ["==", f":{field}" if not field.startswith(':') else field, value]
        if self.current and self.current[0] in ["and", "or"]:
            self.current.append(expr)
        else:
            self.current = expr
        return self
    
    def gte(self, field: str, value: Any) -> "FuzzyQueryBuilder":
        """Add >= comparison."""
        expr = [">=", f":{field}" if not field.startswith(':') else field, value]
        if self.current and self.current[0] in ["and", "or"]:
            self.current.append(expr)
        else:
            self.current = expr
        return self
    
    def lte(self, field: str, value: Any) -> "FuzzyQueryBuilder":
        """Add <= comparison."""
        expr = ["<=", f":{field}" if not field.startswith(':') else field, value]
        if self.current and self.current[0] in ["and", "or"]:
            self.current.append(expr)
        else:
            self.current = expr
        return self
    
    def contains(self, field: str, value: str) -> "FuzzyQueryBuilder":
        """Add contains check."""
        expr = ["contains?", f":{field}" if not field.startswith(':') else field, value]
        if self.current and self.current[0] in ["and", "or"]:
            self.current.append(expr)
        else:
            self.current = expr
        return self
    
    def exists(self, field: str) -> "FuzzyQueryBuilder":
        """Add field existence check."""
        expr = ["exists?", f":{field}" if not field.startswith(':') else field]
        if self.current and self.current[0] in ["and", "or"]:
            self.current.append(expr)
        else:
            self.current = expr
        return self
    
    def end(self) -> "FuzzyQueryBuilder":
        """End current expression."""
        if self.stack:
            parent = self.stack.pop()
            parent.append(self.current)
            self.current = parent
        return self
    
    def build(self) -> List:
        """Build the final query AST."""
        while self.stack:
            self.end()
        
        if len(self.current) == 1:
            return self.current[0]
        return self.current