"""
Enhanced membership functions for fuzzy logic operations.
Provides common fuzzy membership functions used in fuzzy predicates.
"""

import numpy as np
from typing import Union, Callable


def triangular_membership(x: float, a: float, b: float, c: float) -> float:
    """
    Triangular membership function.

    Parameters:
    -----------
    x : float
        Input value
    a : float
        Left foot (membership = 0)
    b : float
        Peak (membership = 1)
    c : float
        Right foot (membership = 0)

    Returns:
    --------
    float : Membership degree in [0, 1]
    """
    # Handle special case where all points are the same
    if a == b == c:
        return 1.0 if x == a else 0.0

    # Handle special case where it's a vertical line at b
    if a == b:
        if x == a:
            return 1.0
        elif x > b and x < c:
            return (c - x) / (c - b)
        else:
            return 0.0

    if b == c:
        if x == c:
            return 1.0
        elif x > a and x < b:
            return (x - a) / (b - a)
        else:
            return 0.0

    # Normal case
    if x <= a or x >= c:
        return 0.0
    elif a < x <= b:
        return (x - a) / (b - a)
    else:  # b < x < c
        return (c - x) / (c - b)


def trapezoidal_membership(x: float, a: float, b: float, c: float, d: float) -> float:
    """
    Trapezoidal membership function.

    Parameters:
    -----------
    x : float
        Input value
    a : float
        Left foot (membership = 0)
    b : float
        Left shoulder (membership = 1)
    c : float
        Right shoulder (membership = 1)
    d : float
        Right foot (membership = 0)

    Returns:
    --------
    float : Membership degree in [0, 1]
    """
    # Handle special case: rectangular membership
    if a == b and c == d:
        if a <= x <= c:
            return 1.0
        else:
            return 0.0

    # Normal trapezoidal case
    if x < a or x > d:
        return 0.0
    elif a <= x < b:
        if b == a:  # Vertical edge
            return 1.0 if x == a else 0.0
        return (x - a) / (b - a)
    elif b <= x <= c:
        return 1.0
    elif c < x <= d:
        if d == c:  # Vertical edge
            return 1.0 if x == c else 0.0
        return (d - x) / (d - c)
    else:
        return 0.0


def gaussian_membership(x: float, mean: float, sigma: float) -> float:
    """
    Gaussian (normal) membership function.

    Parameters:
    -----------
    x : float
        Input value
    mean : float
        Center of the distribution
    sigma : float
        Standard deviation (width)

    Returns:
    --------
    float : Membership degree in [0, 1]
    """
    if sigma == 0:
        return 1.0 if x == mean else 0.0
    return np.exp(-0.5 * ((x - mean) / sigma) ** 2)


def sigmoid_membership(x: float, a: float, c: float) -> float:
    """
    Sigmoid membership function.

    Parameters:
    -----------
    x : float
        Input value
    a : float
        Slope parameter (positive for increasing, negative for decreasing)
    c : float
        Crossover point (where membership = 0.5)

    Returns:
    --------
    float : Membership degree in [0, 1]
    """
    return 1.0 / (1.0 + np.exp(-a * (x - c)))


def bell_membership(x: float, a: float, b: float, c: float) -> float:
    """
    Generalized bell-shaped membership function.

    Parameters:
    -----------
    x : float
        Input value
    a : float
        Width parameter
    b : float
        Shape parameter (usually >= 1)
    c : float
        Center position

    Returns:
    --------
    float : Membership degree in [0, 1]
    """
    if a == 0:
        return 1.0 if x == c else 0.0
    return 1.0 / (1.0 + abs((x - c) / a) ** (2 * b))


# Fuzzy comparison functions using membership functions

def fuzzy_equal(x: float, target: float, tolerance: float = 0.1) -> float:
    """
    Fuzzy equality using triangular membership.
    Returns 1.0 when x == target, decreasing to 0 as distance increases.

    Parameters:
    -----------
    x : float
        Value to compare
    target : float
        Target value
    tolerance : float
        Tolerance range (width of triangular function)

    Returns:
    --------
    float : Membership degree of equality
    """
    return triangular_membership(x, target - tolerance, target, target + tolerance)


def fuzzy_greater_than(x: float, threshold: float, transition_width: float = 0.1) -> float:
    """
    Fuzzy greater-than using sigmoid membership.
    Returns values close to 1 when x >> threshold, close to 0 when x << threshold.

    Parameters:
    -----------
    x : float
        Value to compare
    threshold : float
        Threshold value
    transition_width : float
        Width of the transition zone

    Returns:
    --------
    float : Membership degree of being greater than threshold
    """
    # Slope parameter: steeper for smaller transition width
    a = 10.0 / max(transition_width, 0.001)
    return sigmoid_membership(x, a, threshold)


