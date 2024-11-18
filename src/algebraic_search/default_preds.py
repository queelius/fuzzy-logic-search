import re
from typing import List, Callable, Any, Dict
from .utils import get_values_by_field_path, field_path_count

def default_preds():
    """
    Returns a dictionary mapping predicates to default (crisp) membership
    functions (which reduces to classical Boolean logic).
    """

    def _startswith(ob, doc, quant=all) -> float:
        """
        Tests if an object starts with a target string.
        """
        if isinstance(ob, list):
            return float(quant(str(doc).startswith(str(o)) for o in ob))
        else:
            return float(str(doc).startswith(str(ob)))
        
    def _endswith(ob, doc, quant=all) -> float:
        """
        Tests if an object ends with a target string.
        """
        if isinstance(ob, list):
            return float(quant(str(doc).endswith(str(o)) for o in ob))
        else:
            return float(str(doc).endswith(str(ob)))
        
    def _contains(ob, doc, quant=all) -> float:
        """
        Tests if an object contains another object.

        For example: 'a' in ['a', 'b', 'c'] is True.
        """
        if isinstance(ob, list):
            return float(quant(str(o) in str(doc) for o in ob))
        else:
            return float(str(ob) in str(doc))
        
    def _eq(ob: Any, doc: Any, quant=all) -> float:
        """
        Tests if two objects are equal.
        """
        if isinstance(ob, list):
            return float(quant(o == doc for o in ob))
        else:
            return float(ob == doc)
        
    def _not_eq(ob, doc: Any, quant=all) -> float:
        """
        Tests if two objects are not equal.
        """
        if isinstance(ob, list):
            return float(quant(o != doc for o in ob))
        else:
            return float(ob != doc)
        
    def _gt(ob, doc, quant=all) -> float:
        """
        Tests if an object is greater than another object.
        """
        if isinstance(ob, list):
            return float(quant(o > doc for o in ob))
        else:
            return float(ob > doc)
        
    def _gte(ob, doc, quant=all) -> float:
        """
        Tests if an object is greater than or equal to another object.
        """
        if isinstance(ob, list):
            return float(quant(o >= doc for o in ob))
        else:
            return float(ob >= doc)
        
    def _lt(ob, doc, quant=all) -> float:
        """
        Tests if an object is less than another object.
        """
        if isinstance(ob, list):
            return float(quant(o < doc for o in ob))
        else:
            return float(ob < doc)
        
    def _lte(ob, doc, quant=all):
        """
        Tests if an object is less than or equal to another object.
        """
        if isinstance(ob, list):
            return float(quant(o <= doc for o in ob))
        else:
            return float(ob <= doc)
        
    def _exists(field_path: str, doc: Any, quant=all) -> float:
        """
        Tests if an object exists in the doc.
        """

        count = field_path_count(doc, field_path)
        print(f"exists: field path {count=} for {field_path=} in {doc=}")
        return float(count > 0)
        
    def _matches(ob, doc, quant=all) -> float:
        """
        Tests if an object matches a regular expression.
        """
        if isinstance(ob, list):
            return float(quant(re.search(str(o), str(doc)) for o in ob))
        else:
            return float(re.search(str(ob), str(doc)))
        

    return {
        # universal quantifiers (all = for all, none = for none, any = for any)
        'all': lambda degrees: min(degrees),
        'any': lambda degrees: max(degrees),
        'none': lambda degrees: 1 - max(degrees),
        'exists': _exists,

        # comparison operators
        '==': _eq,
        '!=': _not_eq,
        '>': _gt,
        '>=': _gte,
        '<': _lt,
        '<=': _lte,

        # string comparison operators
        'startswith': _startswith,
        'endswith': _endswith,        
        'contains': _contains,

        # test if an object matches a regular expression
        'matches': _matches
    }


