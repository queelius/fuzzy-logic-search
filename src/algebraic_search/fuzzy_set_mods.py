from .fuzzy_set import FuzzySet

"""
Fuzzy logic modifiers and operations.
"""

def power(fuzzy_set: FuzzySet, n: int) -> FuzzySet:
    """
    Raises the degrees of membership to the power of n.

    Returns:
        FuzzySet: A new FuzzySet with modified degrees of membership.
    """
    return FuzzySet([m ** n for m in fuzzy_set.memberships])

def very(fuzzy_set: FuzzySet) -> FuzzySet:
    """
    Applies the 'very' modifier (squaring the degrees of membership).

    Returns:
        FuzzySet: A new FuzzySet with modified degrees of membership.
    """
    return power(fuzzy_set, 2)

def somewhat(fuzzy_set: FuzzySet) -> FuzzySet:
    """
    Applies the 'somewhat' modifier (square root of the degrees of membership).

    Returns:
        FuzzySet: A new FuzzySet with modified degrees of membership.
    """
    return power(fuzzy_set, 0.5)
    

def slightly(fuzzy_set: FuzzySet) -> FuzzySet:
    """
    Applies the 'slightly' modifier (4th root of the degrees of membership).

    Returns:
        FuzzySet: A new FuzzySet with modified degrees of membership.
    """
    return power(fuzzy_set, 0.25)    

def extremely(fuzzy_set: FuzzySet) -> FuzzySet:
    """
    Applies the 'extremely' modifier (4th power of the degrees of membership).

    Returns:
        FuzzySet: A new FuzzySet with modified degrees of membership.
    """
    return power(fuzzy_set, 4)

def true(fuzzy_set: FuzzySet) -> FuzzySet:
    """
    Sets all degrees of membership to 1.

    Returns:
        FuzzySet: A new FuzzySet where all memberships are 1.
    """
    return FuzzySet([1.0 for _ in fuzzy_set.memberships])

def false(fuzzy_set: FuzzySet) -> 'FuzzySet':
    """
    Sets all degrees of membership to 0.

    Returns:
        FuzzySet: A new FuzzySet where all memberships are 0.
    """
    return FuzzySet([0.0 for _ in fuzzy_set.memberships])

def truth(fuzzy_set: FuzzySet, threshold: float = 0.5) -> FuzzySet:
    """
    Maps degrees of membership to classical truth values based on a threshold.

    Args:
        threshold (float): The threshold value, defaults to 0.5.

    Returns:
        FuzzySet: A new FuzzySet with mapped degrees of membership.
    """
    return FuzzySet([0.0 if m < threshold else 1.0 for m in fuzzy_set.memberships])

def threshold(self, threshold: float) -> 'FuzzySet':
    """
    Returns a new FuzzySet with memberships below the threshold set to 0.

    Args:
        threshold (float): The threshold value.

    Returns:
        FuzzySet: A new FuzzySet with thresholded memberships.
    """
    filtered_memberships = [
        m if m >= threshold else 0.0 for m in self.memberships
    ]
    return FuzzySet(filtered_memberships)
