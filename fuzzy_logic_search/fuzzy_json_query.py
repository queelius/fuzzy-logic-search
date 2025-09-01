import re
from typing import List, Callable, Any, Dict
from .fuzzy_set import FuzzySet
from .default_preds import default_preds
from .utils import get_values_by_field_path
import logging

logging.basicConfig(level=logging.INFO)

class FuzzyJsonQuery:
    """
    A class that represents and evaluates fuzzy queries over JSON documents.
    Accepts an AST directly and evaluates it against the documents.

    FuzzyQuery is a fuzzy set-based query language that allows for querying
    JSON-like documents using fuzzy logic. The members of a fuzzy query are
    documents, and the degree of membership is the degree to which a document
    is a member of the query.

    When we evaluate a fuzzy query against a document or set of documents,
    we get a degree of membership for each document. This degree of membership
    is a value between 0 and 1, where 0 means the document is not a member
    of the query and 1 means the document is a full member of the query.

    We call this result a FuzzySet, which is also a fuzzy set. That is to say,
    FuzzyQuery's `eval` method is a homorphism from FuzzyQuery to FuzzySet.
    As both are fuzzy sets, they support the full range of fuzzy set operations,
    such as `and`, `or`, `not`, `very`, `somewhat`, etc.

    ## Query Syntax

    The query syntax is a nested list of operators and operands. The first element
    of each list is the operator, and the remaining elements are the operands.

    For example, the query "(field field-path (contains python)" would be
    represented as
    
    ```
    Q = FuzzyQuery(['field', 'field-path', ['contains', 'python']])
    ```

    We can apply fuzzy set operations to `Q`, such as `~Q`, `Q1 & Q2`, `Q1 | Q2`, etc.
    `~Q` maps to `FuzzyQuery(['not', Q])` and so on.

    Once we evaluate the query against a set of documents, we get a degree of
    membership for each document:
    
    ```
    D = Q.eval(docs)
    ```

    We can then apply fuzzy set operations to the result `D`. For instance,
    `~D` returns the complement of the result and so on. Note that
    `(~Q).eval(docs)` is equivalent to `~D`.

    There is no way to map `D` back to a query, as the `FuzzySet` class does not
    store the query AST and many queries can produce the same `FuzzySet` result.
    """
    # Define unary and n-ary operators
    unary_ops = {
        'same': lambda x: x,
        'extremely': lambda x: x ** 2, # extremely slightly = same
        'slightly': lambda x: x ** 0.5,
        'very': lambda x: x ** 1.25,  # very somwhat = same
        'somewhat': lambda x: x ** 0.8,
        'not': lambda x: 1.0 - x
    }

    nary_ops = {
        'and': min,
        'or': max,
        # xor = (not A and B) or (A and not B)
        # what is the n-ary version of xor:
        #
        # => (not A and B and C) or (A and not B and C) or (A and B and not C)
        # generalize to n-ary:
        # => (not A and B and C and ... and Z) or (A and not B and C and ... and Z) or ... or (A and B and C and ... and not Z)
        # since these are all over fuzzy degree-of-membership values, we let
        # and = min, or = max, and not = 1 - x
        # 'xor': lambda *args: max(min(1 - arg if i == j else arg for j, arg in
        #                              enumerate(args)) for i, _ in enumerate(args)),
        # 'nand': lambda *args: 1 - min(args),
        # 'nor': lambda *args: 1 - max(args),
        # 'xnor': lambda *args: min(min(1 - arg if i == j else arg for j, arg in
        #                              enumerate(args)) for i, _ in enumerate(args)),
        # 'nxor': lambda *args: 1 - max(min(1 - arg if i == j else arg for j, arg in
        #                                 enumerate(args)) for i, _ in enumerate(args)),
        # 'xnor': lambda *args: 1 - min(min(1 - arg if i == j else arg for j, arg in
        #                                 enumerate(args)) for i, _ in enumerate(args)),
        # 'implies': lambda a, b: min(1, 1 - a + b)
    }

    def __init__(self, ast: List = None, preds: Dict[str, Callable] = None):
        """
        Initializes the FuzzyJsonQuery with an AST and optional custom predicates.
        The primary way in which you can customize is a predicate is by returning
        a degree of membership between 0 and 1, indicating the degree to which
        the predicate is satisfied.

        Args:
            ast (List): The Abstract Syntax Tree representing the query. It is a nested list of
                operators and operands. The first element of each list is the operator, and the
                remaining elements are the operands. It is a JSON-compatible list.
            preds (Dict[str, Callable]): A dictionary of predicate functions.
                Override any of the defaults by providing a custom one.
                See default_preds.py for the default implementations and available predicates.
        """
        if ast is None:
            self.ast = []
        elif isinstance(ast, list):
            self.ast = ast
        else:
            raise TypeError("FuzzyJsonQuery must be initialized with an AST represented as a list.")

        self.preds = default_preds()
        if preds is not None:
            self.preds.update(preds)

    def eval(self, docs: List[Dict]) -> FuzzySet:
        """
        Evaluates the fuzzy query against a list of JSON-compatible dict objects.

        Args:
            docs (List[Dict]): A list of JSON-compatible dict objects.

        Returns:
            FuzzySet: A FuzzySet containing the degree of membership for each
                document in the list with respect to the query.
        """
        def _eval(node: Any, doc: Dict) -> float:

            print(f"node: {node}")
            if not isinstance(node, list):
                print("leaf node: ", node)
                return node
            elif isinstance(node, list):
                op = node[0]
                operands = node[1:]

                print(f"evaluating {op=} on {operands=} for {doc=}")

                if op == "field":
                    if len(operands) != 2 and len(operands) != 3:
                        raise ValueError("Invalid number of operands for 'field' operator.")
                    field_path = operands[0]
                    expr_or_value = operands[1]
                    field_values = get_values_by_field_path(doc, field_path)
                    print(f"{field_path=} has {field_values=}")
                    degrees = []
                    for value in field_values:
                        print(f"evaluating {expr_or_value=} for {value=}")
                        degree = _eval(expr_or_value, value)
                        print(f"degree: {degree}")
                        degrees.append(degree)
                    
                    quant = 'any' if len(operands) == 2 else operands[2][0]
                    if quant not in ['all', 'any', 'none']:
                        raise ValueError(f"Invalid quantifier: {quant}")
                    quant_fn = self.preds.get(quant)
                    if quant_fn is None:
                        raise ValueError(f"Unknown quantifier: {quant}")
                    return quant_fn(degrees) if degrees else 0.0
                
                elif op == "exists":
                    if len(operands) != 1:
                        raise ValueError("Invalid number of operands for 'exists' operator.")
                    field_path = operands[0]
                    print(f"evaluating 'exists' on {field_path=} for {doc=}")                    
                    degree = self.preds['exists'](field_path, doc)
                    print(f"degree: {degree}")
                    return degree

                elif op in self.nary_ops:
                    operand_values = [_eval(op, doc) for op in operands]
                    return self.nary_ops[op](operand_values)

                elif op in self.unary_ops:
                    operand_value = _eval(operands[0], doc)
                    return self.unary_ops[op](operand_value)

                elif op in self.preds:
                    eval_operands = [_eval(operand, doc) for operand in operands]
                    print(f"eval_operands: {eval_operands}")
                    return self.preds[op](eval_operands, doc)

                else:
                    raise ValueError(f"Unknown operator: {op}")
            else:
                raise ValueError("Invalid AST node")
        
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
                operand_strs = ' '.join(_build(operand) for operand in tokens[1:])
                return f"({op} {operand_strs})"
            else:
                return str(tokens)
        return _build(self.ast)

    def __repr__(self) -> str:
        return f"FuzzyJsonQuery({self.ast})"


