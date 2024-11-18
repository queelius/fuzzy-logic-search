import re
from typing import List, Union, Callable
from .result_query import ResultQuery

class FuzzyBooleanQuery:
    """
    A fuzzy Boolean algebra for constructing and evaluating queries with degrees of membership.

    ## Formal Theory

    **Fuzzy Boolean Algebra for Queries**

    We define two algebras in this context:

    1. **Fuzzy Query Algebra (Q_f)**:
        - **Elements**: `Q_f = P(T*)` where `T*` is the set of all finite strings composed of ASCII characters. `P(T*)` represents the power set of `T*`, i.e., all possible subsets of `T*`.
        - **Operations**:
            - **AND (`&`)**: Fuzzy intersection using minimum.
            - **OR (`|`)**: Fuzzy union using maximum.
            - **NOT (`~`)**: Fuzzy complement (`1.0 - x`).
            - **Modifiers**: Such as `very`, `somewhat`, etc., to adjust degrees of membership.

    """

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

    ops = list(unary_ops.keys()) + list(nary_ops.keys())


    def __init__(self, query: Union[str, List] = None):
        """
        Initialize a FuzzyBooleanQuery instance.

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
            raise TypeError("FuzzyBooleanQuery must be initialized with a string or a list of tokens.")

    def tokenize(self, query: str) -> List:
        """
        Tokenize the input query string into a nested list structure, recognizing fuzzy modifiers.

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
                tokens.pop(0)  # Remove '('

            if not tokens:
                raise ValueError("Unexpected end of query after '('.")

            if tokens[0].lower() in FuzzyBooleanQuery.ops:
                op = tokens.pop(0).lower()
            else:
                op = 'and'

            result = [op]
            while tokens and tokens[0] != ')':
                if tokens[0] == '(':
                    tokens.pop(0) # Remove '('
                    result.append(_build(tokens))
                else:
                    result.append(tokens.pop(0))

            if tokens and tokens[0] == ')':
                tokens.pop(0)

            return result
        
        tokens = re.findall(r'\b\w+\b|\(|\)', query)
        return _build(tokens)


    def eval(self,
             docs: List,
             ranker: Callable = lambda term, doc: 1.0 if term in doc else 0.0) -> ResultQuery:
        """
        Evaluate the fuzzy query against one or more documents.

        Args:
            docs: A list of documents where each document is a set of terms,
                or a single document represented as a set of terms.
            ranker (Callable, optional): A function that computes the degree of membership
                of a term in a document. Defaults to a function that returns 1.0 if the term
                is in the document, and 0.0 otherwise. This is also know as the
                set-membership function, i.e., it generates a Boolean query (0 or 1).
                All the modifiers like `very` will thus have no effect.

        Returns:
            ResultQuery: An instance containing a list of float scores
                         indicating the degree of membership for each document.
        """

        def _eval(query_part: Union[str, list], doc) -> float:
            if isinstance(query_part, str):
                return ranker(query_part, doc)
            elif isinstance(query_part, list):
                op = query_part[0]
                if op in FuzzyBooleanQuery.nary_ops.keys():
                    return FuzzyBooleanQuery.nary_ops[op](_eval(part, doc) for part in query_part[1:])
                
                if op in FuzzyBooleanQuery.unary_ops.keys():
                    if len(query_part) != 2:
                        raise ValueError(f"{op} operator must have exactly one operand.")
                    return FuzzyBooleanQuery.unary_ops[op](_eval(query_part[1], doc))
                
                raise ValueError(f"Unknown operator: {op}")
            else:
                raise TypeError("Query parts must be strings or lists.")

        if not isinstance(docs, list):
            docs = [docs]

        scores = [_eval(self.tokens, doc) for doc in docs]
        return ResultQuery(scores)

    def __and__(self, other: 'FuzzyBooleanQuery') -> 'FuzzyBooleanQuery':
        """
        Combine two fuzzy queries with a logical AND.

        Args:
            other (FuzzyBooleanQuery): Another FuzzyBooleanQuery instance.

        Returns:
            FuzzyBooleanQuery: A new FuzzyBooleanQuery representing the logical AND of both queries.
        """
        return FuzzyBooleanQuery(['and', self.tokens, other.tokens])

    def __or__(self, other: 'FuzzyBooleanQuery') -> 'FuzzyBooleanQuery':
        """
        Combine two fuzzy queries with a logical OR.

        Args:
            other (FuzzyBooleanQuery): Another FuzzyBooleanQuery instance.

        Returns:
            FuzzyBooleanQuery: A new FuzzyBooleanQuery representing the logical OR of both queries.
        """
        return FuzzyBooleanQuery(['or', self.tokens, other.tokens])

    def __invert__(self) -> 'FuzzyBooleanQuery':
        """
        Negate the fuzzy query with a logical NOT.

        Returns:
            FuzzyBooleanQuery: A new FuzzyBooleanQuery representing the logical NOT of the current query.
        """
        return FuzzyBooleanQuery(['not', self.tokens])
    
    def very(self) -> 'FuzzyBooleanQuery':
        """
        Apply the `very` modifier to the fuzzy query.

        Returns:
            FuzzyBooleanQuery: A new FuzzyBooleanQuery with the `very` modifier applied.
        """
        return FuzzyBooleanQuery(['very', self.tokens])
    
    def somewhat(self) -> 'FuzzyBooleanQuery':
        """
        Apply the `somewhat` modifier to the fuzzy query.

        Returns:
            FuzzyBooleanQuery: A new FuzzyBooleanQuery with the `somewhat` modifier applied.
        """
        return FuzzyBooleanQuery(['somewhat', self.tokens])
    
    def slightly(self) -> 'FuzzyBooleanQuery':
        """
        Apply the `slightly` modifier to the fuzzy query.

        Returns:
            FuzzyBooleanQuery: A new FuzzyBooleanQuery with the `slightly` modifier applied.
        """
        return FuzzyBooleanQuery(['slightly', self.tokens])
    
    def extremely(self) -> 'FuzzyBooleanQuery':
        """
        Apply the `extremely` modifier to the fuzzy query.

        Returns:
            FuzzyBooleanQuery: A new FuzzyBooleanQuery with the `extremely` modifier applied.
        """
        return FuzzyBooleanQuery(['extremely', self.tokens])
    
    def __eq__(self, other: 'FuzzyBooleanQuery') -> bool:
        return self.tokens == other.tokens
    
    def __ne__(self, other: 'FuzzyBooleanQuery') -> bool:
        return self.tokens != other.tokens
    
    def __getitem__(self, index: int) -> str:
        return self.tokens[index]
    
    def __repr__(self) -> str:
        return f"FuzzyBooleanQuery({self.tokens})"

    def __str__(self) -> str:
        """
        Convert the internal token representation back to a query string.

        Returns:
            str: The string representation of the fuzzy query.
        """
        def _build(tokens: Union[str, list]) -> str:
            if isinstance(tokens, str):
                return tokens
            return f"({tokens[0]} {' '.join(_build(t) for t in tokens[1:])})"
        return _build(self.tokens)
