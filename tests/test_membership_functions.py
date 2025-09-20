"""
Comprehensive test suite for fuzzy membership functions.
Tests all membership function types and their properties.
"""

import unittest
import numpy as np
from fuzzy_logic_search.membership_functions import (
    triangular_membership,
    trapezoidal_membership,
    gaussian_membership,
    sigmoid_membership,
    bell_membership,
    fuzzy_equal,
    fuzzy_greater_than,
    fuzzy_less_than,
    fuzzy_between,
    fuzzy_close_to,
    fuzzy_approximately,
    very,
    somewhat,
    slightly,
    extremely,
    create_membership_function
)


class TestTriangularMembership(unittest.TestCase):
    """Tests for triangular membership function."""

    def test_triangular_basic(self):
        """Test basic triangular membership function."""
        # Triangle with peak at 5, feet at 3 and 7
        self.assertEqual(triangular_membership(3, 3, 5, 7), 0.0)  # Left foot
        self.assertEqual(triangular_membership(5, 3, 5, 7), 1.0)  # Peak
        self.assertEqual(triangular_membership(7, 3, 5, 7), 0.0)  # Right foot
        self.assertAlmostEqual(triangular_membership(4, 3, 5, 7), 0.5)  # Midpoint left
        self.assertAlmostEqual(triangular_membership(6, 3, 5, 7), 0.5)  # Midpoint right

    def test_triangular_outside_range(self):
        """Test triangular membership outside the support range."""
        self.assertEqual(triangular_membership(0, 3, 5, 7), 0.0)
        self.assertEqual(triangular_membership(10, 3, 5, 7), 0.0)

    def test_triangular_degenerate_cases(self):
        """Test edge cases with zero-width segments."""
        # Spike at a single point
        self.assertEqual(triangular_membership(5, 5, 5, 5), 1.0)  # At the spike
        self.assertEqual(triangular_membership(4, 5, 5, 5), 0.0)  # Not at spike
        # Vertical rise
        self.assertEqual(triangular_membership(5, 5, 5, 7), 1.0)  # At peak
        self.assertAlmostEqual(triangular_membership(6, 5, 5, 7), 0.5)  # Midway down
        # Vertical fall
        self.assertEqual(triangular_membership(5, 3, 5, 5), 1.0)  # At peak
        self.assertAlmostEqual(triangular_membership(4, 3, 5, 5), 0.5)  # Midway up


class TestTrapezoidalMembership(unittest.TestCase):
    """Tests for trapezoidal membership function."""

    def test_trapezoidal_basic(self):
        """Test basic trapezoidal membership function."""
        # Trapezoid with plateau from 5 to 7
        self.assertEqual(trapezoidal_membership(3, 3, 5, 7, 9), 0.0)  # Left foot
        self.assertEqual(trapezoidal_membership(5, 3, 5, 7, 9), 1.0)  # Left shoulder
        self.assertEqual(trapezoidal_membership(6, 3, 5, 7, 9), 1.0)  # Plateau
        self.assertEqual(trapezoidal_membership(7, 3, 5, 7, 9), 1.0)  # Right shoulder
        self.assertEqual(trapezoidal_membership(9, 3, 5, 7, 9), 0.0)  # Right foot
        self.assertAlmostEqual(trapezoidal_membership(4, 3, 5, 7, 9), 0.5)  # Rising
        self.assertAlmostEqual(trapezoidal_membership(8, 3, 5, 7, 9), 0.5)  # Falling

    def test_trapezoidal_triangular_special_case(self):
        """Test that trapezoidal degenerates to triangular when b == c."""
        # Should behave like triangular
        self.assertEqual(trapezoidal_membership(5, 3, 5, 5, 7), 1.0)
        self.assertAlmostEqual(trapezoidal_membership(4, 3, 5, 5, 7), 0.5)
        self.assertAlmostEqual(trapezoidal_membership(6, 3, 5, 5, 7), 0.5)

    def test_trapezoidal_rectangular_special_case(self):
        """Test rectangular membership (vertical edges)."""
        # Rectangle from 3 to 7
        self.assertEqual(trapezoidal_membership(2, 3, 3, 7, 7), 0.0)
        self.assertEqual(trapezoidal_membership(3, 3, 3, 7, 7), 1.0)
        self.assertEqual(trapezoidal_membership(5, 3, 3, 7, 7), 1.0)
        self.assertEqual(trapezoidal_membership(7, 3, 3, 7, 7), 1.0)
        self.assertEqual(trapezoidal_membership(8, 3, 3, 7, 7), 0.0)


