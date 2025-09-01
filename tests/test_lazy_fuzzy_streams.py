"""
Tests for lazy fuzzy streaming functionality.
"""

import unittest
import json
import tempfile
import os
from pathlib import Path

from fuzzy_logic_search import (
    FuzzyLazyStream,
    fuzzy_stream,
    fuzzy_eval
)


class TestFuzzyLazyStreams(unittest.TestCase):
    """Test suite for lazy fuzzy streaming."""
    
    def setUp(self):
        """Set up test data."""
        self.test_docs = [
            {"name": "Alice", "age": 25, "score": 85},
            {"name": "Bob", "age": 30, "score": 92},
            {"name": "Charlie", "age": 35, "score": 78},
            {"name": "David", "age": 28, "score": 88},
            {"name": "Eve", "age": 22, "score": 95}
        ]
    
    def test_basic_stream_creation(self):
        """Test creating streams from different sources."""
        # From list
        stream1 = fuzzy_stream(self.test_docs)
        self.assertIsInstance(stream1, FuzzyLazyStream)
        
        # Evaluate and check results
        results = list(stream1.evaluate())
        self.assertEqual(len(results), 5)
        
        # Each result should be (doc, membership) tuple
        for doc, membership in results:
            self.assertIn(doc, self.test_docs)
            self.assertEqual(membership, 1.0)  # Default membership
    
    def test_fuzzy_filter(self):
        """Test fuzzy filtering with membership degrees."""
        stream = fuzzy_stream(self.test_docs)
        
        # Filter by score >= 80 (fuzzy comparison)
        filtered = stream.fuzzy_filter([">=", "@score", 80])
        results = list(filtered.evaluate())
        
        # Should have items with score >= 80
        high_scorers = [d for d in self.test_docs if d["score"] >= 80]
        self.assertEqual(len(results), len(high_scorers))
        
        for doc, membership in results:
            self.assertGreaterEqual(doc["score"], 78)  # Some fuzzy tolerance
            self.assertGreater(membership, 0)
            self.assertLessEqual(membership, 1.0)
    
    def test_fuzzy_modifiers(self):
        """Test fuzzy modifiers (very, somewhat, etc.)."""
        stream = fuzzy_stream(self.test_docs)
        
        # Apply filter then modifier
        filtered = stream.fuzzy_filter([">=", "@score", 85])
        very_filtered = filtered.very()
        
        results = list(very_filtered.evaluate())
        
        # Very modifier should square membership degrees
        for doc, membership in results:
            self.assertGreater(membership, 0)
            self.assertLessEqual(membership, 1.0)
    
    def test_threshold_filtering(self):
        """Test threshold filtering by minimum membership."""
        stream = fuzzy_stream(self.test_docs)
        
        # Filter and apply threshold
        filtered = stream.fuzzy_filter([">=", "@score", 85])
        thresholded = filtered.threshold(0.5)
        
        results = list(thresholded.evaluate())
        
        # All results should have membership >= 0.5
        for doc, membership in results:
            self.assertGreaterEqual(membership, 0.5)
    
    def test_top_k(self):
        """Test top-k selection by membership degree."""
        stream = fuzzy_stream(self.test_docs)
        
        # Filter and get top 3
        filtered = stream.fuzzy_filter([">=", "@score", 70])
        top3 = filtered.top_k(3)
        
        results = list(top3.evaluate())
        
        # Should have exactly 3 results
        self.assertEqual(len(results), 3)
        
        # Should be sorted by membership (descending)
        memberships = [m for _, m in results]
        self.assertEqual(memberships, sorted(memberships, reverse=True))
    
    def test_fuzzy_map(self):
        """Test value transformation with membership preservation."""
        stream = fuzzy_stream(self.test_docs)
        
        # Filter then map to extract names
        filtered = stream.fuzzy_filter([">=", "@age", 25])
        mapped = filtered.fuzzy_map("@name")
        
        results = list(mapped.evaluate())
        
        # Should have transformed values (names) with memberships
        for value, membership in results:
            self.assertIsInstance(value, str)  # Names are strings
            self.assertGreater(membership, 0)
            self.assertLessEqual(membership, 1.0)
    
    def test_fuzzy_set_operations(self):
        """Test fuzzy AND/OR operations on streams."""
        stream1 = fuzzy_stream(self.test_docs)
        stream2 = fuzzy_stream(self.test_docs)
        
        # Two different filters
        age_filter = stream1.fuzzy_filter([">=", "@age", 25])
        score_filter = stream2.fuzzy_filter([">=", "@score", 85])
        
        # Fuzzy AND (intersection)
        intersection = age_filter.fuzzy_and(score_filter)
        and_results = list(intersection.evaluate())
        
        # Fuzzy OR (union)
        union = age_filter.fuzzy_or(score_filter)
        or_results = list(union.evaluate())
        
        # Union should have at least as many as intersection
        self.assertGreaterEqual(len(or_results), len(and_results))
    
    def test_chained_operations(self):
        """Test chaining multiple operations."""
        stream = fuzzy_stream(self.test_docs)
        
        # Complex pipeline
        result = (stream
            .fuzzy_filter([">=", "@score", 80])
            .somewhat()  # Broaden membership
            .threshold(0.3)
            .fuzzy_map("@name")
            .top_k(2))
        
        final_results = list(result.evaluate())
        
        # Should have at most 2 results (top_k)
        self.assertLessEqual(len(final_results), 2)
        
        # Values should be names
        for value, membership in final_results:
            self.assertIsInstance(value, str)
    
    def test_file_streaming(self):
        """Test streaming from files."""
        # Create temporary JSONL file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for doc in self.test_docs:
                f.write(json.dumps(doc) + '\n')
            temp_file = f.name
        
        try:
            # Stream from file
            stream = fuzzy_stream(temp_file)
            filtered = stream.fuzzy_filter([">=", "@score", 85])
            
            results = list(filtered.evaluate())
            
            # Should have filtered results
            self.assertGreater(len(results), 0)
            
            for doc, membership in results:
                self.assertIsInstance(doc, dict)
                self.assertIn("score", doc)
                self.assertGreaterEqual(doc["score"], 85)
        
        finally:
            # Clean up
            os.unlink(temp_file)
    
    def test_fuzzy_complement(self):
        """Test fuzzy NOT operation."""
        stream = fuzzy_stream(self.test_docs)
        
        # Filter then complement
        filtered = stream.fuzzy_filter([">=", "@score", 85])
        complemented = filtered.not_fuzzy()
        
        results = list(complemented.evaluate())
        
        # Complement should invert membership degrees
        for doc, membership in results:
            self.assertGreaterEqual(membership, 0)
            self.assertLessEqual(membership, 1.0)
    
    def test_defuzzification(self):
        """Test defuzzification methods."""
        stream = fuzzy_stream(self.test_docs)
        
        # Filter and defuzzify
        filtered = stream.fuzzy_filter([">=", "@score", 80])
        
        # Max defuzzification - get doc with highest membership
        max_doc = filtered.defuzzify(method="max")
        self.assertIsInstance(max_doc, dict)
        self.assertIn("score", max_doc)
    
    def test_complex_fuzzy_query(self):
        """Test complex fuzzy queries with logical operations."""
        stream = fuzzy_stream(self.test_docs)
        
        # Complex query: (age >= 25 AND score >= 85) OR name starts with 'E'
        complex_query = [
            "or",
            ["and",
                [">=", "@age", 25],
                [">=", "@score", 85]
            ],
            ["starts-with?", "@name", "E"]
        ]
        
        filtered = stream.fuzzy_filter(complex_query)
        results = list(filtered.evaluate())
        
        # Should have results matching the complex condition
        self.assertGreater(len(results), 0)
        
        for doc, membership in results:
            # Check that docs match at least one condition
            matches_age_score = doc["age"] >= 25 and doc["score"] >= 85
            matches_name = doc["name"].startswith("E")
            self.assertTrue(matches_age_score or matches_name)
    
    def test_stream_info(self):
        """Test stream information methods."""
        stream = fuzzy_stream(self.test_docs)
        filtered = stream.fuzzy_filter([">=", "@score", 85])
        modified = filtered.very()
        
        # Get info without evaluating
        info = modified.info()
        
        self.assertIsInstance(info, dict)
        self.assertIn("type", info)
        self.assertIn("pipeline", info)
    
    def test_empty_stream(self):
        """Test handling of empty streams."""
        stream = fuzzy_stream([])
        filtered = stream.fuzzy_filter([">=", "@score", 85])
        
        results = list(filtered.evaluate())
        self.assertEqual(len(results), 0)
    
    def test_membership_combination(self):
        """Test how membership degrees combine through operations."""
        # Create docs with known values
        test_doc = {"value": 50}
        stream = fuzzy_stream([test_doc])
        
        # Apply multiple filters that should reduce membership
        filtered1 = stream.fuzzy_filter([">=", "@value", 40])  # Should pass
        filtered2 = filtered1.fuzzy_filter(["<=", "@value", 60])  # Should pass
        
        results = list(filtered2.evaluate())
        
        # Should have one result with combined membership
        self.assertEqual(len(results), 1)
        doc, membership = results[0]
        self.assertEqual(doc, test_doc)
        self.assertGreater(membership, 0)
        self.assertLessEqual(membership, 1.0)


