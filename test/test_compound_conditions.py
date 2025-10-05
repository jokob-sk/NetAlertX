"""
Unit tests for SafeConditionBuilder compound condition parsing.

Tests the fix for Issue #1210 - compound conditions with multiple AND/OR clauses.
"""

import sys
import unittest
from unittest.mock import MagicMock

# Mock the logger module before importing SafeConditionBuilder
sys.modules['logger'] = MagicMock()

# Add parent directory to path for imports
sys.path.insert(0, '/tmp/netalertx_hotfix/server/db')

from sql_safe_builder import SafeConditionBuilder


class TestCompoundConditions(unittest.TestCase):
    """Test compound condition parsing functionality."""

    def setUp(self):
        """Create a fresh builder instance for each test."""
        self.builder = SafeConditionBuilder()

    def test_user_failing_filter_six_and_clauses(self):
        """Test the exact user-reported failing filter from Issue #1210."""
        condition = (
            "AND devLastIP NOT LIKE '192.168.50.%' "
            "AND devLastIP NOT LIKE '192.168.60.%' "
            "AND devLastIP NOT LIKE '192.168.70.2' "
            "AND devLastIP NOT LIKE '192.168.70.5' "
            "AND devLastIP NOT LIKE '192.168.70.3' "
            "AND devLastIP NOT LIKE '192.168.70.4'"
        )

        sql, params = self.builder.build_safe_condition(condition)

        # Should successfully parse
        self.assertIsNotNone(sql)
        self.assertIsNotNone(params)

        # Should have 6 parameters (one per clause)
        self.assertEqual(len(params), 6)

        # Should contain all 6 AND operators
        self.assertEqual(sql.count('AND'), 6)

        # Should contain all 6 NOT LIKE operators
        self.assertEqual(sql.count('NOT LIKE'), 6)

        # Should have 6 parameter placeholders
        self.assertEqual(sql.count(':param_'), 6)

        # Verify all IP patterns are in parameters
        param_values = list(params.values())
        self.assertIn('192.168.50.%', param_values)
        self.assertIn('192.168.60.%', param_values)
        self.assertIn('192.168.70.2', param_values)
        self.assertIn('192.168.70.5', param_values)
        self.assertIn('192.168.70.3', param_values)
        self.assertIn('192.168.70.4', param_values)

    def test_multiple_and_clauses_simple(self):
        """Test multiple AND clauses with simple equality operators."""
        condition = "AND devName = 'Device1' AND devVendor = 'Apple' AND devFavorite = '1'"

        sql, params = self.builder.build_safe_condition(condition)

        # Should have 3 parameters
        self.assertEqual(len(params), 3)

        # Should have 3 AND operators
        self.assertEqual(sql.count('AND'), 3)

        # Verify all values are parameterized
        param_values = list(params.values())
        self.assertIn('Device1', param_values)
        self.assertIn('Apple', param_values)
        self.assertIn('1', param_values)

    def test_multiple_or_clauses(self):
        """Test multiple OR clauses."""
        condition = "OR devName = 'Device1' OR devName = 'Device2' OR devName = 'Device3'"

        sql, params = self.builder.build_safe_condition(condition)

        # Should have 3 parameters
        self.assertEqual(len(params), 3)

        # Should have 3 OR operators
        self.assertEqual(sql.count('OR'), 3)

        # Verify all device names are parameterized
        param_values = list(params.values())
        self.assertIn('Device1', param_values)
        self.assertIn('Device2', param_values)
        self.assertIn('Device3', param_values)

    def test_mixed_and_or_clauses(self):
        """Test mixed AND/OR logical operators."""
        condition = "AND devName = 'Device1' OR devName = 'Device2' AND devFavorite = '1'"

        sql, params = self.builder.build_safe_condition(condition)

        # Should have 3 parameters
        self.assertEqual(len(params), 3)

        # Should preserve the logical operator order
        self.assertIn('AND', sql)
        self.assertIn('OR', sql)

        # Verify all values are parameterized
        param_values = list(params.values())
        self.assertIn('Device1', param_values)
        self.assertIn('Device2', param_values)
        self.assertIn('1', param_values)

    def test_single_condition_backward_compatibility(self):
        """Test that single conditions still work (backward compatibility)."""
        condition = "AND devName = 'TestDevice'"

        sql, params = self.builder.build_safe_condition(condition)

        # Should have 1 parameter
        self.assertEqual(len(params), 1)

        # Should match expected format
        self.assertIn('AND devName = :param_', sql)

        # Parameter should contain the value
        self.assertIn('TestDevice', params.values())

    def test_single_condition_like_operator(self):
        """Test single LIKE condition for backward compatibility."""
        condition = "AND devComments LIKE '%important%'"

        sql, params = self.builder.build_safe_condition(condition)

        # Should have 1 parameter
        self.assertEqual(len(params), 1)

        # Should contain LIKE operator
        self.assertIn('LIKE', sql)

        # Parameter should contain the pattern
        self.assertIn('%important%', params.values())

    def test_compound_with_like_patterns(self):
        """Test compound conditions with LIKE patterns."""
        condition = "AND devLastIP LIKE '192.168.%' AND devVendor LIKE '%Apple%'"

        sql, params = self.builder.build_safe_condition(condition)

        # Should have 2 parameters
        self.assertEqual(len(params), 2)

        # Should have 2 LIKE operators
        self.assertEqual(sql.count('LIKE'), 2)

        # Verify patterns are parameterized
        param_values = list(params.values())
        self.assertIn('192.168.%', param_values)
        self.assertIn('%Apple%', param_values)

    def test_compound_with_inequality_operators(self):
        """Test compound conditions with various inequality operators."""
        condition = "AND eve_DateTime > '2024-01-01' AND eve_DateTime < '2024-12-31'"

        sql, params = self.builder.build_safe_condition(condition)

        # Should have 2 parameters
        self.assertEqual(len(params), 2)

        # Should have both operators
        self.assertIn('>', sql)
        self.assertIn('<', sql)

        # Verify dates are parameterized
        param_values = list(params.values())
        self.assertIn('2024-01-01', param_values)
        self.assertIn('2024-12-31', param_values)

    def test_empty_condition(self):
        """Test empty condition string."""
        condition = ""

        sql, params = self.builder.build_safe_condition(condition)

        # Should return empty results
        self.assertEqual(sql, "")
        self.assertEqual(params, {})

    def test_whitespace_only_condition(self):
        """Test condition with only whitespace."""
        condition = "   \t\n  "

        sql, params = self.builder.build_safe_condition(condition)

        # Should return empty results
        self.assertEqual(sql, "")
        self.assertEqual(params, {})

    def test_invalid_column_name_rejected(self):
        """Test that invalid column names are rejected."""
        condition = "AND malicious_column = 'value'"

        with self.assertRaises(ValueError):
            self.builder.build_safe_condition(condition)

    def test_invalid_operator_rejected(self):
        """Test that invalid operators are rejected."""
        condition = "AND devName EXECUTE 'DROP TABLE'"

        with self.assertRaises(ValueError):
            self.builder.build_safe_condition(condition)

    def test_sql_injection_attempt_blocked(self):
        """Test that SQL injection attempts are blocked."""
        condition = "AND devName = 'value'; DROP TABLE devices; --"

        # Should either reject or sanitize the dangerous input
        # The semicolon and comment should not appear in the final SQL
        try:
            sql, params = self.builder.build_safe_condition(condition)
            # If it doesn't raise an error, it should sanitize the input
            self.assertNotIn('DROP', sql.upper())
            self.assertNotIn(';', sql)
        except ValueError:
            # Rejection is also acceptable
            pass

    def test_quoted_string_with_spaces(self):
        """Test that quoted strings with spaces are handled correctly."""
        condition = "AND devName = 'My Device Name' AND devComments = 'Has spaces here'"

        sql, params = self.builder.build_safe_condition(condition)

        # Should have 2 parameters
        self.assertEqual(len(params), 2)

        # Verify values with spaces are preserved
        param_values = list(params.values())
        self.assertIn('My Device Name', param_values)
        self.assertIn('Has spaces here', param_values)

    def test_compound_condition_with_not_equal(self):
        """Test compound conditions with != operator."""
        condition = "AND devName != 'Device1' AND devVendor != 'Unknown'"

        sql, params = self.builder.build_safe_condition(condition)

        # Should have 2 parameters
        self.assertEqual(len(params), 2)

        # Should have != operators (or converted to <>)
        self.assertTrue('!=' in sql or '<>' in sql)

        # Verify values are parameterized
        param_values = list(params.values())
        self.assertIn('Device1', param_values)
        self.assertIn('Unknown', param_values)

    def test_very_long_compound_condition(self):
        """Test handling of very long compound conditions (10+ clauses)."""
        clauses = []
        for i in range(10):
            clauses.append(f"AND devName != 'Device{i}'")

        condition = " ".join(clauses)
        sql, params = self.builder.build_safe_condition(condition)

        # Should have 10 parameters
        self.assertEqual(len(params), 10)

        # Should have 10 AND operators
        self.assertEqual(sql.count('AND'), 10)

        # Verify all device names are parameterized
        param_values = list(params.values())
        for i in range(10):
            self.assertIn(f'Device{i}', param_values)