class TestGaussianMembership(unittest.TestCase):
    """Tests for Gaussian membership function."""

    def test_gaussian_basic(self):
        """Test basic Gaussian membership function."""
        # Gaussian centered at 5 with sigma=2
        self.assertEqual(gaussian_membership(5, 5, 2), 1.0)  # Peak at mean
        self.assertLess(gaussian_membership(3, 5, 2), 1.0)  # Left of mean
        self.assertLess(gaussian_membership(7, 5, 2), 1.0)  # Right of mean
        self.assertGreater(gaussian_membership(5, 5, 2), 0.0)  # Always positive

    def test_gaussian_symmetry(self):
        """Test that Gaussian is symmetric around the mean."""
        mean, sigma = 10, 3
        # Points equidistant from mean should have same membership
        self.assertAlmostEqual(
            gaussian_membership(mean - 2, mean, sigma),
            gaussian_membership(mean + 2, mean, sigma)
        )

    def test_gaussian_zero_sigma(self):
        """Test Gaussian with zero standard deviation (impulse)."""
        self.assertEqual(gaussian_membership(5, 5, 0), 1.0)
        self.assertEqual(gaussian_membership(4.999, 5, 0), 0.0)
        self.assertEqual(gaussian_membership(5.001, 5, 0), 0.0)

    def test_gaussian_width_effect(self):
        """Test that wider Gaussian has slower decay."""
        x, mean = 7, 5
        narrow = gaussian_membership(x, mean, 1)
        wide = gaussian_membership(x, mean, 3)
        self.assertGreater(wide, narrow)  # Wider Gaussian decays slower


class TestSigmoidMembership(unittest.TestCase):
    """Tests for sigmoid membership function."""

    def test_sigmoid_basic(self):
        """Test basic sigmoid membership function."""
        # Sigmoid centered at 5 with positive slope
        self.assertAlmostEqual(sigmoid_membership(5, 1, 5), 0.5)  # Crossover point
        self.assertLess(sigmoid_membership(3, 1, 5), 0.5)  # Before crossover
        self.assertGreater(sigmoid_membership(7, 1, 5), 0.5)  # After crossover

    def test_sigmoid_negative_slope(self):
        """Test sigmoid with negative slope (decreasing)."""
        self.assertAlmostEqual(sigmoid_membership(5, -1, 5), 0.5)  # Crossover
        self.assertGreater(sigmoid_membership(3, -1, 5), 0.5)  # Before (higher)
        self.assertLess(sigmoid_membership(7, -1, 5), 0.5)  # After (lower)

    def test_sigmoid_slope_effect(self):
        """Test that steeper slope gives sharper transition."""
        x, c = 5.5, 5
        gentle = sigmoid_membership(x, 1, c)
        steep = sigmoid_membership(x, 10, c)
        self.assertGreater(steep, gentle)  # Steeper slope reaches higher faster


class TestBellMembership(unittest.TestCase):
    """Tests for bell-shaped membership function."""

    def test_bell_basic(self):
        """Test basic bell membership function."""
        # Bell centered at 5 with width 2 and shape 2
        self.assertEqual(bell_membership(5, 2, 2, 5), 1.0)  # Peak at center
        self.assertLess(bell_membership(3, 2, 2, 5), 1.0)  # Left of center
        self.assertLess(bell_membership(7, 2, 2, 5), 1.0)  # Right of center

    def test_bell_symmetry(self):
        """Test that bell is symmetric around center."""
        a, b, c = 3, 2, 10
        # Points equidistant from center should have same membership
        self.assertAlmostEqual(
            bell_membership(c - 2, a, b, c),
            bell_membership(c + 2, a, b, c)
        )

    def test_bell_shape_parameter(self):
        """Test effect of shape parameter b."""
        # Test at the center and away from center
        a, c = 3, 5

        # At center, all should be 1
        self.assertEqual(bell_membership(c, a, 1, c), 1.0)
        self.assertEqual(bell_membership(c, a, 3, c), 1.0)

        # Test at a point where |x-c|/a != 1
        x = 6  # 1 unit from center, a=3 so |x-c|/a = 1/3
        low_b = bell_membership(x, a, 1, c)  # b=1
        high_b = bell_membership(x, a, 2, c)  # b=2
        # With |x-c|/a = 1/3 < 1:
        # For b=1: 1/(1 + (1/3)^2) = 1/(1 + 1/9) = 9/10
        # For b=2: 1/(1 + (1/3)^4) = 1/(1 + 1/81) = 81/82
        # So high_b > low_b (sharper peak with higher b)
        self.assertGreater(high_b, low_b)

    def test_bell_zero_width(self):
        """Test bell with zero width (impulse)."""
        self.assertEqual(bell_membership(5, 0, 2, 5), 1.0)
        self.assertEqual(bell_membership(4.999, 0, 2, 5), 0.0)
        self.assertEqual(bell_membership(5.001, 0, 2, 5), 0.0)


