import re
import logging

# initialize logging
logging.basicConfig(level=logging.INFO)

def crisp_membership_generator(throw_on_error=False) -> callable:
    """
    Returns a boolean (0,1) score function for fuzzy comparisons. This means
    the fuzzy logic is reduced to a classic boolean logic.

    Returns:
    - callable: A function that computes a degree of membership for comparison
        operators.
    """
    def _cmp(observed, target, op: str) -> float:
        try:
            if op == '==':
                return float(observed == target)
            elif op == '!=':
                return float(observed != target)
            elif op == '>':
                return float(observed > target)
            elif op == '>=':
                return float(observed >= target)
            elif op == '<':
                return float(observed < target)
            elif op == '<=':
                return float(observed <= target)
            elif op == 'startswith':
                return float(observed.startswith(target))
            elif op == 'endswith':
                return float(observed.endswith(target))
            elif op == 'matches':
                pat = re.compile(target, re.IGNORECASE)
                return float(pat.match(observed))
            else: # default to op == 'in'
                return float(observed in target)
        except Exception as e:
            if throw_on_error:
                raise e
            logging.error(f"Error: {e} | op='{op}' | observed type={type(observed)}, target type={type(target)}")
            return 0.0        
            
    return _cmp