class TestFuzzyEval(unittest.TestCase):
    """Test the fuzzy_eval function."""
    
    def test_simple_comparison(self):
        """Test simple fuzzy comparisons."""
        doc = {"age": 25, "score": 85}
        
        # Test equality
        membership = fuzzy_eval(["==", "@age", 25], doc)
        self.assertAlmostEqual(membership, 1.0)
        
        # Test inequality
        membership = fuzzy_eval([">=", "@score", 80], doc)
        self.assertGreater(membership, 0)
        self.assertLessEqual(membership, 1.0)
    
    def test_logical_operations(self):
        """Test fuzzy logical operations."""
        doc = {"age": 25, "score": 85}
        
        # AND operation
        membership = fuzzy_eval(
            ["and", [">=", "@age", 20], [">=", "@score", 80]],
            doc
        )
        self.assertGreater(membership, 0)
        
        # OR operation
        membership = fuzzy_eval(
            ["or", [">=", "@age", 30], [">=", "@score", 80]],
            doc
        )
        self.assertGreater(membership, 0)
        
        # NOT operation
        membership = fuzzy_eval(
            ["not", [">=", "@age", 30]],
            doc
        )
        self.assertGreater(membership, 0)
    
    def test_fuzzy_modifiers(self):
        """Test fuzzy modifiers in eval."""
        doc = {"score": 85}
        
        # Very modifier
        base_membership = fuzzy_eval([">=", "@score", 80], doc)
        very_membership = fuzzy_eval(["very", [">=", "@score", 80]], doc)
        
        # Very should reduce membership (square it)
        self.assertLess(very_membership, base_membership)
        
        # Somewhat modifier
        somewhat_membership = fuzzy_eval(["somewhat", [">=", "@score", 80]], doc)
        
        # Somewhat should increase membership (square root)
        self.assertGreater(somewhat_membership, base_membership)
    
    def test_field_existence(self):
        """Test field existence checks."""
        doc = {"name": "Alice", "age": 25}
        
        # Existing field
        membership = fuzzy_eval(["exists?", "@name"], doc)
        self.assertEqual(membership, 1.0)
        
        # Non-existing field
        membership = fuzzy_eval(["exists?", "@missing"], doc)
        self.assertEqual(membership, 0.0)
    
    def test_nested_fields(self):
        """Test nested field access."""
        doc = {"user": {"name": "Alice", "profile": {"age": 25}}}
        
        # Nested field access
        membership = fuzzy_eval(["==", "@user.name", "Alice"], doc)
        self.assertAlmostEqual(membership, 1.0)
        
        # Deeply nested
        membership = fuzzy_eval([">=", "@user.profile.age", 20], doc)
        self.assertGreater(membership, 0)


if __name__ == "__main__":
    unittest.main()