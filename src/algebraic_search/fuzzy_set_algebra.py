from .fuzzy_set import FuzzySet
from typing import List, Tuple

"""
This module provides functions for performing algebraic operations on fuzzy
sets. These operations include the fuzzy Cartesian product, fuzzy join,
fuzzy meet, fuzzy reduce, and fuzzy lift. These operations are useful for
aggregating and combining fuzzy sets in information retrieval and decision
making.
"""

def fuzzy_cartesian_product(
    fuzzy_set_a: FuzzySet,
    fuzzy_set_b: FuzzySet,
    t_norm = min,
) -> List[Tuple[int, int, float]]:
    """
    Computes the fuzzy Cartesian product of two FuzzySets using a specified
    t-norm.
    
    Args:
        fuzzy_set_a (FuzzySet): The first FuzzySet.
        fuzzy_set_b (FuzzySet): The second FuzzySet.
        t_norm (Callable): The t-norm to use for combining membership values.
            By default, the minimum t-norm is used, which is equivalent to the
            fuzzy intersection.
    
    Returns:
        List[Tuple[int, int, float]]: A list of tuples representing the Cartesian
            product of the two FuzzySets. Each tuple contains the indices of the
            two memberships and the combined membership value.
    """
    memberships = []
    for idx1, a in enumerate(fuzzy_set_a.memberships):
        for idx2, b in enumerate(fuzzy_set_b.memberships):
            membership = t_norm(a, b)
            memberships.append((idx1, idx2, membership))
    
    return memberships

def fuzzy_join(a: FuzzySet, b: FuzzySet) -> FuzzySet:
    """
    Computes the fuzzy join of two FuzzySet objects. The fuzzy join is the
    element-wise maximum of the two membership values (equivalent to the fuzzy
    union).
    
    Args:
        a (FuzzySet): The first FuzzySet.
        b (FuzzySet): The second FuzzySet.
    
    Returns:
        FuzzySet: A new FuzzySet representing the fuzzy join of the two input
        sets.

    Raises:
        ValueError: If the FuzzySet objects are not of the same length.
    """

    return fuzzy_reduce([a, b], min)

def fuzzy_meet(a: FuzzySet, b: FuzzySet) -> FuzzySet:
    """
    Computes the fuzzy meet of two FuzzySet objects. The fuzzy meet is the
    element-wise minimum of the two membership values (equivalent to the fuzzy
    intersection).

    Args:
        a (FuzzySet): The first FuzzySet.
        b (FuzzySet): The second FuzzySet.
        t_norm (Callable): The t-norm to use for combining membership values.
            By default, the minimum t-norm is used, which is equivalent to the
            fuzzy intersection.

    Returns:
        FuzzySet: A new FuzzySet representing the fuzzy meet of the two input sets.

    Raises:
        ValueError: If the FuzzySets are not of the same length.
    """    
    return fuzzy_reduce([a, b], min)

def fuzzy_reduce(
    fuzzy_sets: List[FuzzySet],
    t_norm = min
) -> FuzzySet:
    """
    Reduces a list of FuzzySets to a single FuzzySet using a specified t-norm.
    What we mean by t-norm is a function that takes two membership values and
    returns a single membership value. The t-norm is applied element-wise to
    the memberships of the FuzzySets. The resulting FuzzySet represents the
    reduced memberships. By default, the `min` t-norm is used, which is
    equivalent to the fuzzy intersection.
     
    Example:

    Suppose we have n FuzzyQuery evaluations, `q1`, `q2`, ..., `qn`, each
    returning a FuzzySet of memberships with respect to a set of documents
    `docs`. We can aggregate these results using the a t-norm to obtain a
    single FuzzySet representing the aggregation of the n sets. For example,
    suppose we use the t-norm `min`, then:
    
        >>> fuzzy_aggregate([q1(docs), q2(docs), ..., qn(docs)], t_norm=min)
    
    is equivalent to

        >>> (q1 & q2 & ... & qn)(docs)

    Args:
        fuzzy_sets (List[FuzzySet]): A list of FuzzySets to aggregate.
        t_norm (Callable): The t-norm to use for combining membership values.
            By default, the `min` t-norm is used, which is equivalent to the
            fuzzy intersection.

    Returns:
        FuzzySet: A new FuzzySet representing the reduced memberships.

    Raises:
        ValueError: If the FuzzySets are not of the same length.
    """

    if not fuzzy_sets:
        return FuzzySet([])
    
    n = len(fuzzy_sets[0].memberships)
    if not all(len(fs.memberships) == n for fs in fuzzy_sets):
        raise ValueError("FuzzySets must be of the same length.")
    
    memberships = [t_norm(*m) for m in zip(*[fs.memberships for fs in fuzzy_sets])]
    return FuzzySet(memberships)


def fuzzy_lift(
    fuzzy_set: FuzzySet,
    t_norm = min
) -> FuzzySet:
    """
    Lifts a FuzzySet to its power set using a specified t-norm. The power set
    is constructed by taking the Cartesian product of the FuzzySet with itself
    and applying the t-norm to the membership values.

    Args:
        fuzzy_set (FuzzySet): The FuzzySet to lift.
        t_norm (Callable): The t-norm to use for combining membership values.
            By default, the minimum t-norm is used, which is equivalent to the
            fuzzy intersection.

    Returns:
        FuzzySet: A new FuzzySet representing the lifted memberships.

    Raises:
        ValueError: If the FuzzySet is empty.
    """

    if not fuzzy_set.memberships:
        raise ValueError("Cannot lift an empty FuzzySet.")
    
    cartesian_memberships = fuzzy_cartesian_product(fuzzy_set, fuzzy_set, t_norm)
    memberships = [max(m for _, _, m in cartesian_memberships if m > 0)]
    return FuzzySet(memberships)
    