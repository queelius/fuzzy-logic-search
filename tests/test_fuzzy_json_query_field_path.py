import unittest
import sys
import os
# Add parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fuzzy_logic_search.fuzzy_json_query import get_values_by_field_path


class TestFuzzyJsonQuery(unittest.TestCase):

    def test_get_values_by_field_path_flat(self):
        json_data = {"a": 1, "b": 2, "c": 3}
        field_path = "a"
        expected = [1]
        result = get_values_by_field_path(json_data, field_path)
        self.assertCountEqual(result, expected)

    def test_get_values_by_field_path_nested(self):
        json_data = {"a": {"b": {"c": 3}}, "d": 4}
        field_path = "a.b.c"
        expected = [3]
        result = get_values_by_field_path(json_data, field_path)
        self.assertCountEqual(result, expected)

    def test_get_values_by_field_path_incorrect(self):
        json_data = {"a": 1, "b": 2}
        field_path = "a.b"
        expected = []
        result = get_values_by_field_path(json_data, field_path)
        self.assertCountEqual(result, expected)

    def test_get_values_by_field_path_with_list(self):
        json_data = {"a": [{"b": 1}, {"b": 2}], "c": 3}
        field_path = "a.b"
        expected = [1, 2]
        result = get_values_by_field_path(json_data, field_path)
        self.assertCountEqual(result, expected)

    def test_get_values_by_field_path_single_wildcard(self):
        json_data = {
            "a": {
                "x": {"c": 1},
                "y": {"c": 2},
                "z": {"d": 3}
            },
            "b": {"c": 4}
        }
        field_path = "a.*.c"
        expected = [1, 2]
        result = get_values_by_field_path(json_data, field_path)
        self.assertCountEqual(result, expected)

    def test_get_values_by_field_path_double_wildcard(self):
        json_data = {
            "a": {
                "b": {
                    "c": 1,
                    "d": {
                        "c": 2
                    }
                },
                "e": {
                    "f": {
                        "c": 3
                    }
                }
            },
            "c": 4
        }
        field_path = "**.c"
        expected = [1, 2, 3]
        result = get_values_by_field_path(json_data, field_path)
        self.assertCountEqual(result, expected)

    def test_get_values_by_field_path_wildcard_and_field(self):
        json_data = {
            "a": {
                "x": {"c": 1},
                "y": {"c": 2},
                "z": {"d": 3}
            },
            "b": {
                "x": {"c": 4},
                "y": {"c": 5}
            }
        }
        field_path = "*.x.c"
        expected = [1, 4]
        result = get_values_by_field_path(json_data, field_path)
        self.assertCountEqual(result, expected)

    # Additional Tests for '*' and '**' Wildcards

    def test_get_values_by_field_path_multiple_single_wildcards(self):
        """
        Tests field paths with multiple single-level wildcards '*'.
        Example field path: "a.*.*.c"
        """
        json_data = {
            "a": {
                "x": {
                    "y": {"c": 1},
                    "z": {"c": 2}
                },
                "m": {
                    "n": {"c": 3},
                    "o": {"d": 4}
                }
            },
            "c": 5
        }
        field_path = "a.*.*.c"
        expected = [1, 2, 3]
        result = get_values_by_field_path(json_data, field_path)
        self.assertCountEqual(result, expected)

    def test_get_values_by_field_path_wildcard_at_end(self):
        """
        Tests field paths that end with a single wildcard '*'.
        Example field path: "a.b.*"
        """
        json_data = {
            "a": {
                "b": {
                    "c": 1,
                    "d": 2,
                    "e": 3
                },
                "f": 4
            }
        }
        field_path = "a.b.*"
        expected = [1, 2, 3]
        result = get_values_by_field_path(json_data, field_path)
        self.assertCountEqual(result, expected)

    def test_get_values_by_field_path_double_wildcard_middle(self):
        """
        Tests field paths with '**' in the middle.
        Example field path: "a.**.c"
        """
        json_data = {
            "a": {
                "b": {
                    "c": 1,
                    "d": {
                        "c": 2
                    }
                },
                "e": {
                    "f": {
                        "c": 3
                    }
                }
            },
            "c": 4,
            "g": {
                "h": {
                    "c": 5
                }
            }
        }
        field_path = "a.**.c"
        expected = [1, 2, 3]
        result = get_values_by_field_path(json_data, field_path)
        self.assertCountEqual(result, expected)

    def test_get_values_by_field_path_double_wildcard_multiple_fields(self):
        """
        Tests field paths that include '**' and additional fields.
        Example field path: "**.b.c"
        """
        json_data = {
            "a": {
                "b": {
                    "c": 1
                },
                "x": {
                    "b": {
                        "c": 2
                    }
                }
            },
            "b": {
                "c": 3
            },
            "d": 4
        }
        field_path = "**.b.c"
        expected = [1, 2, 3]
        result = get_values_by_field_path(json_data, field_path)
        self.assertCountEqual(result, expected)

    def test_get_values_by_field_path_wildcard_with_list(self):
        """
        Tests field paths with '*' when the JSON contains lists.
        Example field path: "a.*.b"
        """
        json_data = {
            "a": [
                {"b": 1},
                {"b": 2},
                {"c": 3}
            ],
            "b": 4
        }
        field_path = "a.*.b"
        expected = [1, 2]
        result = get_values_by_field_path(json_data, field_path)
        self.assertCountEqual(result, expected)

    def test_get_values_by_field_path_double_wildcard_with_list(self):
        """
        Tests field paths with '**' when the JSON contains deeply nested lists.
        Example field path: "**.c"
        """
        json_data = {
            "a": [
                {"b": {"c": 1}},
                {"b": {"d": [{"c": 2}, {"c": 3}]}},
                {"e": {"f": {"c": 4}}}
            ],
            "c": 5
        }
        field_path = "**.c"
        expected = [1, 2, 3, 4, 5]
        result = get_values_by_field_path(json_data, field_path)
        self.assertCountEqual(result, expected)


if __name__ == '__main__':
    unittest.main()