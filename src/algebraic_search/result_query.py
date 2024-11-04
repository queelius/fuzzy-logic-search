from typing import List, Union

class ResultQuery:
    """
    A class representing the evaluation results of a query.

    ## Formal Theory: Boolean Algebra Over Query Results

    The evaluation results of a query can be represented as a Boolean algebra,
    where the query results are elements of the algebra. Using conventional
    notation, the algebra is defined as follows:

        (R=P([0, 1]^n), and=&, or=|, not=~, bottom=0, top=1)

    - `R = [r_1, r_2, ..., r_n]` where each `r_i` ∈ [0, 1] represents the
      degree-of-membership of the i-th document in the query result.
    - `&` is the element-wise minimum.
    - `|` is the element-wise maximum.
    - `~` is the element-wise complement (`1 - r_i`).

    These operations form a Boolean algebra when results are binary (0 or 1)
    and a fuzzy Boolean algebra when results are in the continuous range [0, 1].

    ## Homomorphism between queries (like BooleanQuery) and ResultQuery

    The evaluation function `eval` in, for instance, the `BooleanQuery` class
    serves as a homomorphism `eval: Q -> R` that preserves the algebraic
    structure:
    
    - `eval(Q1 & Q2) = eval(Q1) & eval(Q2)`
    - `eval(Q1 | Q2) = eval(Q1) | eval(Q2)`
    - `eval(~Q1) = ~eval(Q1)`

    This ensures that the logical composition of queries translates
    appropriately to the combination of their evaluation results.

    ## Fuzzy Operations

    We also provide a range of built-in fuzzy operations that can be applied
    to the evaluation results of a query:

    - `very`: Squares the degree-of-membership of each document.
    - `somewhat`: Takes the square root of the degree-of-membership of each document.
    - `slightly`: Takes the 10th root of the degree-of-membership of each document.
    - `extremely`: Cubes the degree-of-membership of each document.
    - `binary`: Maps the degree-of-membership of each document to 0 if it is less
        than 0.5, and 1 otherwise.
    - `true`: Maps the degree-of-membership of each document to 1.
    - `false`: Maps the degree-of-membership of each document to 0.
    - `map`: Maps the degree-of-membership of each document to 0 if it is less than
      a specified threshold, and 1 otherwise.

    Of course, you are free to define your own fuzzy operations as needed.
    """

    def __init__(self, scores: List[float]):
        if not all(0.0 <= score <= 1.0 for score in scores):
            raise ValueError("All scores must be between 0 and 1.")
        self.scores = scores

    def __and__(self, other: 'ResultQuery') -> 'ResultQuery':
        if len(self.scores) != len(other.scores):
            raise ValueError("ResultQueries must be of the same length.")
        return ResultQuery([min(a, b) for a, b in zip(self.scores, other.scores)])

    def __or__(self, other: 'ResultQuery') -> 'ResultQuery':
        if len(self.scores) != len(other.scores):
            raise ValueError("ResultQueries must be of the same length.")
        return ResultQuery([max(a, b) for a, b in zip(self.scores, other.scores)])

    def __invert__(self) -> 'ResultQuery':
        return ResultQuery([1.0 - score for score in self.scores])
    
    def very(self) -> 'ResultQuery':
        return ResultQuery([score ** 2 for score in self.scores])
    
    def somewhat(self) -> 'ResultQuery':
        return ResultQuery([score ** 0.5 for score in self.scores])

    def slightly(self) -> 'ResultQuery':
        return ResultQuery([score ** 0.1 for score in self.scores])
    
    def extremely(self) -> 'ResultQuery':
        return ResultQuery([score ** 3 for score in self.scores])
    
    def map(self, threshold: float) -> 'ResultQuery':
        return ResultQuery([0 if score < threshold else 1 for score in self.scores])    
    
    def binary(self) -> 'ResultQuery':
        return self.map(0.5)
    
    def true(self) -> 'ResultQuery':
        return [1.0 for _ in self.scores]
    
    def false(self) -> 'ResultQuery':
        return [0.0 for _ in self.scores]
    
    def __eq__(self, other: 'ResultQuery') -> bool:
        return self.scores == other.scores
    
    def __ne__(self, other: 'ResultQuery') -> bool:
        return self.scores != other.scores

    def __getitem__(self, index: int) -> float:
        return self.scores[index]

    def __setitem__(self, index: int, value: float):
        if not 0.0 <= value <= 1.0:
            raise ValueError("Score must be between 0 and 1.")
        self.scores[index] = value

    def __len__(self) -> int:
        return len(self.scores)
    
    def __iter__(self):
        return iter(self.scores)
    
    def __contains__(self, item: Union[float, int]) -> bool:
        return item in self.scores

    def __repr__(self) -> str:
        return f"ResultQuery({self.scores})"

    def __str__(self) -> str:
        return f"ResultQuery({self.scores})"