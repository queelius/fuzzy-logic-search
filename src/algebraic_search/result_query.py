from typing import List, Union

class ResultQuery:
    """
    A class representing the evaluation results of a Query.

    ## Formal Theory

    **Result Algebra (R)**:

    - **Elements**: `R = [r_1, r_2, ..., r_n]` where each `r_i` ∈ [0, 1] represents the degree of membership of the i-th document in the query result.
    - **Operations**:
        - **AND (`&`)**: Element-wise minimum.
        - **OR (`|`)**: Element-wise maximum.
        - **NOT (`~`)**: Element-wise complement (`1 - r_i`).

    These operations form a Boolean algebra when results are binary (0 or 1) and a fuzzy Boolean algebra when results are in the continuous range [0, 1].

    **Homomorphism Between Query and Result Algebras**:

    The evaluation function `eval` in the `Query` class serves as a homomorphism `φ: Q → R` that preserves the algebraic structure:
    
    - `φ(Q1 & Q2) = φ(Q1) & φ(Q2)`
    - `φ(Q1 | Q2) = φ(Q1) | φ(Q2)`
    - `φ(~Q1) = ~φ(Q1)`

    This ensures that the logical composition of queries translates appropriately to the combination of their evaluation results.
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
    
    def map(self, threshold: float) -> 'ResultQuery':
        return ResultQuery([0 if score < threshold else 1 for score in self.scores])    
    
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