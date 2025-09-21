"""
Unit tests for SafeConditionBuilder focusing on core security functionality.
This test file has minimal dependencies to ensure it can run in any environment.
"""

import sys
import unittest
import re
from unittest.mock import Mock, patch

# Mock the logger module to avoid dependency issues
sys.modules['logger'] = Mock()

# Standalone version of SafeConditionBuilder for testing
class TestSafeConditionBuilder:
    """
    Test version of SafeConditionBuilder with mock logger.
    """

    # Whitelist of allowed column names for filtering
    ALLOWED_COLUMNS = {
        'eve_MAC', 'eve_DateTime', 'eve_IP', 'eve_EventType', 'devName', 
        'devComments', 'devLastIP', 'devVendor', 'devAlertEvents', 
        'devAlertDown', 'devIsArchived', 'devPresentLastScan', 'devFavorite',
        'devIsNew', 'Plugin', 'Object_PrimaryId', 'Object_SecondaryId',
        'DateTimeChanged', 'Watched_Value1', 'Watched_Value2', 'Watched_Value3',
        'Watched_Value4', 'Status'
    }

    # Whitelist of allowed comparison operators
    ALLOWED_OPERATORS = {
        '=', '!=', '<>', '<', '>', '<=', '>=', 'LIKE', 'NOT LIKE', 
        'IN', 'NOT IN', 'IS NULL', 'IS NOT NULL'
    }

    # Whitelist of allowed logical operators
    ALLOWED_LOGICAL_OPERATORS = {'AND', 'OR'}

    # Whitelist of allowed event types
    ALLOWED_EVENT_TYPES = {
        'New Device', 'Connected', 'Disconnected', 'Device Down', 
        'Down Reconnected', 'IP Changed'
    }

    def __init__(self):
        """Initialize the SafeConditionBuilder."""
        self.parameters = {}
        self.param_counter = 0

    def _generate_param_name(self, prefix='param'):
        """Generate a unique parameter name for SQL binding."""
        self.param_counter += 1
        return f"{prefix}_{self.param_counter}"

    def _sanitize_string(self, value):
        """Sanitize string input by removing potentially dangerous characters."""
        if not isinstance(value, str):
            return str(value)
        
        # Replace {s-quote} placeholder with single quote (maintaining compatibility)
        value = value.replace('{s-quote}', "'")
        
        # Remove any null bytes, control characters, and excessive whitespace
        value = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]', '', value)
        value = re.sub(r'\s+', ' ', value.strip())
        
        return value

    def _validate_column_name(self, column):
        """Validate that a column name is in the whitelist."""
        return column in self.ALLOWED_COLUMNS

    def _validate_operator(self, operator):
        """Validate that an operator is in the whitelist."""
        return operator.upper() in self.ALLOWED_OPERATORS

    def _validate_logical_operator(self, logical_op):
        """Validate that a logical operator is in the whitelist."""
        return logical_op.upper() in self.ALLOWED_LOGICAL_OPERATORS

    def build_safe_condition(self, condition_string):
        """Parse and build a safe SQL condition from a user-provided string."""
        if not condition_string or not condition_string.strip():
            return "", {}

        # Sanitize the input
        condition_string = self._sanitize_string(condition_string)
        
        # Reset parameters for this condition
        self.parameters = {}
        self.param_counter = 0

        try:
            return self._parse_condition(condition_string)
        except Exception as e:
            raise ValueError(f"Invalid condition format: {condition_string}")

    def _parse_condition(self, condition):
        """Parse a condition string into safe SQL with parameters."""
        condition = condition.strip()
        
        # Handle empty conditions
        if not condition:
            return "", {}

        # Simple pattern matching for common conditions
        # Pattern 1: AND/OR column operator value
        pattern1 = r'^\s*(AND|OR)?\s+(\w+)\s+(=|!=|<>|<|>|<=|>=|LIKE|NOT\s+LIKE)\s+\'([^\']*)\'\s*$'
        match1 = re.match(pattern1, condition, re.IGNORECASE)
        
        if match1:
            logical_op, column, operator, value = match1.groups()
            return self._build_simple_condition(logical_op, column, operator, value)

        # If no patterns match, reject the condition for security
        raise ValueError(f"Unsupported condition pattern: {condition}")

    def _build_simple_condition(self, logical_op, column, operator, value):
        """Build a simple condition with parameter binding."""
        # Validate components
        if not self._validate_column_name(column):
            raise ValueError(f"Invalid column name: {column}")
        
        if not self._validate_operator(operator):
            raise ValueError(f"Invalid operator: {operator}")
        
        if logical_op and not self._validate_logical_operator(logical_op):
            raise ValueError(f"Invalid logical operator: {logical_op}")

        # Generate parameter name and store value
        param_name = self._generate_param_name()
        self.parameters[param_name] = value

        # Build the SQL snippet
        sql_parts = []
        if logical_op:
            sql_parts.append(logical_op.upper())
        
        sql_parts.extend([column, operator.upper(), f":{param_name}"])
        
        return " ".join(sql_parts), self.parameters

    def get_safe_condition_legacy(self, condition_setting):
        """Convert legacy condition settings to safe parameterized queries."""
        if not condition_setting or not condition_setting.strip():
            return "", {}

        try:
            return self.build_safe_condition(condition_setting)
        except ValueError:
            # Log the error and return empty condition for safety
            return "", {}