def fuzzy_less_than(x: float, threshold: float, transition_width: float = 0.1) -> float:
    """
    Fuzzy less-than using sigmoid membership.
    Returns values close to 1 when x << threshold, close to 0 when x >> threshold.

    Parameters:
    -----------
    x : float
        Value to compare
    threshold : float
        Threshold value
    transition_width : float
        Width of the transition zone

    Returns:
    --------
    float : Membership degree of being less than threshold
    """
    # Negative slope for decreasing function
    a = -10.0 / max(transition_width, 0.001)
    return sigmoid_membership(x, a, threshold)


def fuzzy_between(x: float, low: float, high: float, transition_width: float = 0.1) -> float:
    """
    Fuzzy between using trapezoidal membership.
    Returns 1.0 when low <= x <= high, with smooth transitions.

    Parameters:
    -----------
    x : float
        Value to test
    low : float
        Lower bound
    high : float
        Upper bound
    transition_width : float
        Width of transition zones

    Returns:
    --------
    float : Membership degree of being between low and high
    """
    a = low - transition_width
    b = low
    c = high
    d = high + transition_width
    return trapezoidal_membership(x, a, b, c, d)


def fuzzy_close_to(x: float, target: float, sigma: float = 0.1) -> float:
    """
    Fuzzy closeness using Gaussian membership.
    Returns 1.0 when x == target, decreasing smoothly as distance increases.

    Parameters:
    -----------
    x : float
        Value to test
    target : float
        Target value
    sigma : float
        Standard deviation (controls spread)

    Returns:
    --------
    float : Membership degree of being close to target
    """
    return gaussian_membership(x, target, sigma)


def fuzzy_approximately(x: float, target: float, width: float = 0.1) -> float:
    """
    Fuzzy approximation using bell-shaped membership.
    Similar to fuzzy_close_to but with different shape characteristics.

    Parameters:
    -----------
    x : float
        Value to test
    target : float
        Target value
    width : float
        Width parameter

    Returns:
    --------
    float : Membership degree of being approximately equal to target
    """
    return bell_membership(x, width, 2.0, target)


# Linguistic hedges applied to membership functions

def very(membership: float) -> float:
    """
    Linguistic hedge 'very' - intensifies membership.
    very(A) = A^2
    """
    return membership ** 2


def somewhat(membership: float) -> float:
    """
    Linguistic hedge 'somewhat' - dilutes membership.
    somewhat(A) = sqrt(A)
    """
    return membership ** 0.5


def slightly(membership: float) -> float:
    """
    Linguistic hedge 'slightly' - strongly dilutes membership.
    slightly(A) = A^(1/10)
    """
    return membership ** 0.1


def extremely(membership: float) -> float:
    """
    Linguistic hedge 'extremely' - strongly intensifies membership.
    extremely(A) = A^3
    """
    return membership ** 3


# Factory function for creating custom membership functions

def create_membership_function(
    func_type: str,
    **params
) -> Callable[[float], float]:
    """
    Factory function to create membership functions with preset parameters.

    Parameters:
    -----------
    func_type : str
        Type of membership function ('triangular', 'trapezoidal', 'gaussian', 'sigmoid', 'bell')
    **params : dict
        Parameters specific to the function type

    Returns:
    --------
    Callable : A membership function that takes a single float and returns membership degree

    Examples:
    ---------
    >>> young = create_membership_function('trapezoidal', a=0, b=0, c=25, d=35)
    >>> middle_aged = create_membership_function('gaussian', mean=45, sigma=10)
    >>> old = create_membership_function('sigmoid', a=0.1, c=65)
    """
    if func_type == 'triangular':
        a, b, c = params['a'], params['b'], params['c']
        return lambda x: triangular_membership(x, a, b, c)

    elif func_type == 'trapezoidal':
        a, b, c, d = params['a'], params['b'], params['c'], params['d']
        return lambda x: trapezoidal_membership(x, a, b, c, d)

    elif func_type == 'gaussian':
        mean, sigma = params['mean'], params['sigma']
        return lambda x: gaussian_membership(x, mean, sigma)

    elif func_type == 'sigmoid':
        a, c = params['a'], params['c']
        return lambda x: sigmoid_membership(x, a, c)

    elif func_type == 'bell':
        a, b, c = params['a'], params['b'], params['c']
        return lambda x: bell_membership(x, a, b, c)

    else:
        raise ValueError(f"Unknown membership function type: {func_type}")