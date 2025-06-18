from typing import List, Any, Callable, Union
from .fuzzy_set import FuzzySet

def defuzzify(fuzzy_set: FuzzySet, method: Union[str, Callable[[float], str]]) -> Union[float, List[str]]:
    """
    Defuzzifies the FuzzySet using the specified method.

    Args:
        fuzzy_set (FuzzySet): The fuzzy set to defuzzify.
        method (Any): if a string, one of 'centroid', 'bisector', 'mom', 'lom', 'som', or 'mom-som'.
            if a callable, a custom defuzzification method that maps a fuzzy value
            to a linguistic term.

    Returns:
        Any: The defuzzified value. If the method is a string, this will be a float.
            If the method is a callable, this will be the return value of the method,
            which can be of any type.
    """

    if not isinstance(fuzzy_set, FuzzySet):
        raise TypeError("Fuzzy set must be an instance of FuzzySet.")
    
    if isinstance(method, str):
        if method == "centroid":
            return defuzzify_centroid(fuzzy_set)
        
        elif method == "bisector":
            return defuzzify_bisector(fuzzy_set)
        
        elif method == "mom":
            return defuzzify_mom(fuzzy_set)
        
        elif method == "lom":
            return defuzzify_lom(fuzzy_set)
        
        elif method == "som":
            return defuzzify_som(fuzzy_set)
        
        elif method == "mom-som":
            return defuzzify_mom_som(fuzzy_set)
        
        elif method == "low-high":
            return defuzzify_linguistic(fuzzy_set, lambda m:
                                        "low" if m < 0.5 else
                                        "high")
        
        elif method == "low-medium-high":
            return defuzzify_linguistic(fuzzy_set, lambda m:
                                        "low" if m < 0.33 else
                                        "medium" if m < 0.66 else
                                        "high")
        
        else:
            raise ValueError("Invalid defuzzification method.")
    elif callable(method):
        return defuzzify_linguistic(fuzzy_set, method)
    else:
        raise TypeError("Defuzzification method must be a string or callable.")

def defuzzify_centroid(fuzzy_set: FuzzySet) -> float:
    """
    Defuzzifies the FuzzySet using the centroid (center of gravity) method.
    Provides a balanced view of overall relevance.

    Returns:
        float: The centroid of the membership function.
    """
    num = sum(idx * m for idx, m in enumerate(fuzzy_set.memberships))
    denom = sum(fuzzy_set.memberships)
    return num / denom if denom != 0 else 0.0

def defuzzify_bisector(fuzzy_set: FuzzySet) -> float:
    """
    Defuzzifies the FuzzySet using the bisector method. Indicates the median
    relevance score.

    Args:
        fuzzy_set (FuzzySet): The fuzzy set to defuzzify.

    Returns:
        float: The bisector of the membership function.
    """
    tot_area = sum(fuzzy_set.memberships)
    if tot_area == 0:
        return 0.0
    cum_area = 0.0
    for idx, m in enumerate(fuzzy_set.memberships):
        cum_area += m
        if cum_area >= tot_area / 2:
            return idx
    return len(fuzzy_set.memberships) - 1

def defuzzify_mom(fuzzy_set: FuzzySet, tol: float=1e-5) -> float:
    """
    Defuzzifies the FuzzySet using the mean of maximum (MOM) method.
    Shows the average relevance of the top documents.

    Args:
        fuzzy_set (FuzzySet): The fuzzy set to defuzzify.
        tol (float, optional): Tolerance for comparing membership values.
            Defaults to 1e-5.

    Returns:
        float: The mean of the maximum membership values.
    """
    max_membership = max(fuzzy_set.memberships)
    max_indices = [idx for idx, m in enumerate(fuzzy_set.memberships) if
                    (m - max_membership) < tol]
    return sum(max_indices) / len(max_indices) if max_indices else 0.0

def defuzzify_lom(fuzzy_set: FuzzySet, tol: float=1e-5) -> float:
    """
    Defuzzifies the FuzzySet using the largest of maximum (LOM) method.

    Args:
        fuzzy_set (FuzzySet): The fuzzy set to defuzzify.
        tol (float, optional): Tolerance for comparing membership values.
            Defaults to 1e-5.

    Returns:
        float: The largest value among the maximum membership values.
    """
    max_membership = max(fuzzy_set.memberships)
    for idx in reversed(range(len(fuzzy_set.memberships))):
        if (fuzzy_set.memberships[idx] - max_membership) < tol:
            return idx
    return 0.0

def defuzzify_som(fuzzy_set: FuzzySet, tol: float=1e-5) -> float:
    """
    Defuzzifies the FuzzySet using the smallest of maximum (SOM) method.

    Returns:
        float: The smallest value among the maximum membership values.
    """
    max_membership = max(fuzzy_set.memberships)
    for idx, m in enumerate(fuzzy_set.memberships):
        if (m - max_membership) < tol:
            return idx
    return 0.0

def defuzzify_mom_som(fuzzy_set: FuzzySet, tol: float=1e-5) -> float:
    """
    Defuzzifies the FuzzySet using the mean of maximum and smallest of maximum (MOM-SOM) method.

    Args:
        fuzzy_set (FuzzySet): The fuzzy set to defuzzify.
        tol (float, optional): Tolerance for comparing membership values.
            Defaults to 1e-5.

    Returns:
        float: The mean of the maximum and smallest membership values.
    """
    max_membership = max(fuzzy_set.memberships)
    max_indices = [idx for idx, m in enumerate(fuzzy_set.memberships) if
                    (m - max_membership) < tol]
    return sum(max_indices) / len(max_indices) if max_indices else 0.0


def defuzzify_linguistic(fuzzy_set: FuzzySet, defuzz_fn: Callable[[float], str]) -> List[str]:
    """
    Defuzzifies the FuzzySet using a custom method `defuzz_fn`. This method
    maps the fuzzy values in a FuzzySet to linguistic terms, like
    'low', 'medium', 'high'. The defuzzified value is a list of these terms,
    one for each fuzzy value in the FuzzySet.

    Args:
        defuzz_fn (Callable[[float], str]): The custom defuzzification method,
            which maps a fuzzy value to a linguistic term.

    Returns:
        List[str]: The defuzzified values. Each value is a linguistic term.
    """

    if not callable(defuzz_fn):
        raise TypeError("Custom defuzzification method must be callable.")
    
    if not isinstance(fuzzy_set, FuzzySet):
        raise TypeError("Fuzzy set must be an instance of FuzzySet.")
    
    return [defuzz_fn(m) for m in fuzzy_set.memberships]
