"""
Fuzzy evaluation function for lazy streaming.

This module provides the core fuzzy evaluation logic used by the lazy streaming
system. It evaluates fuzzy queries on individual documents and returns
membership degrees.
"""

from typing import Any, Dict, List, Union
import re
import logging
from .default_preds import default_preds
from .utils import get_values_by_field_path

logger = logging.getLogger(__name__)


# Define unary and n-ary operators for fuzzy logic
UNARY_OPS = {
    'same': lambda x: x,
    'extremely': lambda x: x ** 3,
    'slightly': lambda x: x ** 0.1,
    'very': lambda x: x ** 2,
    'somewhat': lambda x: x ** 0.5,
    'not': lambda x: 1.0 - x
}

NARY_OPS = {
    'and': lambda *args: min(args) if args else 0.0,
    'or': lambda *args: max(args) if args else 0.0,
}


def fuzzy_eval(query: Union[List, str, float], doc: Dict) -> float:
    """
    Evaluate a fuzzy query expression against a single document.
    
    This function is the core of the fuzzy logic evaluation system,
    used by the lazy streaming infrastructure.
    
    Args:
        query: Fuzzy query expression (AST), string, or number
        doc: JSON document to evaluate against
        
    Returns:
        Membership degree in [0, 1]
    """
    preds = default_preds()
    
    def _eval(node: Any, document: Dict) -> float:
        # Handle literals
        if isinstance(node, (int, float)):
            return float(node)
        elif isinstance(node, str):
            # Handle field/path shortcuts
            if node.startswith(':'):
                # Field accessor - check existence
                field_path = node[1:]
                values = get_values_by_field_path(document, field_path)
                return 1.0 if values else 0.0
            elif node.startswith('@'):
                # Path accessor - check existence
                field_path = node[1:]
                values = get_values_by_field_path(document, field_path)
                return 1.0 if values else 0.0
            else:
                # String literal
                return 1.0
        elif not isinstance(node, list):
            return 1.0
        
        # Handle list expressions
        if not node:
            return 0.0
            
        op = node[0]
        operands = node[1:] if len(node) > 1 else []
        
        # Handle field/path operations
        if op == "field" or op == "path" or op == "@":
            if not operands:
                return 0.0
            field_path = operands[0]
            if isinstance(field_path, str):
                if field_path.startswith("@"):
                    field_path = field_path[1:]
                values = get_values_by_field_path(document, field_path)
                
                if len(operands) > 1:
                    # Apply predicate to field values
                    predicate = operands[1]
                    if not values:
                        return 0.0
                    degrees = []
                    for val in values:
                        if isinstance(predicate, list):
                            # Evaluate predicate on value
                            degree = _eval(predicate, {"value": val})
                        else:
                            # Direct comparison
                            degree = 1.0 if val == predicate else 0.0
                        degrees.append(degree)
                    # Use existential quantification (max)
                    return max(degrees) if degrees else 0.0
                else:
                    # Just existence check
                    return 1.0 if values else 0.0
            return 0.0
        
        # Handle exists operator
        elif op in ["exists", "exists?"]:
            if not operands:
                return 0.0
            field_path = operands[0]
            if isinstance(field_path, str):
                if field_path.startswith("@") or field_path.startswith(":"):
                    field_path = field_path[1:]
                values = get_values_by_field_path(document, field_path)
                return 1.0 if values else 0.0
            return 0.0
        
        # Handle fuzzy modifiers
        elif op in UNARY_OPS:
            if not operands:
                return 0.0
            operand_value = _eval(operands[0], document)
            return UNARY_OPS[op](operand_value)
        
        # Handle logical operators
        elif op in NARY_OPS:
            if not operands:
                return 0.0
            operand_values = [_eval(operand, document) for operand in operands]
            return NARY_OPS[op](*operand_values)
        
        # Handle comparison operators
        elif op in ["==", "eq?", "!=", "neq?", ">", "gt?", "<", "lt?", ">=", "gte?", "<=", "lte?"]:
            if len(operands) != 2:
                return 0.0
                
            left = operands[0]
            right = operands[1]
            
            # Extract values if they're field paths
            if isinstance(left, str) and (left.startswith("@") or left.startswith(":")):
                field_path = left[1:] if (left.startswith("@") or left.startswith(":")) else left
                left_values = get_values_by_field_path(document, field_path)
                left = left_values[0] if left_values else None
            elif isinstance(left, list):
                left = _eval(left, document)
                
            if isinstance(right, str) and (right.startswith("@") or right.startswith(":")):
                field_path = right[1:] if (right.startswith("@") or right.startswith(":")) else right
                right_values = get_values_by_field_path(document, field_path)
                right = right_values[0] if right_values else None
            elif isinstance(right, list):
                right = _eval(right, document)
            
            # Apply comparison directly (with fuzzy tolerance for numeric values)
            if left is None or right is None:
                return 0.0
                
            try:
                # Apply fuzzy membership functions for numeric comparisons
                if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                    # Fuzzy comparison with tolerance
                    epsilon = 0.01 * max(abs(left), abs(right), 1.0)  # Adaptive tolerance
                    
                    if op in ["==", "eq?"]:
                        # Triangular membership for equality
                        diff = abs(left - right)
                        if diff <= epsilon:
                            return 1.0 - (diff / epsilon)
                        return 0.0
                    elif op in ["!=", "neq?"]:
                        # Inverse of equality
                        diff = abs(left - right)
                        if diff <= epsilon:
                            return diff / epsilon
                        return 1.0
                    elif op in [">", "gt?"]:
                        # Fuzzy greater than
                        if left > right + epsilon:
                            return 1.0
                        elif left > right - epsilon:
                            return (left - (right - epsilon)) / (2 * epsilon)
                        return 0.0
                    elif op in ["<", "lt?"]:
                        # Fuzzy less than
                        if left < right - epsilon:
                            return 1.0
                        elif left < right + epsilon:
                            return ((right + epsilon) - left) / (2 * epsilon)
                        return 0.0
                    elif op in [">=", "gte?"]:
                        # Fuzzy greater than or equal
                        if left >= right - epsilon:
                            return 1.0
                        elif left >= right - 2*epsilon:
                            return (left - (right - 2*epsilon)) / epsilon
                        return 0.0
                    elif op in ["<=", "lte?"]:
                        # Fuzzy less than or equal
                        if left <= right + epsilon:
                            return 1.0
                        elif left <= right + 2*epsilon:
                            return ((right + 2*epsilon) - left) / epsilon
                        return 0.0
                else:
                    # Crisp comparison for non-numeric values
                    if op in ["==", "eq?"]:
                        return 1.0 if left == right else 0.0
                    elif op in ["!=", "neq?"]:
                        return 1.0 if left != right else 0.0
                    elif op in [">", "gt?"]:
                        return 1.0 if left > right else 0.0
                    elif op in ["<", "lt?"]:
                        return 1.0 if left < right else 0.0
                    elif op in [">=", "gte?"]:
                        return 1.0 if left >= right else 0.0
                    elif op in ["<=", "lte?"]:
                        return 1.0 if left <= right else 0.0
            except (TypeError, ValueError):
                return 0.0
        
        # Handle string predicates
        elif op in ["contains?", "starts-with?", "ends-with?", "regex?", "in?"]:
            if op in preds:
                eval_operands = []
                for operand in operands:
                    if isinstance(operand, str) and (operand.startswith("@") or operand.startswith(":")):
                        values = get_values_by_field_path(document, operand[1:])
                        eval_operands.append(values[0] if values else "")
                    elif isinstance(operand, list):
                        eval_operands.append(_eval(operand, document))
                    else:
                        eval_operands.append(operand)
                try:
                    return preds[op](eval_operands, document)
                except:
                    return 0.0
            return 0.0
        
        # Handle other predicates
        elif op in preds:
            eval_operands = []
            for operand in operands:
                if isinstance(operand, str) and (operand.startswith("@") or operand.startswith(":")):
                    values = get_values_by_field_path(document, operand[1:])
                    eval_operands.append(values[0] if values else None)
                elif isinstance(operand, list):
                    eval_operands.append(_eval(operand, document))
                else:
                    eval_operands.append(operand)
            try:
                return preds[op](eval_operands, document)
            except:
                return 0.0
        
        # Unknown operator
        return 0.0
    
    try:
        result = _eval(query, doc)
        # Ensure result is in [0, 1]
        return max(0.0, min(1.0, float(result)))
    except Exception as e:
        logger.debug(f"Error evaluating fuzzy query: {e}")
        return 0.0