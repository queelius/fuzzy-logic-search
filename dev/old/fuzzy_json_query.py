from typing import List, Union, Callable, Any, Dict, Tuple
import re
import FuzzySet

class FuzzyJsonQuery:
    """
    A class that represents and evaluates fuzzy queries over JSON documents.
    Supports field constraints, predicates, logical operators, fuzzy modifiers,
    and wildcards for field paths using a simplified and uniform syntax.
    """

    # Define unary and n-ary operators
    unary_ops = {
        'very': lambda x: x ** 2,
        'somewhat': lambda x: x ** 0.5,
        'slightly': lambda x: x ** 0.1,
        'extremely': lambda x: x ** 3,
        'not': lambda x: 1.0 - x
    }

    nary_ops = {
        'and': min,
        'or': max
    }

    pred_ops = {
        '<': lambda x, y: x < y,
        '<=': lambda x, y: x <= y,
        '>': lambda x, y: x > y,
        '>=': lambda x, y: x >= y,
        '==': lambda x, y: x == y,
        '!=': lambda x, y: x != y,
        'matches': lambda x, y: re.match(y, x) is not None,
        'startswith': lambda x, y: x.startswith(y),
        'endswith': lambda x, y: x.endswith(y),
        'in': lambda x, y: x in y
    }

    reserved_ops = unary_ops.keys() + nary_ops.keys() + pred_ops.keys()

    def __init__(self, query: Union[str, List] = None):
        if isinstance(query, str):
            self.ast = self.parse(query)
        elif isinstance(query, list):
            self.ast = query
        elif query is None:
            self.ast = []
        else:
            raise TypeError("FuzzyJsonQuery must be initialized with a string or a list representing the AST.")

    def parse(self, query: str) -> Any:
        tokens = self.tokenize(query)
        ast = self.compile(tokens)
        return ast

    def tokenize(self, query: str) -> List[str]:
        """
        Tokenizes the input query string.

        Args:
            query (str): The query string.

        Returns:
            List[str]: A list of tokens.
        """
        pat = r'''
            \s*(?:
                (?P<NUMBER>[-+]?\d*\.\d+|\d+)             |  # Integer or decimal number
                (?P<STRING>"[^"]*"|'[^']*')               |  # Quoted string
                (?P<OPERATOR><=|>=|!=|==|<|>|=|matches|startswith|endswith|and|or|not|very|somewhat|slightly|extremely|in) |  # Operators
                (?P<LPAREN>\()                            |  # Left parenthesis
                (?P<RPAREN>\))                            |  # Right parenthesis
                (?P<WORD>\b\w+(\.\w+)*(\.\*\*?|\.\*\*?)?) |  # Word (includes field paths with wildcards)
                (?P<OTHER>.)                                 # Any other character
            )
        '''
        regex = re.compile(pat, re.IGNORECASE | re.VERBOSE)
        tokens = []
        for match in regex.finditer(query):
            kind = match.lastgroup
            value = match.group(kind)
            if kind == 'STRING':
                tokens.append(value.strip('"\''))
            elif kind == 'NUMBER':
                tokens.append(value)
            elif kind == 'WORD':
                tokens.append(value)
            elif kind == 'OPERATOR':
                tokens.append(value.lower())
            elif kind in ('LPAREN', 'RPAREN'):
                tokens.append(value)
            elif kind == 'OTHER':
                if value.strip():
                    tokens.append(value.strip())
        return tokens

    def compile(self, tokens: List[str]) -> List:
        """
        Compiles the tokenized query into an abstract syntax tree (AST).

        Args:
            tokens (List[str]): A list of tokens.

        Returns:
            List: The abstract syntax tree (AST) representation of the query. It
            is a nested list structure that can be evaluated against JSON documents.
            It is also valid JSON (but no dictionary objects).            
        """
        def _parse_expression(index: int) -> Tuple[Any, int]:
            if index >= len(tokens):
                raise ValueError("Unexpected end of query.")

            token = tokens[index]

            if token == '(':
                index += 1
                if index >= len(tokens):
                    raise ValueError("Unexpected end of query after '('.")
                op = tokens[index]
                index += 1

                if op in self.reserved_ops:
                    # Operator expression
                    operands = []
                    if op in self.unary_ops:
                        # Unary operator
                        expr, index = _parse_expression(index)
                        operands.append(expr)
                    else:
                        # N-ary operator
                        while index < len(tokens) and tokens[index] != ')':
                            expr, index = _parse_expression(index)
                            operands.append(expr)
                    if index >= len(tokens) or tokens[index] != ')':
                        raise ValueError("Missing closing parenthesis.")
                    index += 1  # Skip ')'
                    return [op] + operands, index
                else:
                    # Field expression
                    field_path = op
                    expr, index = _parse_expression(index)
                    if index >= len(tokens) or tokens[index] != ')':
                        raise ValueError("Missing closing parenthesis after field expression.")
                    index += 1  # Skip ')'
                    return [field_path, expr], index
            elif token in self.reserved_ops:
                # Unary operator without parentheses
                if token in self.unary_ops:
                    expr, index = _parse_expression(index + 1)
                    return [token, expr], index
                else:
                    raise ValueError(f"Operator '{token}' must be within parentheses.")
            else:
                # Operand
                return token, index + 1

        ast, next_index = _parse_expression(0)
        if next_index != len(tokens):
            raise ValueError("Unprocessed tokens remaining.")
        return ast

    def eval(self, docs: List[Dict], membership_fn: callable) -> FuzzySet:
        """
        Evaluates the fuzzy query against a list of JSON documents.

        Args:
            docs (List[Dict]): A list of JSON documents.
            scoring_function (callable): A function to compute the degree of membership.

        Returns:
            FuzzySet: A FuzzySet containing the degrees of membership for each document.
        """

        def _eval(query_part: Any, doc: Dict) -> float:
            if isinstance(query_part, str):
                # default 'in' logic
                values = flatten_json_values(doc)
                degrees = [eval_pred('in', query_part, value, membership_fn) for value in values]
                return max(degrees, default=0.0)
            elif isinstance(query_part, list):
                op = query_part[0]
                if op in self.unary_ops:
                    operand_value = _eval(query_part[1], doc)
                    return self.unary_ops[op](operand_value)
                elif op in self.nary_ops:
                    operand_values = [_eval(operand, doc) for operand in query_part[1:]]
                    return self.nary_ops[op](operand_values)
                elif op in self.pred_ops:
                    # Comparison operator
                    field_value = get_values_by_field_path(doc, query_part[1])
                    target_value = query_part[2]
                    degrees = [eval_pred(op, fv, target_value, membership_fn) for fv in field_value]
                    return max(degrees, default=0.0)
                else:
                    # Field expression
                    field_path = op
                    expression = query_part[1]
                    field_values = get_values_by_field_path(doc, field_path)
                    degrees = [_eval(expression, {field_path: value}) for value in field_values]
                    return max(degrees, default=0.0)
            else:
                raise TypeError("Invalid query part.")

        degrees_of_membership = [_eval(self.ast, doc) for doc in docs]
        return FuzzySet(degrees_of_membership)

    def __str__(self) -> str:
        """
        Converts the internal AST representation back to a query string.

        Returns:
            str: The string representation of the query.
        """
        def _build(tokens: Any) -> str:
            if isinstance(tokens, str):
                return tokens
            elif isinstance(tokens, list):
                op = tokens[0]
                if op in self.unary_ops or op in self.nary_ops or op in self.pred_ops:
                    operand_strs = ' '.join(_build(operand) for operand in tokens[1:])
                    return f"({op} {operand_strs})"
                else:
                    # Field expression
                    field_path = op
                    expr_str = _build(tokens[1])
                    return f"({field_path} {expr_str})"
            else:
                return str(tokens)
        return _build(self.ast)

    def __repr__(self) -> str:
        return f"FuzzyJsonQuery({self.ast})"