def fuzzy_eval(query: List, doc: Dict) -> float:
    """
    Evaluate a fuzzy query expression against a single document.
    
    This is a standalone function that can be used by the lazy streaming
    system to evaluate fuzzy queries on individual documents.
    
    Args:
        query: Fuzzy query expression (AST)
        doc: JSON document to evaluate against
        
    Returns:
        Membership degree in [0, 1]
    """
    # Create a temporary FuzzyJsonQuery to leverage existing evaluation logic
    fq = FuzzyJsonQuery(query)
    
    # Internal evaluation function from the class
    def _eval(node: Any, document: Dict) -> float:
        if not isinstance(node, list):
            # Leaf node - return as is
            return node if isinstance(node, (int, float)) else 1.0
            
        op = node[0]
        operands = node[1:]
        
        # Handle field access
        if op == "field" or (isinstance(op, str) and op.startswith(":")):
            if op.startswith(":"):
                # Shorthand field access like ":name"
                field_path = op[1:]
                if len(operands) == 0:
                    # Just return field value existence check
                    values = get_values_by_field_path(document, field_path)
                    return 1.0 if values else 0.0
                else:
                    # Apply predicate to field values
                    values = get_values_by_field_path(document, field_path)
                    if not values:
                        return 0.0
                    # Evaluate predicate on each value and take max (existential)
                    degrees = [_eval(operands[0], val) if isinstance(operands[0], list)
                              else fq.preds.get("==", lambda x, y: 1.0 if x == y else 0.0)([val, operands[0]], document)
                              for val in values]
                    return max(degrees) if degrees else 0.0
            else:
                # Standard field operator
                field_path = operands[0]
                values = get_values_by_field_path(document, field_path)
                if len(operands) > 1:
                    expr = operands[1]
                    degrees = [_eval(expr, val) if isinstance(expr, list)
                              else fq.preds.get("==", lambda x, y: 1.0 if x == y else 0.0)([val, expr], document)
                              for val in values]
                    # Default to existential quantification (any)
                    return max(degrees) if degrees else 0.0
                else:
                    return 1.0 if values else 0.0
        
        # Handle path operator for field extraction
        elif op == "path" or op == "@":
            if len(operands) == 1:
                field_path = operands[0]
                if isinstance(field_path, str):
                    # Remove @ prefix if present
                    if field_path.startswith("@"):
                        field_path = field_path[1:]
                    values = get_values_by_field_path(document, field_path)
                    # For path extraction, return 1.0 if field exists, 0.0 otherwise
                    return 1.0 if values else 0.0
            return 0.0
        
        # Handle exists operator
        elif op == "exists" or op == "exists?":
            field_path = operands[0]
            if isinstance(field_path, str) and field_path.startswith("@"):
                field_path = field_path[1:]
            values = get_values_by_field_path(document, field_path)
            return 1.0 if values else 0.0
        
        # Handle fuzzy modifiers
        elif op in fq.unary_ops:
            operand_value = _eval(operands[0], document)
            return fq.unary_ops[op](operand_value)
        
        # Handle logical operators
        elif op in fq.nary_ops:
            operand_values = [_eval(operand, document) for operand in operands]
            return fq.nary_ops[op](*operand_values)
        
        # Handle comparison operators
        elif op in ["==", "eq?", "!=", "neq?", ">", "gt?", "<", "lt?", ">=", "gte?", "<=", "lte?"]:
            if len(operands) == 2:
                left = operands[0]
                right = operands[1]
                
                # Extract values if they're field paths
                if isinstance(left, str) and left.startswith("@"):
                    left_values = get_values_by_field_path(document, left[1:])
                    left = left_values[0] if left_values else None
                elif isinstance(left, list):
                    left = _eval(left, document)
                    
                if isinstance(right, str) and right.startswith("@"):
                    right_values = get_values_by_field_path(document, right[1:])
                    right = right_values[0] if right_values else None
                elif isinstance(right, list):
                    right = _eval(right, document)
                
                # Apply fuzzy predicate
                if op in ["==", "eq?"]:
                    pred = fq.preds.get("==", lambda x, y: 1.0 if x == y else 0.0)
                elif op in ["!=", "neq?"]:
                    pred = fq.preds.get("!=", lambda x, y: 1.0 if x != y else 0.0)
                elif op in [">", "gt?"]:
                    pred = fq.preds.get(">", lambda x, y: 1.0 if x > y else 0.0)
                elif op in ["<", "lt?"]:
                    pred = fq.preds.get("<", lambda x, y: 1.0 if x < y else 0.0)
                elif op in [">=", "gte?"]:
                    pred = fq.preds.get(">=", lambda x, y: 1.0 if x >= y else 0.0)
                elif op in ["<=", "lte?"]:
                    pred = fq.preds.get("<=", lambda x, y: 1.0 if x <= y else 0.0)
                
                return pred([left, right], document)
        
        # Handle string predicates
        elif op in ["contains?", "starts-with?", "ends-with?", "regex?", "in?"]:
            if op in fq.preds:
                eval_operands = []
                for operand in operands:
                    if isinstance(operand, str) and operand.startswith("@"):
                        values = get_values_by_field_path(document, operand[1:])
                        eval_operands.append(values[0] if values else "")
                    elif isinstance(operand, list):
                        eval_operands.append(_eval(operand, document))
                    else:
                        eval_operands.append(operand)
                return fq.preds[op](eval_operands, document)
        
        # Handle other predicates in the predicate dictionary
        elif op in fq.preds:
            eval_operands = []
            for operand in operands:
                if isinstance(operand, str) and operand.startswith("@"):
                    values = get_values_by_field_path(document, operand[1:])
                    eval_operands.append(values[0] if values else None)
                elif isinstance(operand, list):
                    eval_operands.append(_eval(operand, document))
                else:
                    eval_operands.append(operand)
            return fq.preds[op](eval_operands, document)
        
        # Default: unknown operator returns 0
        return 0.0
    
    try:
        result = _eval(query, doc)
        # Ensure result is in [0, 1]
        return max(0.0, min(1.0, float(result)))
    except Exception as e:
        # On error, return 0 membership
        logging.debug(f"Error evaluating fuzzy query: {e}")
        return 0.0

