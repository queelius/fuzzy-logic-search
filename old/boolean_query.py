import re
from typing import List, Union
from .result_query import ResultQuery

class BooleanQuery:
    """
    A Boolean algebra for constructing and evaluating queries. We define a
    Boolean Query language for parsing, generating, and evaluating Boolean
    queries. The query language is based on the following theoretical framework:

    ## Formal Theory

    Q = (P(T*), and, or, not, {}, T*)

    where:
    - T is the set of all characters,
    - T* is the set of all strings of characters,
    - {} is the empty set,
    - P(T*) is the power set of T*.

    This framework allows constructing queries such as:
        "(or (and cat dog) (not (or fish bird)))"
    which is internally represented as:
        ['or', ['and', 'cat', 'dog'], ['not', ['or', 'fish', 'bird']]]

    Queries can also be combined using Python operators:
        Q1 & Q2  # Represents logical AND
        Q1 | Q2  # Represents logical OR
        ~Q1      # Represents logical NOT

    ## Evaluation
    
    The evaluation of queries is performed by the `eval` method, which takes a
    list of documents and returns a ResultQuery instance indicating which
    documents match the query. The ResultQuery instance is itself a Boolean
    algebra, where the query results are elements of the algebra. Thus,
    the evaluation function `eval` serves as a homomorphism `eval: Q -> R`
    that preserves the algebraic structure. See `ResultQuery` for more details.
    """

    def __init__(self, query: Union[str, List] = None):
        """
        Initialize a Query instance.

        Args:
            query (str or list, optional): A query string or a list of tokens.
                If a string is provided, it is parsed into tokens.
                If a list is provided, it is used directly as the token representation.
                Defaults to None, which initializes an empty query.
        """
        if isinstance(query, str):
            self.tokens = self.tokenize(query)
        elif isinstance(query, list):
            self.tokens = query
        elif query is None:
            self.tokens = []
        else:
            raise TypeError("Query must be initialized with a string or a list of tokens.")

    def tokenize(self, query: str) -> List:
        """
        Tokenize the input query string into a nested list structure.

        Args:
            query (str): The query string.

        Returns:
            list: A nested list representing the parsed query.

        Raises:
            ValueError: If there are mismatched parentheses or unexpected tokens.
        """
        def _build(tokens: List) -> List:
            if not tokens:
                raise ValueError("Unexpected end of query.")

            if tokens[0] == '(':
                tokens.pop(0) # Remove '('

            if not tokens:
                raise ValueError("Unexpected end of query after '('.")

            if tokens[0].lower() not in ['and', 'or', 'not']:
                op = 'and'
            else:
                op = tokens.pop(0).lower()

            result = [op]
            while tokens and tokens[0] != ')':
                if tokens[0] == '(':
                    tokens.pop(0)  # Remove '('
                    result.append(_build(tokens))
                else:
                    result.append(tokens.pop(0))

            if tokens and tokens[0] == ')':
                tokens.pop(0)

            return result

        tokens = re.findall(r'\b\w+\b|\(|\)', query)
        return _build(tokens)

    def eval(self, docs: List) -> ResultQuery:
        """
        Evaluate the query against a list of documents.

        Args:
            docs: A list where each document has method for determining if it
            contains a term, `__contains__`.

        Returns:
            List[float]: A list indicating whether each document matches the
            query, 1 for a match and 0 for a non-match.
        """
        def _eval(query_part: Union[str, list], doc) -> bool:
            if isinstance(query_part, str):
                return query_part in doc
            elif isinstance(query_part, list):
                op = query_part[0]
                if op == 'and':
                    return all(_eval(part, doc) for part in query_part[1:])
                elif op == 'or':
                    return any(_eval(part, doc) for part in query_part[1:])
                elif op == 'not':
                    if len(query_part) != 2:
                        raise ValueError("`not` operation must have exactly one operand.")
                    return not _eval(query_part[1], doc)
                else:
                    raise ValueError(f"Unknown operator: {op}")
            else:
                raise TypeError("BooleanQuery parts must be strings or lists.")

        if not isinstance(docs, list):
            docs = [docs]

        results = [_eval(self.tokens, doc) for doc in docs]
        return ResultQuery(results)

    def __and__(self, other: 'BooleanQuery') -> 'BooleanQuery':
        """
        Combine two queries with a logical AND.

        Args:
            other (BooleanQuery): Another BooleanQuery instance.

        Returns:
            BooleanQuery: A new BooleanQuery representing the logical AND of both queries.
        """
        return BooleanQuery(['and', self.tokens, other.tokens])

    def __or__(self, other: 'BooleanQuery') -> 'BooleanQuery':
        """
        Combine two queries with a logical OR.

        Args:
            other (Query): Another BooleanQuery instance.

        Returns:
            BooleanQuery: A new BooleanQuery representing the logical OR of both queries.
        """
        return BooleanQuery(['or', self.tokens, other.tokens])

    def __invert__(self) -> 'BooleanQuery':
        """
        Negate the query with a logical NOT.

        Returns:
            BooleanQuery: A new BooleanQuery representing the logical NOT of the current query.
        """
        return BooleanQuery(['not', self.tokens])

    def __repr__(self) -> str:
        return f"BooleanQuery({self.tokens})"

    def __str__(self) -> str:
        """
        Convert the internal token representation back to a query string.

        Returns:
            str: The string representation of the query.
        """
        def _build(tokens: Union[str, list]) -> str:
            if isinstance(tokens, str):
                return tokens
            return f"({tokens[0]} {' '.join(_build(t) for t in tokens[1:])})"
        return _build(self.tokens)
