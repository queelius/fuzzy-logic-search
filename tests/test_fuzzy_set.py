"""
Comprehensive test suite for FuzzySet operations.
Tests all basic operations, properties, and edge cases.
"""

import unittest
import pytest
from fuzzy_logic_search.fuzzy_set import FuzzySet


class TestFuzzySetOperations(unittest.TestCase):
    """Tests for core FuzzySet operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.fs1 = FuzzySet([0.8, 0.6, 0.4, 0.2])
        self.fs2 = FuzzySet([0.7, 0.9, 0.3, 0.5])
        self.fs3 = FuzzySet([1.0, 0.0, 0.5, 0.25])
        self.empty = FuzzySet([])
        self.single = FuzzySet([0.5])

    def test_initialization(self):
        """Test FuzzySet initialization."""
        fs = FuzzySet([0.1, 0.5, 0.9])
        self.assertEqual(fs.memberships, [0.1, 0.5, 0.9])

    def test_initialization_invalid_values(self):
        """Test that invalid membership values raise errors."""
        with self.assertRaises(ValueError):
            FuzzySet([0.5, 1.2, 0.3])  # Value > 1
        with self.assertRaises(ValueError):
            FuzzySet([-0.1, 0.5, 0.3])  # Value < 0

    def test_intersection(self):
        """Test fuzzy intersection (AND) operation."""
        result = self.fs1 & self.fs2
        expected = FuzzySet([0.7, 0.6, 0.3, 0.2])
        self.assertEqual(result, expected)

    def test_union(self):
        """Test fuzzy union (OR) operation."""
        result = self.fs1 | self.fs2
        expected = FuzzySet([0.8, 0.9, 0.4, 0.5])
        self.assertEqual(result, expected)

    def test_complement(self):
        """Test fuzzy complement (NOT) operation."""
        result = ~self.fs1
        expected = FuzzySet([0.2, 0.4, 0.6, 0.8])
        self.assertEqual(result, expected)

    def test_symmetric_difference(self):
        """Test fuzzy symmetric difference (XOR) operation."""
        result = self.fs1 ^ self.fs2
        # (A & ~B) | (~A & B)
        # A = [0.8, 0.6, 0.4, 0.2], B = [0.7, 0.9, 0.3, 0.5]
        # ~B = [0.3, 0.1, 0.7, 0.5]
        # A & ~B = [0.3, 0.1, 0.4, 0.2]
        # ~A = [0.2, 0.4, 0.6, 0.8]
        # ~A & B = [0.2, 0.4, 0.3, 0.5]
        # Result = [0.3, 0.4, 0.4, 0.5]
        expected = FuzzySet([0.3, 0.4, 0.4, 0.5])
        self.assertEqual(result, expected)

    def test_difference(self):
        """Test fuzzy difference (SUB) operation."""
        result = self.fs1 - self.fs2
        # A & ~B where A = [0.8, 0.6, 0.4, 0.2], B = [0.7, 0.9, 0.3, 0.5]
        # ~B = [0.3, 0.1, 0.7, 0.5]
        # A & ~B = [0.3, 0.1, 0.4, 0.2]
        expected = FuzzySet([0.3, 0.1, 0.4, 0.2])
        self.assertEqual(result, expected)

    def test_operations_with_mismatched_lengths(self):
        """Test that operations with mismatched lengths raise errors."""
        fs_short = FuzzySet([0.5, 0.5])

        with self.assertRaises(ValueError):
            _ = self.fs1 & fs_short
        with self.assertRaises(ValueError):
            _ = self.fs1 | fs_short
        with self.assertRaises(ValueError):
            _ = self.fs1 ^ fs_short
        with self.assertRaises(ValueError):
            _ = self.fs1 - fs_short

    def test_empty_set_operations(self):
        """Test operations with empty sets."""
        empty1 = FuzzySet([])
        empty2 = FuzzySet([])

        result = empty1 & empty2
        self.assertEqual(result, empty1)

        result = empty1 | empty2
        self.assertEqual(result, empty1)

        result = ~empty1
        self.assertEqual(result, empty1)


class TestFuzzySetSequenceProtocol(unittest.TestCase):
    """Tests for FuzzySet sequence protocol methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.fs = FuzzySet([0.8, 0.6, 0.4, 0.2])

    def test_getitem(self):
        """Test element access via indexing."""
        self.assertEqual(self.fs[0], 0.8)
        self.assertEqual(self.fs[1], 0.6)
        self.assertEqual(self.fs[-1], 0.2)

    def test_setitem(self):
        """Test element modification via indexing."""
        self.fs[1] = 0.7
        self.assertEqual(self.fs[1], 0.7)

    def test_setitem_invalid_value(self):
        """Test that setting invalid values raises errors."""
        with self.assertRaises(ValueError):
            self.fs[0] = 1.5
        with self.assertRaises(ValueError):
            self.fs[0] = -0.1

    def test_len(self):
        """Test length operation."""
        self.assertEqual(len(self.fs), 4)
        self.assertEqual(len(FuzzySet([])), 0)
        self.assertEqual(len(FuzzySet([0.5])), 1)

    def test_iter(self):
        """Test iteration over FuzzySet."""
        values = list(self.fs)
        self.assertEqual(values, [0.8, 0.6, 0.4, 0.2])

    def test_contains(self):
        """Test membership checking."""
        self.assertTrue(0.8 in self.fs)
        self.assertTrue(0.2 in self.fs)
        self.assertFalse(0.9 in self.fs)
        self.assertFalse(0 in self.fs)


