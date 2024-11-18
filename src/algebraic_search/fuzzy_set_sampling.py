from .fuzzy_set import FuzzySet
from typing import List
import random
import bisect
import itertools

"""
This module provides functions for sampling from fuzzy sets and converting
fuzzy sets into probability distributions.
"""

def top_k(fuzzy_set: FuzzySet, k: int) -> List[int]:
    """
    Returns a list of indices corresponding to the top k memberships.

    Args:
        fuzzy_set (FuzzySet): The FuzzySet to extract the top-k indices from.
        k (int): The number of top memberships to include.

    Returns:
        List[int]: The number of top memberships to include.

    Raises:
        ValueError: If k is a negative integer.
    """
    if k < 0:
        raise ValueError("k must be a non-negative integer.")
    indices_and_memberships = sorted(
        enumerate(fuzzy_set.memberships),
        key=lambda x: x[1],
        reverse=True
    )
    top_indices = [idx for idx, _ in indices_and_memberships[:k]]
    return top_indices

def top_p(fuzzy_set: FuzzySet, p: float) -> List[int]:
    """
    Returns a list of indices corresponding to the top memberships whose
    normalized probabilities sum to p.

    Args:
        fuzzy_set (FuzzySet): The FuzzySet to extract the top-p indices from.
        p (float): The cumulative probability threshold (0 <= p <= 1).

    Returns:
        List[int]: A list of indices corresponding to the top-p memberships.
    
    Raises:
        ValueError: If p is not between 0 and 1, inclusive.
    """
    if not (0 <= p <= 1):
        raise ValueError("p must be between 0 and 1, inclusive.")
       
   
    total_memberships = sum(fuzzy_set.memberships)
    if total_memberships == 0:
        return []
    
    sorted_memberships = sorted(
        enumerate(fuzzy_set.memberships),
        key=lambda x: x[1],
        reverse=True
    )
    cumulative_sum = 0
    top_indices = []
    for idx, membership in sorted_memberships:
        top_indices.append(idx)
        cumulative_sum += membership
        if (cumulative_sum / total_memberships) >= p:
            break
    return top_indices

def sample(fuzzy_set: FuzzySet, n: int, replacement=False) -> List[int]:
    """
    Returns n indices sampled from the original FuzzySet, using the
    normalized membership values as probabilities.

    Args:
        fuzzy_set (FuzzySet): The FuzzySet to sample from.
        n (int): The number of indices to sample.
        replacement (bool, optional): Whether to sample with replacement (default: False).

    Returns:
        List[int]: A list of sampled indices.

    Raises:
        ValueError: If sampling without replacement and n exceeds the number of elements.
        ValueError: If all membership values are zero.
                                      
    """
    if n <= 0:
        raise ValueError("Sample size n must be positive integer.")
    total = sum(fuzzy_set.memberships)
    if total == 0:
        raise ValueError("Cannot sample from a FuzzySet with all zero total memberships.")
    
    probs = [m / total for m in fuzzy_set.memberships]
    population = list(range(len(fuzzy_set.memberships)))
    if replacement:
        sampled_indices = random.choices(population, weights=probs, k=n)
    else:
        if n > len(fuzzy_set.memberships):
            raise ValueError("Sample size n cannot be larger than the number of elements when sampling without replacement.")
        sampled_indices = weighted_sample_without_replacement(
            fuzzy_set.memberships, n)
    return sampled_indices
    
def weighted_sample_without_replacement(weights: List[float], n: int) -> List[int]:
    """
    Samples n unique indices from the list of weights without replacement,
    where the probability of each index is proportional to its weight.

    Args:
        weights (List[float]): The weights for sampling.
        n (int): Number of samples to draw.

    Returns:
        List[int]: Indices of the sampled elements.

    Raises:
        ValueError: If sample size exceeds the number of available elements.
        ValueError: If any weight is negative or all weights are zero.
    """
    if n > len(weights):
        raise ValueError("Sample size n cannot be larger than the number of weights.")
    if any(w < 0 for w in weights):
        raise ValueError("Weights must be non-negative.")
    if all(w == 0 for w in weights):
        raise ValueError("At least one weight must be positive.")
    
    indices = list(range(len(weights)))
    sampled_indices = []
    
    for _ in range(n):
        total = sum(weights)
        cumulative_weights = list(itertools.accumulate(weights))
        r = random.uniform(0, total)
        i = bisect.bisect_left(cumulative_weights, r)
        sampled_indices.append(indices[i])
        # Remove selected weight and index
        del weights[i]
        del indices[i]
    
    return sampled_indices

def to_probability_distribution(fuzzy_set: FuzzySet) -> FuzzySet:
    """
    Converts the membership degrees of the FuzzySet into a probability distribution.
    Each membership degree is divided by the sum of all membership degrees.

    Args:
        fuzzy_set (FuzzySet): The FuzzySet to convert.

    Returns:
        FuzzySet: A new FuzzySet with membership degrees summing to 1.

    Raises:
        ValueError: If the sum of membership degrees is zero.
    """
    total = sum(fuzzy_set.memberships)
    if total == 0:
        raise ValueError("Cannot normalize a FuzzySet with all zero memberships.")
    new_memberships = [m / total for m in fuzzy_set.memberships]
    return FuzzySet(new_memberships)