# Helper functions

def flatten_json_values(obj: Any) -> List[Any]:
    values = []
    if isinstance(obj, dict):
        for v in obj.values():
            values.extend(flatten_json_values(v))
    elif isinstance(obj, list):
        for item in obj:
            values.extend(flatten_json_values(item))
    else:
        values.append(obj)
    return values

def get_values_by_field_path(obj: Any, field_path: str) -> List[Any]:
    """
    Retrieves values from the JSON object based on the field path,
    supporting wildcards '*' and '**'.

    Args:
        obj (Any): The JSON object.
        field_path (str): The field path string.

    Returns:
        List[Any]: A list of values matching the field path.
    """
    def recursive_get(obj, fields):
        if not fields:
            return [obj]
        field = fields[0]
        rest = fields[1:]
        results = []
        if field == '**':
            # Match any descendant at any depth
            if isinstance(obj, dict):
                for key, value in obj.items():
                    results.extend(recursive_get(value, rest))
                    results.extend(recursive_get(value, fields))
            elif isinstance(obj, list):
                for item in obj:
                    results.extend(recursive_get(item, rest))
                    results.extend(recursive_get(item, fields))
        elif field == '*':
            # Match any immediate child
            if isinstance(obj, dict):
                for key, value in obj.items():
                    results.extend(recursive_get(value, rest))
            elif isinstance(obj, list):
                for item in obj:
                    results.extend(recursive_get(item, rest))
        else:
            # Match specific field
            if isinstance(obj, dict) and field in obj:
                results.extend(recursive_get(obj[field], rest))
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, dict) and field in item:
                        results.extend(recursive_get(item[field], rest))
        return results

    fields = field_path.split('.')
    return recursive_get(obj, fields)

def eval_pred(operator: str,
              field_value: Any,
              target_value: Any,
              membership_fn: callable) -> float:
    
    if field_value is None:
        return 0.0

    return membership_fn(field_value, target_value, operator)