class TestFuzzySetComparison(unittest.TestCase):
    """Tests for FuzzySet comparison operations."""

    def test_equality(self):
        """Test equality comparison."""
        fs1 = FuzzySet([0.5, 0.3, 0.8])
        fs2 = FuzzySet([0.5, 0.3, 0.8])
        fs3 = FuzzySet([0.5, 0.3, 0.7])

        self.assertEqual(fs1, fs2)
        self.assertNotEqual(fs1, fs3)

    def test_equality_with_floating_point_precision(self):
        """Test equality with floating point precision issues."""
        fs1 = FuzzySet([0.1 + 0.2, 0.5])
        fs2 = FuzzySet([0.3, 0.5])
        # Due to floating point representation, these should be equal
        self.assertEqual(fs1, fs2)

    def test_inequality_different_lengths(self):
        """Test inequality with different length sets."""
        fs1 = FuzzySet([0.5, 0.3])
        fs2 = FuzzySet([0.5, 0.3, 0.8])
        self.assertNotEqual(fs1, fs2)


class TestFuzzySetRepresentation(unittest.TestCase):
    """Tests for FuzzySet string representations."""

    def test_repr(self):
        """Test __repr__ method."""
        fs = FuzzySet([0.5, 0.3, 0.8])
        self.assertEqual(repr(fs), "FuzzySet([0.5, 0.3, 0.8])")

    def test_str_short(self):
        """Test __str__ method with short sets."""
        fs = FuzzySet([0.5, 0.3, 0.8])
        self.assertEqual(str(fs), "FuzzySet([0.5, 0.3, 0.8])")

    def test_str_long(self):
        """Test __str__ method with long sets."""
        fs = FuzzySet([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
        self.assertEqual(str(fs), "FuzzySet([0.1, 0.2, 0.3, 0.4, 0.5, 0.6]...)")


class TestFuzzySetMathematicalProperties(unittest.TestCase):
    """Test mathematical properties of fuzzy set operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.a = FuzzySet([0.8, 0.6, 0.4])
        self.b = FuzzySet([0.7, 0.9, 0.3])
        self.c = FuzzySet([0.5, 0.5, 0.5])
        self.universal = FuzzySet([1.0, 1.0, 1.0])
        self.empty = FuzzySet([0.0, 0.0, 0.0])

    def test_commutativity(self):
        """Test commutative properties."""
        # A ∩ B = B ∩ A
        self.assertEqual(self.a & self.b, self.b & self.a)
        # A ∪ B = B ∪ A
        self.assertEqual(self.a | self.b, self.b | self.a)

    def test_associativity(self):
        """Test associative properties."""
        # (A ∩ B) ∩ C = A ∩ (B ∩ C)
        self.assertEqual((self.a & self.b) & self.c, self.a & (self.b & self.c))
        # (A ∪ B) ∪ C = A ∪ (B ∪ C)
        self.assertEqual((self.a | self.b) | self.c, self.a | (self.b | self.c))

    def test_distributivity(self):
        """Test distributive properties."""
        # A ∩ (B ∪ C) = (A ∩ B) ∪ (A ∩ C)
        left = self.a & (self.b | self.c)
        right = (self.a & self.b) | (self.a & self.c)
        self.assertEqual(left, right)

        # A ∪ (B ∩ C) = (A ∪ B) ∩ (A ∪ C)
        left = self.a | (self.b & self.c)
        right = (self.a | self.b) & (self.a | self.c)
        self.assertEqual(left, right)

    def test_de_morgans_laws(self):
        """Test De Morgan's laws."""
        # ¬(A ∩ B) = ¬A ∪ ¬B
        left = ~(self.a & self.b)
        right = (~self.a) | (~self.b)
        self.assertEqual(left, right)

        # ¬(A ∪ B) = ¬A ∩ ¬B
        left = ~(self.a | self.b)
        right = (~self.a) & (~self.b)
        self.assertEqual(left, right)

    def test_involution(self):
        """Test involution property."""
        # ¬(¬A) = A
        self.assertEqual(~~self.a, self.a)

    def test_idempotence(self):
        """Test idempotent properties."""
        # A ∩ A = A
        self.assertEqual(self.a & self.a, self.a)
        # A ∪ A = A
        self.assertEqual(self.a | self.a, self.a)

    def test_identity_elements(self):
        """Test identity elements."""
        # A ∩ U = A (where U is universal set)
        self.assertEqual(self.a & self.universal, self.a)
        # A ∪ ∅ = A (where ∅ is empty set)
        self.assertEqual(self.a | self.empty, self.a)

    def test_annihilator_elements(self):
        """Test annihilator elements."""
        # A ∩ ∅ = ∅
        self.assertEqual(self.a & self.empty, self.empty)
        # A ∪ U = U
        self.assertEqual(self.a | self.universal, self.universal)

    def test_complement_properties(self):
        """Test complement properties."""
        # A ∩ ¬A results in minimum values (not necessarily 0 in fuzzy logic)
        intersection = self.a & (~self.a)
        # In fuzzy logic, A ∩ ¬A ≠ ∅ necessarily
        # but each element should be min(a, 1-a)
        expected = FuzzySet([min(0.8, 0.2), min(0.6, 0.4), min(0.4, 0.6)])
        self.assertEqual(intersection, expected)

        # A ∪ ¬A results in maximum values (not necessarily 1 in fuzzy logic)
        union = self.a | (~self.a)
        # In fuzzy logic, A ∪ ¬A ≠ U necessarily
        # but each element should be max(a, 1-a)
        expected = FuzzySet([max(0.8, 0.2), max(0.6, 0.4), max(0.4, 0.6)])
        self.assertEqual(union, expected)


class TestFuzzySetEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def test_single_element_operations(self):
        """Test operations on single-element sets."""
        fs1 = FuzzySet([0.7])
        fs2 = FuzzySet([0.4])

        self.assertEqual(fs1 & fs2, FuzzySet([0.4]))
        self.assertEqual(fs1 | fs2, FuzzySet([0.7]))
        self.assertEqual(~fs1, FuzzySet([0.3]))

    def test_extreme_values(self):
        """Test sets with extreme membership values."""
        all_zero = FuzzySet([0.0, 0.0, 0.0])
        all_one = FuzzySet([1.0, 1.0, 1.0])
        mixed = FuzzySet([0.0, 0.5, 1.0])

        # Operations with all zeros
        self.assertEqual(all_zero & mixed, all_zero)
        self.assertEqual(all_zero | mixed, mixed)
        self.assertEqual(~all_zero, all_one)

        # Operations with all ones
        self.assertEqual(all_one & mixed, mixed)
        self.assertEqual(all_one | mixed, all_one)
        self.assertEqual(~all_one, all_zero)

    def test_precision_boundaries(self):
        """Test membership values at precision boundaries."""
        fs = FuzzySet([0.0, 1.0, 0.999999, 0.000001])
        # Should not raise any errors
        self.assertEqual(len(fs), 4)

    def test_large_fuzzy_sets(self):
        """Test operations on large fuzzy sets."""
        import random
        random.seed(42)

        # Create large fuzzy sets
        size = 1000
        values1 = [random.random() for _ in range(size)]
        values2 = [random.random() for _ in range(size)]

        fs1 = FuzzySet(values1)
        fs2 = FuzzySet(values2)

        # Test that operations complete without errors
        result = fs1 & fs2
        self.assertEqual(len(result), size)

        result = fs1 | fs2
        self.assertEqual(len(result), size)

        result = ~fs1
        self.assertEqual(len(result), size)


if __name__ == '__main__':
    unittest.main()