class TestParameterGeneration(unittest.TestCase):
    """Test parameter generation and naming."""

    def setUp(self):
        """Create a fresh builder instance for each test."""
        self.builder = SafeConditionBuilder()

    def test_parameters_have_unique_names(self):
        """Test that all parameters get unique names."""
        condition = "AND devName = 'A' AND devName = 'B' AND devName = 'C'"

        sql, params = self.builder.build_safe_condition(condition)

        # All parameter names should be unique
        param_names = list(params.keys())
        self.assertEqual(len(param_names), len(set(param_names)))

    def test_parameter_values_match_condition(self):
        """Test that parameter values correctly match the condition values."""
        condition = "AND devLastIP NOT LIKE '192.168.1.%' AND devLastIP NOT LIKE '10.0.0.%'"

        sql, params = self.builder.build_safe_condition(condition)

        # Should have exactly the values from the condition
        param_values = sorted(params.values())
        expected_values = sorted(['192.168.1.%', '10.0.0.%'])
        self.assertEqual(param_values, expected_values)

    def test_parameters_referenced_in_sql(self):
        """Test that all parameters are actually referenced in the SQL."""
        condition = "AND devName = 'Device1' AND devVendor = 'Apple'"

        sql, params = self.builder.build_safe_condition(condition)

        # Every parameter should appear in the SQL
        for param_name in params.keys():
            self.assertIn(f':{param_name}', sql)


if __name__ == '__main__':
    unittest.main()
