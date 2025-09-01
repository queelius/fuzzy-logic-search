"""
Fuzzy Logic Search - A lazy streaming framework for fuzzy queries on JSON documents.

This package provides fuzzy logic-based querying using lazy evaluation,
enabling efficient processing of large datasets with continuous membership degrees.
"""

# Core classes
from .fuzzy_set import FuzzySet
from .fuzzy_eval import fuzzy_eval

# Lazy streaming classes
from .lazy_fuzzy_streams import (
    FuzzyLazyStream,
    FuzzyFilteredStream,
    FuzzyMappedStream,
    FuzzyModifiedStream,
    FuzzyThresholdStream,
    FuzzyTopKStream,
    FuzzyIntersectionStream,
    FuzzyUnionStream,
    fuzzy_stream
)

# Fuzzy set operations
from .fuzzy_set_algebra import (
    fuzzy_join,
    fuzzy_meet,
    fuzzy_cartesian_product
)

# Fuzzy modifiers
from .fuzzy_set_mods import (
    very,
    somewhat,
    slightly,
    extremely
)

# Defuzzification methods
from .defuzz_fuzzy_set import (
    defuzzify,
    defuzzify_centroid,
    defuzzify_bisector,
    defuzzify_mom,
    defuzzify_lom,
    defuzzify_som
)

# Utilities
from .utils import get_values_by_field_path
from .default_preds import default_preds

# Query parsing
from .query_parser import (
    FuzzyQueryParser,
    FuzzyQueryFormatter,
    parse_fuzzy_query,
    format_fuzzy_query,
    validate_query_syntax,
    FuzzyQueryBuilder
)

__version__ = "0.1.0"

__all__ = [
    # Core classes
    "FuzzySet",
    "fuzzy_eval",
    
    # Lazy streaming
    "FuzzyLazyStream",
    "FuzzyFilteredStream",
    "FuzzyMappedStream",
    "FuzzyModifiedStream",
    "FuzzyThresholdStream",
    "FuzzyTopKStream",
    "FuzzyIntersectionStream",
    "FuzzyUnionStream",
    "fuzzy_stream",
    
    # Operations
    "fuzzy_join",
    "fuzzy_meet",
    "fuzzy_cartesian_product",
    
    # Modifiers
    "very",
    "somewhat",
    "slightly",
    "extremely",
    
    # Defuzzification
    "defuzzify",
    "defuzzify_centroid",
    "defuzzify_bisector",
    "defuzzify_mom",
    "defuzzify_lom",
    "defuzzify_som",
    
    # Utilities
    "get_values_by_field_path",
    "default_preds",
    
    # Query parsing
    "FuzzyQueryParser",
    "FuzzyQueryFormatter",
    "parse_fuzzy_query",
    "format_fuzzy_query",
    "validate_query_syntax",
    "FuzzyQueryBuilder"
]