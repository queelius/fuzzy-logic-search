import re
from typing import List, Union, Callable
from .fuzzy_set import FuzzySet

class FuzzyQuery:
    """
    Represents a fuzzy query constructed using fuzzy logic, supporting fuzzy modifiers
    and logical operators. When evaluated, it produces a FuzzySet of documents with
    degrees of membership.

    ## Formal Theory: Fuzzy Query Algebra

    The `FuzzyQuery` class represents elements in a fuzzy query algebra, allowing for
    the construction and combination of fuzzy queries using logical operators and
    fuzzy modifiers.

    ## Supported Features

    - **Logical Operators**:
        - `and`: Fuzzy intersection (minimum).
        - `or`: Fuzzy union (maximum).
        - `not`: Fuzzy complement (`1.0 - membership`).

    - **Fuzzy Modifiers**:
        - `very`: Squares the degree of membership.
        - `somewhat`: Square root of the degree of membership.
        - `slightly`: 10th root of the degree of membership.
        - `extremely`: Cube of the degree of membership.

    - **Custom Membership Functions**:
        - Users can provide custom membership functions to calculate the degree of
          membership of terms in documents.

    ### Example

    This framework allows constructing queries such as:
    ```
    (or (and cat dog) (not (very (or fish bird))))
    ```
    which is represented (AST) as:
    ```json
    ['or', ['and', 'cat', 'dog'], ['very' ['not', ['or', 'fish', 'bird']]]]
    ```
    You are free of course to directly construct the query using the AST
    JSON representation.

    You may also construct the query using Python operators:

    ```python
    from fuzzy_query import FuzzyQuery as fq
    import fuzzy_mods as mods
    q = fq("cat") & fq("dog") & (mods.very(~(fq("fish") | fq("bird"))))
    ```

    ## Homomorphism to FuzzySet

    The `FuzzyQuery.eval` method acts as a homomorphism from the fuzzy query
    algebra to the fuzzy set algebra (`FuzzySet`), preserving the algebraic
    structure.

    ### Example

    Let `q1` and `q2` be two fuzzy queries. The following properties hold:

    - `(q1 & q2).eval(d) = q1.eval(d) & q2(d)`
    - `(q1 | q2).eval(d) = q1.eval(d) | q2.eval(d)`
    - `(~q1).eval(d) = ~(q1.eval(d))`
    - 'q1.very().eval(d) = q1.eval(d).very()`
    
    and so on. This ensures that the logical composition of fuzzy queries maps
    to the corresponding fuzzy set operations.

    ## Additional Notes

    ### Fuzzy Queries vs. Fuzzy Sets

    You cannot go from a `FuzzySet` to a `FuzzyQuery', as the relationship is
    not bijective. However, as demonstrated, many of the same operations can be
    performed on both fuzzy sets and fuzzy queries.
    
    The primary role of `FuzzyQuery` is to construct and evaluate fuzzy queries
    using fuzzy logic, while `FuzzySet` is used to represent the results of
    these queries. Fuzzy sets have additional operations such as defuzzification
    and sampling, which are not directly applicable to fuzzy queries themselves,
    only to the evaluated results.

    ### Relaxing the Queries

    By default, a query such as "cat dog" will be treated as a logical AND
    operation: "(and cat dog)". This simplifies most queries, since most
    queries are likely to be conjunctions.

    #### Example
    
    The query:
    ```
    cat dog (not fish)
    ```
    is equivalent to:
    ```
    (and cat dog (not fish))
    ```
    """
    
    # Define the unary operators
    unary_ops = {
        'very': lambda x: x ** 2,
        'somewhat': lambda x: x ** 0.5,
        'slightly': lambda x: x ** 0.1,
        'extremely': lambda x: x ** 3,
        'not': lambda x: 1.0 - x
    }

    # Define the n-ary operators, n > 1
    nary_ops = {
        'and': min,
        'or': max,
        'sym-diff': lambda a, b: max(a, b) - min(a, b),
        'diff': lambda a, b: max(a - b, 0)
    }

    # List of all operators
    ops = list(unary_ops.keys()) + list(nary_ops.keys())

    def __init__(self, query: Union[str, List]):
        """
        Initializes a FuzzyQuery instance.

        Args:
            query (str or list, optional): A query string or a list of tokens.
                If a string is provided, it is parsed into tokens.
                If a list is provided, it is used directly as the abstract syntax tree.

        Raises:
            TypeError: If the query is not a string or list.
            ValueError: If there is an error in parsing the query string.
        """
        if isinstance(query, str):
            self.ast = self.parse(query)
        elif isinstance(query, list):
            self.ast = query
        else:
            raise TypeError("FuzzyQuery must be initialized with a string or a list.")

    def parse(self, query: str) -> List:
        """
        Maps the input query string to the AST representation, a nested list
        structure representing the query. The AST is valid JSON.

        Args:
            query (str): The query string.

        Returns:
            list: A nested list representing the parsed query.

        Raises:
            ValueError: If there are mismatched parentheses or unexpected tokens.
        """
        def _build(ast: List) -> List:
            if not ast:
                raise ValueError("Unexpected end of query.")

            if ast[0] == '(':
                ast.pop(0)

            if not ast:
                raise ValueError("Unexpected end of query after '('.")
            
            if ast[0].lower() in FuzzyQuery.ops:
                op = ast.pop(0).lower()
            else:
                op = 'and'

            result = [op]
            while ast and ast[0] != ')':
                if ast[0] == '(':
                    ast.pop(0)  # Remove '('
                    result.append(_build(ast))
                else:
                    result.append(ast.pop(0))

            if ast and ast[0] == ')':
                ast.pop(0)

            return result

        tokens = re.findall(r'\b\w+\b|\(|\)', query)
        return _build(tokens)
    
    def __call__(self, docs, membership_fn=None) -> FuzzySet:
        """
        A shortcut for evaluating the fuzzy query against a list of documents.
        See: `FuzzyQuery.eval`.        
        """
        return self.eval(docs, membership_fn)        

    def eval(self,
             docs: List,
             membership_fn: Callable = None) -> FuzzySet:
        """
        Evaluates the fuzzy query against a list of documents.

        Args:
            docs (List[List[str]]): A list of documents, where each document is
                a list of terms.
            membership_fn (Callable, optional): A function that computes the
                degree of membership of a term in a document. It should accept a
                term and a document, and return a float between 0 and 1.
                Defaults to crisp set-membership function (classical), assigning
                1.0 if the term is in the document, and 0.0 otherwise.

        Returns:
            FuzzySet: A FuzzySet containing the degrees of membership for each
            document.

        Raises:
            ValueError: If there is an error during evaluation.
        """
        if membership_fn is None:
            membership_fn = lambda term, doc: 1.0 if term in doc else 0.0

        def _eval(query_part: Union[str, list], doc) -> float:
            if isinstance(query_part, str):
                return membership_fn(query_part, doc)
            elif isinstance(query_part, list):
                op = query_part[0]
                if op in self.nary_ops.keys():
                    operands = [_eval(operand, doc) for operand in query_part[1:]]
                    return self.nary_ops[op](operands)
                elif op in self.unary_ops.keys():
                    if len(query_part) != 2:
                        raise ValueError(f"Operator '{op}' requires exactly one operand.")
                    operand = _eval(query_part[1], doc)
                    return self.unary_ops[op](operand)
                else:
                    raise ValueError(f"Unknown operator: {op}")
            else:
                raise TypeError("Query parts must be strings or lists.")
            
        if not isinstance(docs, list):
            docs = [docs]

        degrees_of_membership = [_eval(self.ast, doc) for doc in docs]
        return FuzzySet(degrees_of_membership)

    def __and__(self, other: 'FuzzyQuery') -> 'FuzzyQuery':
        """
        Combines two FuzzyQueries with a logical AND.

        Args:
            other (FuzzyQuery): Another FuzzyQuery instance.

        Returns:
            FuzzyQuery: A new FuzzyQuery representing the logical AND of both queries.
        """
        return FuzzyQuery(['and', self.ast, other.ast])

    def __or__(self, other: 'FuzzyQuery') -> 'FuzzyQuery':
        """
        Combines two FuzzyQueries with a logical OR.

        Args:
            other (FuzzyQuery): Another FuzzyQuery instance.

        Returns:
            FuzzyQuery: A new FuzzyQuery representing the logical OR of both queries.
        """
        return FuzzyQuery(['or', self.ast, other.ast])

    def __invert__(self) -> 'FuzzyQuery':
        """
        Negates the FuzzyQuery with a logical NOT.

        Returns:
            FuzzyQuery: A new FuzzyQuery representing the logical NOT of the current query.
        """
        return FuzzyQuery(['not', self.ast])
    
    # Fuzzy Modifiers
    def very(self) -> 'FuzzyQuery':
        """
        Applies the 'very' modifier to the FuzzyQuery.

        Returns:
            FuzzyQuery: A new FuzzyQuery with the 'very' modifier applied.
        """
        return FuzzyQuery(['very', self.ast])

    def somewhat(self) -> 'FuzzyQuery':
        """
        Applies the 'somewhat' modifier to the FuzzyQuery.

        Returns:
            FuzzyQuery: A new FuzzyQuery with the 'somewhat' modifier applied.
        """
        return FuzzyQuery(['somewhat', self.ast])

    def slightly(self) -> 'FuzzyQuery':
        """
        Applies the 'slightly' modifier to the FuzzyQuery.

        Returns:
            FuzzyQuery: A new FuzzyQuery with the 'slightly' modifier applied.
        """
        return FuzzyQuery(['slightly', self.ast])

    def extremely(self) -> 'FuzzyQuery':
        """
        Applies the 'extremely' modifier to the FuzzyQuery.

        Returns:
            FuzzyQuery: A new FuzzyQuery with the 'extremely' modifier applied.
        """
        return FuzzyQuery(['extremely', self.ast])

    # Comparison operators

    def __eq__(self, other: 'FuzzyQuery') -> bool:
        """
        Checks if two FuzzyQueries are equal.

        Args:
            other (FuzzyQuery): Another FuzzyQuery to compare with.

        Returns:
            bool: True if the queries are equal, False otherwise.
        """
        return self.ast == other.ast

    def __ne__(self, other: 'FuzzyQuery') -> bool:
        """
        Checks if two FuzzyQueries are not equal.

        Args:
            other (FuzzyQuery): Another FuzzyQuery to compare with.

        Returns:
            bool: True if the queries are not equal, False otherwise.
        """
        return self.ast != other.ast

    def __str__(self) -> str:
        """
        Converts the AST representation to query string format.

        Returns:
            str: The string representation of the FuzzyQuery.
        """
        def _build(ast: Union[str, list]) -> str:
            if isinstance(ast, str):
                return ast
            elif isinstance(ast, list):
                op = ast[0]
                operands = ast[1:]
                if op in self.unary_ops.keys():
                    return f"({op} {_build(operands[0])})"
                elif op in self.nary_ops.keys():
                    operand_strs = ' '.join(_build(operand) for operand in operands)
                    return f"({op} {operand_strs})"
                else:
                    raise ValueError(f"Unknown operator: {op}")
            else:
                raise TypeError("AST elements must be strings or lists.")
            
        return _build(self.ast)

    def __repr__(self) -> str:
        """
        Returns the stringified AST representation of the FuzzyQuery.

        Returns:
            str: The AST as a string.
        """
        return f"FuzzyQuery({self.ast})"
