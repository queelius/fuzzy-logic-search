from math import exp
from difflib import SequenceMatcher

def fuzzy_comparison_membership_generator(
        sigma: float = 1.0,
        k: float = 1.0) -> callable:
    """
    Returns a comparison scoring function for fuzzy comparisons. Supports both
    numeric and string types.

    Args:
    - sigma (float): Parameter for Gaussian function in '==' and '!=' operations.
    - k (float): Parameter for sigmoid function in ordering operations.

    Returns:
    - callable: A function that computes a degree of membership for comparison
      operators.
    """
    
    def _cmp(observed, target, op: str) -> float:
        # Handle numeric comparisons

        def _compute_diff(observed, target):
            if isinstance(observed, (int, float)) and isinstance(target, (int, float)):
                return observed - target
            
            elif isinstance(observed, str) and isinstance(target, str):
                return SequenceMatcher(None, observed, target).ratio()
            
        diff = _compute_diff(observed, target)

        if op == '==':
            return exp(-(diff ** 2) / (2 * sigma ** 2))
        elif op == '!=':
            return 1 - exp(-(diff ** 2) / (2 * sigma ** 2))
        elif op == '>':
            return 1 / (1 + exp(-k * diff))
        elif op == '>=':
            return 1 / (1 + exp(-k * (diff + 0.5)))
        elif op == '<':
            return 1 - (1 / (1 + exp(-k * diff)))
        elif op == '<=':
            return 1 - (1 / (1 + exp(-k * (diff - 0.5))))
        else:
            return 0.0
    
    return _cmp
