from typing import List, Union, Iterator

"""
A module for working with fuzzy sets and fuzzy logic in Python.
"""

class FuzzySet:
    """
    Represents a fuzzy set of elements (e.g., documents), where each element has an associated
    degree of membership between 0 and 1. Supports set-theoretic and fuzzy-like operations.

    ## Formal Theory: Fuzzy Set Algebra

    In fuzzy set theory, each element has a degree of membership ranging from 0 (not a member)
    to 1 (full member). The `FuzzySet` class allows for operations such as fuzzy intersection,
    union, and complement, as well as modifiers like `very` and `somewhat`.

    ## Supported Operations

    - Fuzzy Intersection (`&`): Element-wise minimum of degrees of membership.
    - Fuzzy Union (`|`): Element-wise maximum of degrees of membership.
    - Fuzzy Complement (`~`): Element-wise complement (`1.0 - membership`).

    ## Additional Operations

    This class implements a bare-bones version of fuzzy set operations. For more
    advanced operations, consider using the following modules:
    
    - Fuzzy Set Modifiers in `fuzzy_mods.py`
    - Fuzzy Set Defuzzification in `defuzzification.py`
    - Fuzzy Set Sampling in `fuzzy_sampling.py`        
    """

    def __init__(self, memberships: List[float]):
        """
        Initializes a FuzzySet with the given degrees of membership.

        Args:
            memberships (List[float]): A list of degrees of membership between 0 and 1.

        Raises:
            ValueError: If any membership value is not between 0 and 1.
        """
        if not all(0.0 <= m <= 1.0 for m in memberships):
            raise ValueError("All memberships must be between 0 and 1.")
        self.memberships = memberships

    def __and__(self, other: 'FuzzySet') -> 'FuzzySet':
        """
        Returns the fuzzy intersection (AND) of two FuzzySets.

        Args:
            other (FuzzySet): Another FuzzySet to intersect with.

        Returns:
            FuzzySet: A new FuzzySet representing the intersection.

        Raises:
            ValueError: If the FuzzySets are not of the same length.
        """
        if len(self.memberships) != len(other.memberships):
            raise ValueError("FuzzySets must be of the same length.")
        return FuzzySet([min(a, b) for a, b in zip(self.memberships, other.memberships)])

    def __or__(self, other: 'FuzzySet') -> 'FuzzySet':
        """
        Returns the fuzzy union (OR) of two FuzzySets.

        Args:
            other (FuzzySet): Another FuzzySet to union with.

        Returns:
            FuzzySet: A new FuzzySet representing the union.

        Raises:
            ValueError: If the FuzzySets are not of the same length.
        """
        if len(self.memberships) != len(other.memberships):
            raise ValueError("FuzzySets must be of the same length.")
        return FuzzySet([max(a, b) for a, b in zip(self.memberships, other.memberships)])

    def __invert__(self) -> 'FuzzySet':
        """
        Returns the fuzzy complement (NOT) of the FuzzySet.

        Returns:
            FuzzySet: A new FuzzySet representing the complement.
        """
        return FuzzySet([1 - m for m in self.memberships])

    # Comparison Operators
    def __eq__(self, other: 'FuzzySet') -> bool:
        """
        Checks if two FuzzySets are equal.

        Args:
            other (FuzzySet): Another FuzzySet to compare with.

        Returns:
            bool: True if the memberships are equal, False otherwise.
        """
        # check for approximate equality
        if len(self.memberships) != len(other.memberships):
            return False
        return all(abs(a - b) < 1e-6 for a, b in zip(self.memberships, other.memberships))

    def __ne__(self, other: 'FuzzySet') -> bool:
        """
        Checks if two FuzzySets are not equal.

        Args:
            other (FuzzySet): Another FuzzySet to compare with.

        Returns:
            bool: True if the memberships are not equal, False otherwise.
        """
        return not (self.memberships == other.memberships)

    # Sequence Protocol Methods
    def __getitem__(self, index: int) -> float:
        """
        Retrieves the degree of membership at a specific index.

        Args:
            index (int): The index of the membership value to retrieve.

        Returns:
            float: The degree of membership at the specified index.
        """
        return self.memberships[index]

    def __setitem__(self, index: int, value: float):
        """
        Sets the degree of membership at a specific index.

        Args:
            index (int): The index to set the membership value.
            value (float): The new degree of membership (must be between 0 and 1).

        Raises:
            ValueError: If the value is not between 0 and 1.
        """
        if not 0.0 <= value <= 1.0:
            raise ValueError("Degree of membership must be between 0 and 1.")
        self.memberships[index] = value

    def __len__(self) -> int:
        """
        Returns the number of elements in the FuzzySet.

        Returns:
            int: The number of membership values.
        """
        return len(self.memberships)

    def __iter__(self) -> Iterator[float]:
        """
        Returns an iterator over the degrees of membership.

        Returns:
            Iterator[float]: An iterator over the memberships.
        """
        return iter(self.memberships)
    
    def __contains__(self, item: Union[float, int]) -> bool:
        """
        Checks if a membership value is in the FuzzySet.

        Args:
            item (float or int): The membership value to check.

        Returns:
            bool: True if the value is in the memberships, False otherwise.
        """
        return item in self.memberships
    
    def __xor__(self, other: 'FuzzySet') -> 'FuzzySet':
        """
        Returns the fuzzy symmetric difference of two FuzzySets.

        Args:
            other (FuzzySet): Another FuzzySet to compute the symmetric
            difference with.

        Returns:
            FuzzySet: A new FuzzySet representing the symmetric difference.

        Raises:
            ValueError: If the FuzzySets are not of the same length.
        """
        if len(self.memberships) != len(other.memberships):
            raise ValueError("FuzzySets must be of the same length.")
        return (self & ~other) | (~self & other)
    
    def __sub__(self, other: 'FuzzySet') -> 'FuzzySet':
        """
        Returns the fuzzy difference (SUB) of two FuzzySets.

        Args:
            other (FuzzySet): Another FuzzySet to subtract.

        Returns:
            FuzzySet: A new FuzzySet representing the difference.

        Raises:
            ValueError: If the FuzzySets are not of the same length.
        """
        if len(self.memberships) != len(other.memberships):
            raise ValueError("FuzzySets must be of the same length.")
        return self & ~other
       
    # Representation Methods
    def __repr__(self) -> str:
        """
        Returns the official string representation of the FuzzySet.

        Returns:
            str: The string representation.
        """
        return f"FuzzySet({self.memberships})"

    def __str__(self) -> str:
        """
        Returns the informal string representation of the FuzzySet.

        Returns:
            str: A truncated string representation.
        """
        if len(self.memberships) > 6:
            return f"FuzzySet({self.memberships[:6]}...)"
        return f"FuzzySet({self.memberships})"