class TestFuzzyComparisons(unittest.TestCase):
    """Tests for fuzzy comparison functions."""

    def test_fuzzy_equal(self):
        """Test fuzzy equality."""
        self.assertEqual(fuzzy_equal(5, 5, 1), 1.0)  # Exact match
        self.assertGreater(fuzzy_equal(5.5, 5, 1), 0)  # Close match
        self.assertEqual(fuzzy_equal(7, 5, 1), 0.0)  # Outside tolerance

    def test_fuzzy_greater_than(self):
        """Test fuzzy greater-than."""
        self.assertAlmostEqual(fuzzy_greater_than(5, 5, 1), 0.5, places=2)  # At threshold
        self.assertGreater(fuzzy_greater_than(7, 5, 1), 0.9)  # Well above
        self.assertLess(fuzzy_greater_than(3, 5, 1), 0.1)  # Well below

    def test_fuzzy_less_than(self):
        """Test fuzzy less-than."""
        self.assertAlmostEqual(fuzzy_less_than(5, 5, 1), 0.5, places=2)  # At threshold
        self.assertLess(fuzzy_less_than(7, 5, 1), 0.1)  # Well above
        self.assertGreater(fuzzy_less_than(3, 5, 1), 0.9)  # Well below

    def test_fuzzy_between(self):
        """Test fuzzy between."""
        self.assertEqual(fuzzy_between(5, 3, 7, 1), 1.0)  # In range
        self.assertEqual(fuzzy_between(3, 3, 7, 0.1), 1.0)  # At lower boundary
        self.assertEqual(fuzzy_between(7, 3, 7, 0.1), 1.0)  # At upper boundary
        self.assertAlmostEqual(fuzzy_between(1, 3, 7, 1), 0.0, places=2)  # Outside

    def test_fuzzy_close_to(self):
        """Test fuzzy closeness (Gaussian)."""
        self.assertEqual(fuzzy_close_to(5, 5, 1), 1.0)  # Exact match
        self.assertGreater(fuzzy_close_to(5.5, 5, 1), 0.5)  # Close
        self.assertLess(fuzzy_close_to(8, 5, 1), 0.1)  # Far

    def test_fuzzy_approximately(self):
        """Test fuzzy approximation (bell-shaped)."""
        self.assertEqual(fuzzy_approximately(5, 5, 1), 1.0)  # Exact
        self.assertGreater(fuzzy_approximately(5.5, 5, 2), 0.5)  # Close
        self.assertLess(fuzzy_approximately(10, 5, 1), 0.1)  # Far


class TestLinguisticHedges(unittest.TestCase):
    """Tests for linguistic hedges."""

    def test_very(self):
        """Test 'very' hedge (intensification)."""
        self.assertEqual(very(1.0), 1.0)
        self.assertEqual(very(0.0), 0.0)
        self.assertEqual(very(0.5), 0.25)
        self.assertAlmostEqual(very(0.7), 0.49)

    def test_somewhat(self):
        """Test 'somewhat' hedge (dilution)."""
        self.assertEqual(somewhat(1.0), 1.0)
        self.assertEqual(somewhat(0.0), 0.0)
        self.assertAlmostEqual(somewhat(0.25), 0.5)
        self.assertAlmostEqual(somewhat(0.49), 0.7)

    def test_slightly(self):
        """Test 'slightly' hedge (strong dilution)."""
        self.assertEqual(slightly(1.0), 1.0)
        self.assertEqual(slightly(0.0), 0.0)
        self.assertGreater(slightly(0.5), 0.9)  # Strong dilution

    def test_extremely(self):
        """Test 'extremely' hedge (strong intensification)."""
        self.assertEqual(extremely(1.0), 1.0)
        self.assertEqual(extremely(0.0), 0.0)
        self.assertEqual(extremely(0.5), 0.125)
        self.assertAlmostEqual(extremely(0.8), 0.512)

    def test_hedge_composition(self):
        """Test composition of hedges."""
        # Test with different value where difference is more pronounced
        x = 0.4
        vs = very(somewhat(x))  # sqrt(0.4)^2 = 0.4
        sv = somewhat(very(x))  # sqrt(0.4^2) = sqrt(0.16) = 0.4
        # Actually for this case they are equal, let's test a different property
        # very(very(x)) should be different from somewhat(somewhat(x))
        vv = very(very(x))  # 0.4^4 = 0.0256
        ss = somewhat(somewhat(x))  # 0.4^0.25 ≈ 0.795
        self.assertNotAlmostEqual(vv, ss, places=2)

    def test_hedge_properties(self):
        """Test mathematical properties of hedges."""
        x = 0.7
        # very reduces membership for values < 1
        self.assertLess(very(x), x)
        # somewhat increases membership for values < 1
        self.assertGreater(somewhat(x), x)
        # extremely reduces more than very
        self.assertLess(extremely(x), very(x))
        # slightly increases more than somewhat
        self.assertGreater(slightly(x), somewhat(x))


