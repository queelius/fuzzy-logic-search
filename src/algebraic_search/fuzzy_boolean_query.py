import re
from typing import List, Union

class FuzzyBooleanQuery:
    """
    A fuzzy Boolean algebra for constructing and evaluating queries with degrees of membership.

    ## Formal Theory

    **Fuzzy Boolean Algebra for Queries and Results**

    We define two algebras in this context:

    1. **Fuzzy Query Algebra (Q_f)**:
        - **Elements**: `Q_f = P(T*)` where `T*` is the set of all finite strings composed of ASCII characters. `P(T*)` represents the power set of `T*`, i.e., all possible subsets of `T*`.
        - **Operations**:
            - **AND (`&`)**: Fuzzy intersection using minimum.
            - **OR (`|`)**: Fuzzy union using maximum.
            - **NOT (`~`)**: Fuzzy complement (`1.0 - x`).
            - **Modifiers**: Such as `very`, `somewhat`, etc., to adjust degrees of membership.

    2. **Fuzzy Result Algebra (R_f)**:
        - **Elements**: `R_f = [r_1, r_2, ..., r_n]` where each `r_i` ∈ [0.0, 1.0] represents the degree of membership of the i-th document in the query result.
        - **Operations**:
            - **AND (`&`)**: Element-wise minimum.
            - **OR (`|`)**: Element-wise maximum.
            - **NOT (`~`)**: Element-wise complement (`1.0 - r_i`).

    **Homomorphism Between Fuzzy Query and Result Algebras**

    The evaluation function `eval` in the `FuzzyBooleanQuery` class serves as a **homomorphism** `φ_f: Q_f → R_f` that preserves the algebraic structure:

    - **Preservation of Operations**:
        - `φ_f(Q1 & Q2) = φ_f(Q1) & φ_f(Q2)`
        - `φ_f(Q1 | Q2) = φ_f(Q1) | φ_f(Q2)`
        - `φ_f(~Q1) = ~φ_f(Q1)`
    - **Preservation of Modifiers**:
        - `φ_f(very Q) = very φ_f(Q)`
        - `φ_f(somewhat Q) = somewhat φ_f(Q)`

    This homomorphic relationship ensures that the logical and fuzzy structures of queries are faithfully represented in the evaluation results.

    ## Attributes

    - `tokens (List)`: A nested list representing the parsed query structure.

    ## Methods

    - `__init__(self, query: Union[str, List] = None)`: Initializes a FuzzyBooleanQuery instance from a query string or list of tokens.
    - `tokenize(self, query: str) -> List`: Parses the query string into a nested list structure, recognizing fuzzy modifiers.
    - `eval(self, docs: Union[List[Set[str]], Set[str]]) -> ResultFuzzyBooleanQuery`: Evaluates the query against documents, returning fuzzy scores.
    - `__and__(self, other: 'FuzzyBooleanQuery') -> 'FuzzyBooleanQuery'`: Combines two fuzzy queries with logical AND.
    - `__or__(self, other: 'FuzzyBooleanQuery') -> 'FuzzyBooleanQuery'`: Combines two fuzzy queries with logical OR.
    - `__invert__(self) -> 'FuzzyBooleanQuery'`: Negates the fuzzy query with logical NOT.
    - `__repr__(self) -> str`: String representation.
    - `__str__(self) -> str`: Readable string representation.

    ## Usage Example

    ```python
    # Example queries
    q1 = FuzzyBooleanQuery("cat dog")
    q2 = FuzzyBooleanQuery("(or fish bird)")
    q3 = ~q2
    combined_query = q1 & q3  # Represents "(and (and cat dog) (not (or fish bird)))"

    # Example documents
    documents = [
        ["cat", "dog"],
        ["fish"],
        ["bird"],
        ["cat", "dog", "fish"],
        ["cat", "dog", "bird"],
        ["cat"],
        ["dog"],
        ["fish", "bird"],
        ["cat", "dog", "fish", "bird"],
    ]

    # Evaluate queries against documents
    results_combined = combined_query.eval(documents)
    print(combined_query)  # Output: (and (and cat dog) (not (or fish bird)))
    print(results_combined)
    # Output: ResultFuzzyBooleanQuery([...])
    ```
    """

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
        tokens = re.findall(r'\b\w+\b|\(|\)', query)

        def _build(tokens: List) -> List:
            if not tokens:
                raise ValueError("Unexpected end of query.")

            if tokens[0] == '(':
                tokens.pop(0)  # Remove '('

            if not tokens:
                raise ValueError("Unexpected end of query after '('.")

            cur = tokens[0].lower()
            ops = {'very', 'somewhat', 'slightly', 'and', 'or', 'not'}
            

            if cur in ops:
                op = tokens.pop(0).lower()
                result = [op]
            elif current not in {'and', 'or', 'not'}:
                # If the first token is not an operator or modifier, default to 'and'
                op = 'and'
                operand = tokens.pop(0)
                if operand == '(':
                    operand = _build(tokens)
                result = [op, operand]
                while tokens and tokens[0] != ')':
                    if tokens[0] == '(':
                        tokens.pop(0)  # Remove '('
                        result.append(_build(tokens))
                    else:
                        operand = tokens.pop(0)
                        if operand == '(':
                            operand = _build(tokens)
                        result.append(operand)

            if tokens and tokens[0] == ')':
                tokens.pop(0)  # Remove ')'

            return result

        parsed_query = _build(tokens)
        if tokens:
            raise ValueError("Mismatched parentheses in query.")
        return parsed_query

    def eval(self, docs: Union[List[Set[str]], Set[str]]) -> ResultFuzzyBooleanQuery:
        """
        Evaluate the fuzzy query against one or more documents.

        Args:
            docs (List[set] or set): A list of documents where each document is a set of terms,
                or a single document represented as a set of terms.

        Returns:
            ResultFuzzyBooleanQuery: An instance containing a list of float scores indicating the degree of membership
                                     for each document.

        Raises:
            ValueError: If the query contains invalid operators, modifiers, or incorrect operand usage.
            TypeError: If the documents are not provided as sets or lists of sets.
        """
        def _eval(query_part: Union[str, list], doc: Set[str]) -> float:
            if isinstance(query_part, str):
                return 1.0 if query_part in doc else 0.0
            elif isinstance(query_part, list):
                op = query_part[0]
                if op == 'and':
                    return min(_eval(part, doc) for part in query_part[1:])
                elif op == 'or':
                    return max(_eval(part, doc) for part in query_part[1:])
                elif op == 'not':
                    if len(query_part) != 2:
                        raise ValueError("`not` operation must have exactly one operand.")
                    return 1.0 - _eval(query_part[1], doc)
                elif op == 'very':
                    if len(query_part) != 2:
                        raise ValueError("`very` modifier must have exactly one operand.")
                    return _eval(query_part[1], doc) ** 2  # Example: 'very' as squared
                elif op == 'somewhat':
                    if len(query_part) != 2:
                        raise ValueError("`somewhat` modifier must have exactly one operand.")
                    return _eval(query_part[1], doc) ** 0.5  # Example: 'somewhat' as square root
                else:
                    raise ValueError(f"Unknown operator or modifier: {op}")
            else:
                raise TypeError("Query parts must be strings or lists.")

        def _evaluate_single(doc: Set[str], evaluator) -> float:
            return evaluator(self.tokens, doc)

        if isinstance(docs, list):
            scores = [ _evaluate_single(doc, _eval) for doc in docs ]
        elif isinstance(docs, set):
            scores = [ _evaluate_single(docs, _eval) ]
        else:
            raise TypeError("Documents must be a set or a list of sets.")

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
