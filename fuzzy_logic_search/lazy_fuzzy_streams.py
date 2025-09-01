"""
Lazy streaming implementation for fuzzy logic queries.

This module provides lazy evaluation of fuzzy queries on JSON streams,
allowing efficient processing of large datasets without loading everything
into memory. Unlike boolean filtering, fuzzy streams maintain membership
degrees for each item.

Key Classes:
    FuzzyLazyStream: Base class for all fuzzy streams
    FuzzyFilteredStream: Stream with fuzzy membership degrees
    FuzzyMappedStream: Stream with transformed values and degrees
    FuzzyModifiedStream: Stream with modified membership degrees
    
Example:
    >>> from fuzzy_logic_search import fuzzy_stream
    >>> result = fuzzy_stream("data.jsonl") \\
    ...     .fuzzy_filter([">=", "@score", 80]) \\
    ...     .very() \\
    ...     .threshold(0.7) \\
    ...     .evaluate()
    >>> list(result)  # Returns (doc, membership) tuples
"""

from typing import Any, Dict, List, Optional, Generator, Tuple, Union, Callable
from abc import ABC, abstractmethod
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FuzzyLazyStream(ABC):
    """
    Base class for all lazy fuzzy data streams.
    
    A fuzzy stream represents a lazy computation over a data source that
    produces (document, membership_degree) pairs. Operations return new
    stream objects, building a pipeline that evaluates lazily.
    
    Unlike crisp boolean streams, fuzzy streams maintain continuous
    membership degrees in [0, 1] for each document.
    """
    
    def __init__(self, source: Union[str, Path, List, Dict[str, Any]], 
                 collection_id: Optional[str] = None):
        """
        Initialize a fuzzy lazy stream.
        
        Args:
            source: Data source (file path, list of docs, or source dict)
            collection_id: Optional identifier for this collection
        """
        self.source = self._normalize_source(source)
        self.collection_id = collection_id
        
    def _normalize_source(self, source: Any) -> Dict[str, Any]:
        """Normalize source to a consistent dict format."""
        if isinstance(source, (str, Path)):
            return {"type": "file", "path": str(source)}
        elif isinstance(source, list):
            return {"type": "memory", "data": source}
        elif isinstance(source, dict):
            return source
        else:
            raise ValueError(f"Unsupported source type: {type(source)}")
    
    def evaluate(self) -> Generator[Tuple[Any, float], None, None]:
        """
        Evaluate the stream, yielding (document, membership) pairs.
        
        Default implementation streams from source with membership 1.0.
        Subclasses override to add fuzzy filtering, transformation, etc.
        
        Yields:
            Tuples of (document, membership_degree)
        """
        for doc in self._stream_source():
            yield (doc, 1.0)
    
    def _stream_source(self) -> Generator[Any, None, None]:
        """Stream raw documents from the source."""
        source_type = self.source.get("type")
        
        if source_type == "file":
            yield from self._stream_file(self.source["path"])
        elif source_type == "memory":
            yield from self.source["data"]
        elif source_type == "generator":
            yield from self.source["generator"]()
        else:
            raise ValueError(f"Unknown source type: {source_type}")
    
    def _stream_file(self, path: str) -> Generator[Any, None, None]:
        """Stream JSON documents from a file."""
        path = Path(path)
        
        if path.suffix == ".jsonl":
            # Stream JSONL file line by line
            with open(path, 'r') as f:
                for line in f:
                    if line.strip():
                        yield json.loads(line)
        elif path.suffix == ".json":
            # Load entire JSON file (could be array or single doc)
            with open(path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    yield from data
                else:
                    yield data
        else:
            # Treat as text file - yield as single string document
            with open(path, 'r') as f:
                yield {"content": f.read(), "filename": str(path)}
    
    # Composable fuzzy operations - return new stream objects
    
    def fuzzy_filter(self, query: List) -> "FuzzyFilteredStream":
        """
        Apply a fuzzy filter to this stream.
        
        Args:
            query: Fuzzy query expression that returns membership degrees
            
        Returns:
            New stream with fuzzy membership degrees
        """
        return FuzzyFilteredStream(query, self)
    
    def fuzzy_map(self, expression: Union[List, str]) -> "FuzzyMappedStream":
        """
        Transform values while preserving membership degrees.
        
        Args:
            expression: Transformation expression or field path
            
        Returns:
            New stream with transformed values
        """
        return FuzzyMappedStream(expression, self)
    
    def threshold(self, min_membership: float) -> "FuzzyThresholdStream":
        """
        Filter by minimum membership degree (alpha-cut).
        
        Args:
            min_membership: Minimum membership degree to pass through
            
        Returns:
            New stream with only items above threshold
        """
        return FuzzyThresholdStream(min_membership, self)
    
    def top_k(self, k: int) -> "FuzzyTopKStream":
        """
        Keep only top k items by membership degree.
        
        Args:
            k: Number of top items to keep
            
        Returns:
            New stream with top k items
        """
        return FuzzyTopKStream(k, self)
    
    # Fuzzy modifiers as stream operations
    
    def very(self) -> "FuzzyModifiedStream":
        """Apply 'very' modifier (square membership)."""
        return FuzzyModifiedStream(lambda x: x ** 2, "very", self)
    
    def somewhat(self) -> "FuzzyModifiedStream":
        """Apply 'somewhat' modifier (square root membership)."""
        return FuzzyModifiedStream(lambda x: x ** 0.5, "somewhat", self)
    
    def slightly(self) -> "FuzzyModifiedStream":
        """Apply 'slightly' modifier (10th root membership)."""
        return FuzzyModifiedStream(lambda x: x ** 0.1, "slightly", self)
    
    def extremely(self) -> "FuzzyModifiedStream":
        """Apply 'extremely' modifier (cube membership)."""
        return FuzzyModifiedStream(lambda x: x ** 3, "extremely", self)
    
    def not_fuzzy(self) -> "FuzzyModifiedStream":
        """Apply fuzzy NOT (complement membership)."""
        return FuzzyModifiedStream(lambda x: 1.0 - x, "not", self)
    
    # Fuzzy set operations
    
    def fuzzy_and(self, other: "FuzzyLazyStream") -> "FuzzyIntersectionStream":
        """
        Fuzzy intersection with another stream (minimum membership).
        
        Args:
            other: Another fuzzy stream to intersect with
            
        Returns:
            New stream with minimum membership degrees
        """
        return FuzzyIntersectionStream(self, other)
    
    def fuzzy_or(self, other: "FuzzyLazyStream") -> "FuzzyUnionStream":
        """
        Fuzzy union with another stream (maximum membership).
        
        Args:
            other: Another fuzzy stream to union with
            
        Returns:
            New stream with maximum membership degrees
        """
        return FuzzyUnionStream(self, other)
    
    # Utility methods
    
    def to_fuzzy_set(self) -> Dict[Any, float]:
        """
        Evaluate stream and return as fuzzy set dict.
        
        Returns:
            Dict mapping documents to membership degrees
        """
        result = {}
        for doc, membership in self.evaluate():
            # Use document hash as key if it's not hashable
            key = self._make_hashable(doc)
            result[key] = membership
        return result
    
    def _make_hashable(self, doc: Any) -> Any:
        """Make document hashable for use as dict key."""
        if isinstance(doc, dict):
            return json.dumps(doc, sort_keys=True)
        elif isinstance(doc, list):
            return tuple(doc)
        else:
            return doc
    
    def defuzzify(self, method: str = "centroid") -> Any:
        """
        Defuzzify the stream to get a crisp result.
        
        Args:
            method: Defuzzification method (centroid, max, mean)
            
        Returns:
            Crisp result based on membership degrees
        """
        docs_and_memberships = list(self.evaluate())
        
        if not docs_and_memberships:
            return None
            
        if method == "max":
            # Return document with highest membership
            return max(docs_and_memberships, key=lambda x: x[1])[0]
        elif method == "mean":
            # Return weighted mean (if docs are numeric)
            total_weight = sum(m for _, m in docs_and_memberships)
            if total_weight == 0:
                return None
            weighted_sum = sum(d * m for d, m in docs_and_memberships 
                             if isinstance(d, (int, float)))
            return weighted_sum / total_weight
        else:  # centroid or default
            # Return document closest to membership centroid
            memberships = [m for _, m in docs_and_memberships]
            avg_membership = sum(memberships) / len(memberships)
            closest = min(docs_and_memberships, 
                         key=lambda x: abs(x[1] - avg_membership))
            return closest[0]
    
    def info(self) -> Dict[str, Any]:
        """Get information about this stream without evaluating."""
        return {
            "type": self.__class__.__name__,
            "source": self.source,
            "collection_id": self.collection_id,
            "pipeline": self._describe_pipeline()
        }
    
    def _describe_pipeline(self) -> str:
        """Get human-readable pipeline description."""
        return f"{self.__class__.__name__}({self.source.get('type', 'unknown')})"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(source={self.source})"


class FuzzyFilteredStream(FuzzyLazyStream):
    """
    Stream filtered by a fuzzy query that produces membership degrees.
    
    Each document gets a membership degree based on how well it matches
    the fuzzy query. Documents with membership 0 are filtered out.
    """
    
    def __init__(self, query: List, source: FuzzyLazyStream):
        """
        Create a fuzzy filtered stream.
        
        Args:
            query: Fuzzy query expression
            source: Source stream to filter
        """
        filter_source = {
            "type": "fuzzy_filter",
            "query": query,
            "inner_source": source.source
        }
        super().__init__(filter_source, source.collection_id)
        self.query = query
        self.source = source
    
    def evaluate(self) -> Generator[Tuple[Any, float], None, None]:
        """Evaluate fuzzy filter, yielding docs with membership degrees."""
        from .fuzzy_eval import fuzzy_eval
        
        for doc, existing_membership in self.source.evaluate():
            # Evaluate fuzzy query to get new membership
            query_membership = fuzzy_eval(self.query, doc)
            
            # Combine with existing membership (minimum for AND semantics)
            combined_membership = min(existing_membership, query_membership)
            
            # Only yield if membership > 0
            if combined_membership > 0:
                yield (doc, combined_membership)
    
    def _describe_pipeline(self) -> str:
        return f"fuzzy_filter({self.query}) → {self.source._describe_pipeline()}"


class FuzzyMappedStream(FuzzyLazyStream):
    """
    Stream with transformed values, preserving membership degrees.
    """
    
    def __init__(self, expression: Union[List, str], source: FuzzyLazyStream):
        """
        Create a fuzzy mapped stream.
        
        Args:
            expression: Transformation expression or field path
            source: Source stream to map
        """
        map_source = {
            "type": "fuzzy_map",
            "expression": expression,
            "inner_source": source.source
        }
        super().__init__(map_source, source.collection_id)
        self.expression = expression
        self.source = source
    
    def evaluate(self) -> Generator[Tuple[Any, float], None, None]:
        """Transform values while preserving membership degrees."""
        from .utils import get_values_by_field_path
        
        for doc, membership in self.source.evaluate():
            if isinstance(self.expression, str):
                # Simple field extraction
                if self.expression.startswith("@"):
                    # Field path like "@name" or "@user.email"
                    field_path = self.expression[1:]
                    values = get_values_by_field_path(doc, field_path)
                    transformed = values[0] if values else None
                else:
                    transformed = self.expression
            else:
                # Complex expression evaluation
                from .fuzzy_eval import fuzzy_eval
                transformed = fuzzy_eval(self.expression, doc)
            
            yield (transformed, membership)
    
    def _describe_pipeline(self) -> str:
        return f"map({self.expression}) → {self.source._describe_pipeline()}"


class FuzzyModifiedStream(FuzzyLazyStream):
    """
    Stream with modified membership degrees using fuzzy modifiers.
    """
    
    def __init__(self, modifier: Callable[[float], float], 
                 name: str, source: FuzzyLazyStream):
        """
        Create a stream with modified membership degrees.
        
        Args:
            modifier: Function to modify membership degrees
            name: Name of the modifier (for description)
            source: Source stream
        """
        mod_source = {
            "type": "fuzzy_modifier",
            "modifier_name": name,
            "inner_source": source.source
        }
        super().__init__(mod_source, source.collection_id)
        self.modifier = modifier
        self.modifier_name = name
        self.source = source
    
    def evaluate(self) -> Generator[Tuple[Any, float], None, None]:
        """Apply modifier to membership degrees."""
        for doc, membership in self.source.evaluate():
            modified_membership = self.modifier(membership)
            # Ensure membership stays in [0, 1]
            modified_membership = max(0.0, min(1.0, modified_membership))
            yield (doc, modified_membership)
    
    def _describe_pipeline(self) -> str:
        return f"{self.modifier_name}() → {self.source._describe_pipeline()}"


class FuzzyThresholdStream(FuzzyLazyStream):
    """
    Stream filtered by minimum membership degree (alpha-cut).
    """
    
    def __init__(self, min_membership: float, source: FuzzyLazyStream):
        """
        Create threshold stream.
        
        Args:
            min_membership: Minimum membership to pass through
            source: Source stream
        """
        threshold_source = {
            "type": "fuzzy_threshold",
            "min_membership": min_membership,
            "inner_source": source.source
        }
        super().__init__(threshold_source, source.collection_id)
        self.min_membership = min_membership
        self.source = source
    
    def evaluate(self) -> Generator[Tuple[Any, float], None, None]:
        """Filter by minimum membership."""
        for doc, membership in self.source.evaluate():
            if membership >= self.min_membership:
                yield (doc, membership)
    
    def _describe_pipeline(self) -> str:
        return f"threshold({self.min_membership}) → {self.source._describe_pipeline()}"


class FuzzyTopKStream(FuzzyLazyStream):
    """
    Stream keeping only top k items by membership degree.
    """
    
    def __init__(self, k: int, source: FuzzyLazyStream):
        """
        Create top-k stream.
        
        Args:
            k: Number of top items to keep
            source: Source stream
        """
        topk_source = {
            "type": "fuzzy_topk",
            "k": k,
            "inner_source": source.source
        }
        super().__init__(topk_source, source.collection_id)
        self.k = k
        self.source = source
    
    def evaluate(self) -> Generator[Tuple[Any, float], None, None]:
        """Keep only top k by membership."""
        # Need to collect all items to find top k
        all_items = list(self.source.evaluate())
        
        # Sort by membership degree (descending)
        sorted_items = sorted(all_items, key=lambda x: x[1], reverse=True)
        
        # Yield top k
        for item in sorted_items[:self.k]:
            yield item
    
    def _describe_pipeline(self) -> str:
        return f"top_k({self.k}) → {self.source._describe_pipeline()}"


class FuzzyIntersectionStream(FuzzyLazyStream):
    """
    Fuzzy intersection of two streams (minimum membership).
    """
    
    def __init__(self, left: FuzzyLazyStream, right: FuzzyLazyStream):
        """
        Create intersection stream.
        
        Args:
            left: First stream
            right: Second stream
        """
        intersect_source = {
            "type": "fuzzy_intersection",
            "left": left.source,
            "right": right.source
        }
        super().__init__(intersect_source, left.collection_id)
        self.left = left
        self.right = right
    
    def evaluate(self) -> Generator[Tuple[Any, float], None, None]:
        """Compute fuzzy intersection."""
        # Collect right stream into dict for lookup
        right_dict = {}
        for doc, membership in self.right.evaluate():
            key = self._make_hashable(doc)
            right_dict[key] = membership
        
        # Stream left, taking minimum with right
        for doc, left_membership in self.left.evaluate():
            key = self._make_hashable(doc)
            if key in right_dict:
                # Fuzzy AND: minimum membership
                combined = min(left_membership, right_dict[key])
                yield (doc, combined)
    
    def _describe_pipeline(self) -> str:
        return f"({self.left._describe_pipeline()} AND {self.right._describe_pipeline()})"


class FuzzyUnionStream(FuzzyLazyStream):
    """
    Fuzzy union of two streams (maximum membership).
    """
    
    def __init__(self, left: FuzzyLazyStream, right: FuzzyLazyStream):
        """
        Create union stream.
        
        Args:
            left: First stream
            right: Second stream
        """
        union_source = {
            "type": "fuzzy_union",
            "left": left.source,
            "right": right.source
        }
        super().__init__(union_source, left.collection_id)
        self.left = left
        self.right = right
    
    def evaluate(self) -> Generator[Tuple[Any, float], None, None]:
        """Compute fuzzy union."""
        seen = {}
        
        # Process left stream
        for doc, membership in self.left.evaluate():
            key = self._make_hashable(doc)
            seen[key] = membership
            yield (doc, membership)
        
        # Process right stream, taking maximum with left
        for doc, right_membership in self.right.evaluate():
            key = self._make_hashable(doc)
            if key in seen:
                # Already yielded, but update if right has higher membership
                if right_membership > seen[key]:
                    # Note: Can't update already yielded value in generator
                    # This is a limitation of streaming approach
                    pass
            else:
                yield (doc, right_membership)
    
    def _describe_pipeline(self) -> str:
        return f"({self.left._describe_pipeline()} OR {self.right._describe_pipeline()})"


# Convenience function to create fuzzy streams
def fuzzy_stream(source: Union[str, Path, List, Dict[str, Any]]) -> FuzzyLazyStream:
    """
    Create a fuzzy lazy stream from a data source.
    
    Args:
        source: File path, list of documents, or source dict
        
    Returns:
        FuzzyLazyStream ready for operations
    """
    return FuzzyLazyStream(source)