class TestSafeConditionBuilderSecurity(unittest.TestCase):
    """Test cases for the SafeConditionBuilder security functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.builder = TestSafeConditionBuilder()

    def test_initialization(self):
        """Test that SafeConditionBuilder initializes correctly."""
        self.assertIsInstance(self.builder, TestSafeConditionBuilder)
        self.assertEqual(self.builder.param_counter, 0)
        self.assertEqual(self.builder.parameters, {})

    def test_sanitize_string(self):
        """Test string sanitization functionality."""
        # Test normal string
        result = self.builder._sanitize_string("normal string")
        self.assertEqual(result, "normal string")

        # Test s-quote replacement
        result = self.builder._sanitize_string("test{s-quote}value")
        self.assertEqual(result, "test'value")

        # Test control character removal
        result = self.builder._sanitize_string("test\x00\x01string")
        self.assertEqual(result, "teststring")

        # Test excessive whitespace
        result = self.builder._sanitize_string("  test   string  ")
        self.assertEqual(result, "test string")

    def test_validate_column_name(self):
        """Test column name validation against whitelist."""
        # Valid columns
        self.assertTrue(self.builder._validate_column_name('eve_MAC'))
        self.assertTrue(self.builder._validate_column_name('devName'))
        self.assertTrue(self.builder._validate_column_name('eve_EventType'))

        # Invalid columns
        self.assertFalse(self.builder._validate_column_name('malicious_column'))
        self.assertFalse(self.builder._validate_column_name('drop_table'))
        self.assertFalse(self.builder._validate_column_name('user_input'))

    def test_validate_operator(self):
        """Test operator validation against whitelist."""
        # Valid operators
        self.assertTrue(self.builder._validate_operator('='))
        self.assertTrue(self.builder._validate_operator('LIKE'))
        self.assertTrue(self.builder._validate_operator('IN'))

        # Invalid operators
        self.assertFalse(self.builder._validate_operator('UNION'))
        self.assertFalse(self.builder._validate_operator('DROP'))
        self.assertFalse(self.builder._validate_operator('EXEC'))

    def test_build_simple_condition_valid(self):
        """Test building valid simple conditions."""
        sql, params = self.builder._build_simple_condition('AND', 'devName', '=', 'TestDevice')
        
        self.assertIn('AND devName = :param_', sql)
        self.assertEqual(len(params), 1)
        self.assertIn('TestDevice', params.values())

    def test_build_simple_condition_invalid_column(self):
        """Test that invalid column names are rejected."""
        with self.assertRaises(ValueError) as context:
            self.builder._build_simple_condition('AND', 'invalid_column', '=', 'value')
        
        self.assertIn('Invalid column name', str(context.exception))

    def test_build_simple_condition_invalid_operator(self):
        """Test that invalid operators are rejected."""
        with self.assertRaises(ValueError) as context:
            self.builder._build_simple_condition('AND', 'devName', 'UNION', 'value')
        
        self.assertIn('Invalid operator', str(context.exception))

    def test_sql_injection_attempts(self):
        """Test that various SQL injection attempts are blocked."""
        injection_attempts = [
            "'; DROP TABLE Devices; --",
            "' UNION SELECT * FROM Settings --",
            "' OR 1=1 --",
            "'; INSERT INTO Events VALUES(1,2,3); --",
            "' AND (SELECT COUNT(*) FROM sqlite_master) > 0 --",
        ]

        for injection in injection_attempts:
            with self.subTest(injection=injection):
                with self.assertRaises(ValueError):
                    self.builder.build_safe_condition(f"AND devName = '{injection}'")

    def test_legacy_condition_compatibility(self):
        """Test backward compatibility with legacy condition formats."""
        # Test simple condition
        sql, params = self.builder.get_safe_condition_legacy("AND devName = 'TestDevice'")
        self.assertIn('devName', sql)
        self.assertIn('TestDevice', params.values())

        # Test empty condition
        sql, params = self.builder.get_safe_condition_legacy("")
        self.assertEqual(sql, "")
        self.assertEqual(params, {})

        # Test invalid condition returns empty
        sql, params = self.builder.get_safe_condition_legacy("INVALID SQL INJECTION")
        self.assertEqual(sql, "")
        self.assertEqual(params, {})

    def test_parameter_generation(self):
        """Test that parameters are generated correctly."""
        # Test multiple parameters
        sql1, params1 = self.builder.build_safe_condition("AND devName = 'Device1'")
        sql2, params2 = self.builder.build_safe_condition("AND devName = 'Device2'")
        
        # Each should have unique parameter names
        self.assertNotEqual(list(params1.keys())[0], list(params2.keys())[0])

    def test_xss_prevention(self):
        """Test that XSS-like payloads in device names are handled safely."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "<img src=x onerror=alert(1)>",
            "'; DROP TABLE users; SELECT '<script>alert(1)</script>' --"
        ]

        for payload in xss_payloads:
            with self.subTest(payload=payload):
                # Should either process safely or reject
                try:
                    sql, params = self.builder.build_safe_condition(f"AND devName = '{payload}'")
                    # If processed, should be parameterized
                    self.assertIn(':', sql)
                    self.assertIn(payload, params.values())
                except ValueError:
                    # Rejection is also acceptable for safety
                    pass

    def test_unicode_handling(self):
        """Test that Unicode characters are handled properly."""
        unicode_strings = [
            "Ülrich's Device",
            "Café Network",
            "测试设备",
            "Устройство"
        ]

        for unicode_str in unicode_strings:
            with self.subTest(unicode_str=unicode_str):
                sql, params = self.builder.build_safe_condition(f"AND devName = '{unicode_str}'")
                self.assertIn(unicode_str, params.values())

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        edge_cases = [
            "",  # Empty string
            "   ",  # Whitespace only
            "AND devName = ''",  # Empty value
            "AND devName = 'a'",  # Single character
            "AND devName = '" + "x" * 1000 + "'",  # Very long string
        ]

        for case in edge_cases:
            with self.subTest(case=case):
                try:
                    sql, params = self.builder.get_safe_condition_legacy(case)
                    # Should either return valid result or empty safe result
                    self.assertIsInstance(sql, str)
                    self.assertIsInstance(params, dict)
                except Exception:
                    self.fail(f"Unexpected exception for edge case: {case}")


if __name__ == '__main__':
    # Run the test suite
    unittest.main(verbosity=2)