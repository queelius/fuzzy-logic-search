import re
import math
from typing import List, Union, Callable, Any, Dict
from ..src.algebraic_search.fuzzy_set import FuzzySet

class FuzzyJsonQuery:
    """
    A class that represents and evaluates fuzzy queries over JSON documents.
    Supports field constraints, predicates, logical operators, fuzzy modifiers,
    and wildcards for field paths.
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

    # Comparison and predicate operators
    comparison_operators = {'<', '<=', '>', '>=', '==', '!=', '=', 'contains', 'startswith', 'exists', 'contains_all', 'contains_any'}

    # List of all operators
    ops = list(unary_ops.keys()) + list(nary_ops.keys()) + list(comparison_operators)

    def __init__(self, query: Union[str, List] = None):
        if isinstance(query, str):
            self.ast = self.tokenize(query)
        elif isinstance(query, list):
            self.ast = query
        elif query is None:
            self.ast = []
        else:
            raise TypeError("FuzzyJsonQuery must be initialized with a string or a list of tokens.")

    def tokenize(self, query: str) -> Any:
        """
        Tokenizes the input query string into a nested list structure, recognizing
        field constraints, predicates, logical operators, fuzzy modifiers, and wildcards.

        Args:
            query (str): The query string.

        Returns:
            list: A nested list representing the parsed query.

        Raises:
            ValueError: If there are mismatched parentheses or unexpected tokens.
        """
        def _build(tokens: List[str]) -> Any:
            if not tokens:
                raise ValueError("Unexpected end of query.")

            token = tokens.pop(0)

            if token == '(':
                # Start a new expression
                if not tokens:
                    raise ValueError("Unexpected end of query after '('.")
                op_or_term = tokens.pop(0)

                if op_or_term.lower() in self.ops:
                    op = op_or_term.lower()
                    operands = []
                    while tokens and tokens[0] != ')':
                        operands.append(_build(tokens))
                    if not tokens:
                        raise ValueError("Missing closing parenthesis.")
                    tokens.pop(0)  # Remove the closing ')'
                    return [op] + operands
                else:
                    # It's not an operator; treat as term or predicate
                    tokens.insert(0, op_or_term)
                    operands = []
                    while tokens and tokens[0] != ')':
                        operands.append(_build(tokens))
                    if not tokens:
                        raise ValueError("Missing closing parenthesis.")
                    tokens.pop(0)  # Remove the closing ')'
                    # Default operator is 'and' for grouping terms
                    return ['and'] + operands
            elif token.lower() in self.unary_ops.keys():
                # Unary operator
                op = token.lower()
                operand = _build(tokens)
                return [op, operand]
            elif token.lower() in self.comparison_operators:
                # Predicate operator
                operator = token.lower()
                field_path = tokens.pop(0)
                # Collect all values until we hit an operator or closing parenthesis
                values = []
                while tokens and tokens[0] not in self.ops and tokens[0] != ')':
                    value = tokens.pop(0)
                    # Remove quotes from strings
                    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    else:
                        # Try converting to number
                        try:
                            value = float(value)
                        except ValueError:
                            pass
                    values.append(value)
                return [operator, field_path] + values
            else:
                # Field constraint or simple term
                if ':' in token:
                    field_path, term = token.split(':', 1)
                    return ['contains', field_path, term]
                else:
                    return token

        # Tokenize the query string
        tokens = re.findall(r'\*\*|\*|[<>]=?|==|!=|<=|>=|=|\b\w+(\.\w+)*\b|[:()"]|[-+]?\d*\.\d+|\d+|"[^"]*"|\'[^\']*\'', query)
        tokens = [token for token in tokens if token.strip()]

        parsed = _build(tokens)
        if tokens:
            raise ValueError("Unprocessed tokens remaining.")
        return parsed

    def eval(self, docs: List[Dict], scoring_function: Callable[[Any, Any, str], float] = None) -> 'FuzzySet':
        """
        Evaluates the fuzzy query against a list of JSON documents.

        Args:
            docs (List[Dict]): A list of JSON documents.
            scoring_function (Callable, optional): A function to compute the degree of membership.

        Returns:
            FuzzySet: A FuzzySet containing the degrees of membership for each document.
        """
        if scoring_function is None:
            scoring_function = default_scoring_function

        def _eval(query_part: Any, doc: Dict) -> float:
            if isinstance(query_part, str):
                # Simple term; search in the entire document
                values = flatten_json_values(doc)
                return scoring_function(query_part, values, operator=None)
            elif isinstance(query_part, list):
                op = query_part[0]
                if op in self.comparison_operators:
                    # Predicate evaluation
                    operator = op
                    field_path = query_part[1]
                    target_values = query_part[2:]
                    field_values = get_values_by_field_path(doc, field_path)
                    degrees = []
                    for field_value in field_values:
                        if operator in {'contains_all', 'contains_any'}:
                            degree = evaluate_predicate(operator, field_value, target_values, scoring_function)
                        else:
                            for target_value in target_values:
                                degree = evaluate_predicate(operator, field_value, target_value, scoring_function)
                        degrees.append(degree)
                    return max(degrees, default=0.0)
                elif op in self.nary_ops.keys():
                    # n-ary operator
                    operand_values = [_eval(operand, doc) for operand in query_part[1:]]
                    return self.nary_ops[op](operand_values)
                elif op in self.unary_ops.keys():
                    # Unary operator
                    if len(query_part) != 2:
                        raise ValueError(f"Operator '{op}' requires exactly one operand.")
                    operand_value = _eval(query_part[1], doc)
                    return self.unary_ops[op](operand_value)
                else:
                    raise ValueError(f"Unknown operator: {op}")
            else:
                raise TypeError("Query parts must be strings or lists.")

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
                if op in self.comparison_operators:
                    # Comparison predicate
                    values_str = ' '.join(str(v) for v in tokens[2:])
                    return f"({op} {tokens[1]} {values_str})"
                elif op in self.unary_ops.keys():
                    return f"{op} ({_build(tokens[1])})"
                elif op in self.nary_ops.keys():
                    operand_strs = ' '.join(_build(operand) for operand in tokens[1:])
                    return f"({op} {operand_strs})"
                else:
                    operand_strs = ' '.join(_build(operand) for operand in tokens[1:])
                    return f"({op} {operand_strs})"
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

def evaluate_predicate(operator: str, field_value: Any, target_value: Any, scoring_function: Callable[[Any, Any, str], float]) -> float:
    if field_value is None:
        return 0.0

    if operator in {'contains', 'contains_all', 'contains_any'}:
        if not isinstance(target_value, list):
            target_values = [target_value]
        else:
            target_values = target_value
        if operator == 'contains':
            degrees = [scoring_function(field_value, target, operator) for target in target_values]
            return max(degrees, default=0.0)
        elif operator == 'contains_all':
            degrees = [scoring_function(field_value, target, 'contains') for target in target_values]
            return min(degrees, default=0.0)
        elif operator == 'contains_any':
            degrees = [scoring_function(field_value, target, 'contains') for target in target_values]
            return max(degrees, default=0.0)
    elif operator == 'startswith':
        if isinstance(field_value, str) and isinstance(target_value, str):
            return scoring_function(field_value, target_value, operator)
        else:
            return 0.0
    elif operator == 'exists':
        # Field exists if field_value is not None
        return 1.0
    else:
        # Comparison operators
        try:
            field_value_num = float(field_value)
            target_value_num = float(target_value)
            return scoring_function(field_value_num, target_value_num, operator)
        except ValueError:
            # Cannot convert to float
            return 0.0

def default_scoring_function(observed: Any, target: Any, operator: str = None) -> float:
    if operator in {'==', '!=', '>', '>=', '<', '<='}:
        return comparison_scoring_function(observed, target, operator)
    elif operator == 'contains':
        if isinstance(observed, str) and isinstance(target, str):
            return 1.0 if target.lower() in observed.lower() else 0.0
        else:
            return 0.0
    elif operator == 'startswith':
        if isinstance(observed, str) and isinstance(target, str):
            return 1.0 if observed.lower().startswith(target.lower()) else 0.0
        else:
            return 0.0
    else:
        if isinstance(observed, list):
            return max(default_scoring_function(v, target) for v in observed)
        elif isinstance(observed, dict):
            return max(default_scoring_function(v, target) for v in observed.values())
        elif isinstance(observed, str) and isinstance(target, str):
            return 1.0 if target.lower() in observed.lower() else 0.0
        else:
            return 0.0

def comparison_scoring_function(observed: float, target: float, operator: str) -> float:
    if operator == '==':
        sigma = 1.0
        return math.exp(-((observed - target) ** 2) / (2 * sigma ** 2))
    elif operator == '!=':
        sigma = 1.0
        return 1.0 - math.exp(-((observed - target) ** 2) / (2 * sigma ** 2))
    elif operator == '>':
        k = 1.0
        x0 = target
        return 1.0 / (1.0 + math.exp(-k * (observed - x0)))
    elif operator == '>=':
        k = 1.0
        x0 = target - 0.5
        return 1.0 / (1.0 + math.exp(-k * (observed - x0)))
    elif operator == '<':
        k = 1.0
        x0 = target
        return 1.0 - (1.0 / (1.0 + math.exp(-k * (observed - x0))))
    elif operator == '<=':
        k = 1.0
        x0 = target + 0.5
        return 1.0 - (1.0 / (1.0 + math.exp(-k * (observed - x0))))
    else:
        return 0.0

# Sample JSON documents
docs = [
    {
        "person": {
            "first_name": "John",
            "last_name": "Doe",
            "age": 22,
            "address": {
                "city": "Springfield",
                "street": "Main St"
            }
        },
        "key1": "Value1",
        "summary": "This is a test summary."
    },
    {
        "person": {
            "first_name": "Alice",
            "last_name": "Smith",
            "age": 19,
            "address": {
                "city": "Wood River",
                "street": "Elm St"
            }
        },
        "key1": "Value2",
        "summary": "Another test document."
    },
    {
        "person": {
            "first_name": "Bob",
            "last_name": "Brown",
            "age": 25,
            "address": {
                "city": "Riverwood",
                "street": "Oak St"
            }
        },
        "key1": "Value3",
        "summary": "Yet another test."
    }
]

# Define the query with contains_all
query_str = """
(and
  (contains * "test")
  (exists key1)
  (or
    (< person.age 21)
    (startswith person.first_name "Al")
  )
  (contains_all person.address.* "wood" "river")
)
"""

# Create the query object
query = FuzzyJsonQuery(query_str)

# Evaluate the query
fuzzy_set = query.eval(docs)

# Print the degrees of membership
print(fuzzy_set.memberships)

# Print the query string
print(str(query))