class TestMembershipFactory(unittest.TestCase):
    """Tests for membership function factory."""

    def test_create_triangular(self):
        """Test creating triangular membership function."""
        tri = create_membership_function('triangular', a=3, b=5, c=7)
        self.assertEqual(tri(5), 1.0)
        self.assertEqual(tri(3), 0.0)
        self.assertEqual(tri(7), 0.0)

    def test_create_trapezoidal(self):
        """Test creating trapezoidal membership function."""
        trap = create_membership_function('trapezoidal', a=2, b=4, c=6, d=8)
        self.assertEqual(trap(5), 1.0)
        self.assertEqual(trap(2), 0.0)
        self.assertEqual(trap(8), 0.0)

    def test_create_gaussian(self):
        """Test creating Gaussian membership function."""
        gauss = create_membership_function('gaussian', mean=10, sigma=2)
        self.assertEqual(gauss(10), 1.0)
        self.assertLess(gauss(8), 1.0)
        self.assertGreater(gauss(10), gauss(8))

    def test_create_sigmoid(self):
        """Test creating sigmoid membership function."""
        sig = create_membership_function('sigmoid', a=1, c=5)
        self.assertAlmostEqual(sig(5), 0.5)
        self.assertLess(sig(3), 0.5)
        self.assertGreater(sig(7), 0.5)

    def test_create_bell(self):
        """Test creating bell membership function."""
        bell = create_membership_function('bell', a=2, b=2, c=5)
        self.assertEqual(bell(5), 1.0)
        self.assertLess(bell(3), 1.0)
        self.assertLess(bell(7), 1.0)

    def test_invalid_function_type(self):
        """Test that invalid function type raises error."""
        with self.assertRaises(ValueError):
            create_membership_function('invalid_type', a=1, b=2)


class TestMembershipFunctionIntegration(unittest.TestCase):
    """Integration tests for membership functions."""

    def test_age_categories(self):
        """Test modeling age categories with membership functions."""
        # Create age category membership functions
        young = create_membership_function('trapezoidal', a=0, b=0, c=25, d=35)
        middle_aged = create_membership_function('gaussian', mean=45, sigma=10)
        old = create_membership_function('sigmoid', a=0.1, c=65)

        # Test a 20-year-old
        age = 20
        self.assertGreater(young(age), 0.8)  # Strongly young
        self.assertLess(middle_aged(age), 0.2)  # Not middle-aged
        self.assertLess(old(age), 0.1)  # Not old

        # Test a 45-year-old
        age = 45
        self.assertLess(young(age), 0.1)  # Not young
        self.assertEqual(middle_aged(age), 1.0)  # Peak middle-aged
        self.assertLess(old(age), 0.2)  # Not really old yet

        # Test a 70-year-old
        age = 70
        self.assertEqual(young(age), 0.0)  # Not young
        self.assertLess(middle_aged(age), 0.2)  # Not middle-aged
        self.assertGreater(old(age), 0.6)  # Clearly old (adjusted threshold)

    def test_temperature_control(self):
        """Test temperature control with fuzzy membership."""
        # Temperature categories
        cold = lambda t: fuzzy_less_than(t, 18, 2)
        comfortable = lambda t: fuzzy_between(t, 18, 24, 2)
        hot = lambda t: fuzzy_greater_than(t, 24, 2)

        # Test various temperatures
        self.assertGreater(cold(10), 0.9)  # Very cold
        self.assertLess(comfortable(10), 0.1)
        self.assertLess(hot(10), 0.1)

        self.assertLess(cold(21), 0.1)  # Comfortable
        self.assertGreater(comfortable(21), 0.9)
        self.assertLess(hot(21), 0.1)

        self.assertLess(cold(30), 0.1)  # Very hot
        self.assertLess(comfortable(30), 0.1)
        self.assertGreater(hot(30), 0.9)


if __name__ == '__main__':
    unittest.main()