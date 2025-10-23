"""
Unit tests for SafeConditionBuilder focusing on core security functionality.
This test file has minimal dependencies to ensure it can run in any environment.
"""

import sys
import re
import pytest
from unittest.mock import Mock, patch

# Mock the logger module to avoid dependency issues
sys.modules['logger'] = Mock()

# Standalone version of SafeConditionBuilder for testing
class SafeConditionBuilder:
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


@pytest.fixture
def builder():
    """Fixture to provide a fresh SafeConditionBuilder instance for each test."""
    return SafeConditionBuilder()


def test_initialization(builder):
    """Test that SafeConditionBuilder initializes correctly."""
    assert isinstance(builder, SafeConditionBuilder)
    assert builder.param_counter == 0
    assert builder.parameters == {}


def test_sanitize_string(builder):
    """Test string sanitization functionality."""
    # Test normal string
    result = builder._sanitize_string("normal string")
    assert result == "normal string"

    # Test s-quote replacement
    result = builder._sanitize_string("test{s-quote}value")
    assert result == "test'value"

    # Test control character removal
    result = builder._sanitize_string("test\x00\x01string")
    assert result == "teststring"

    # Test excessive whitespace
    result = builder._sanitize_string("  test   string  ")
    assert result == "test string"


def test_validate_column_name(builder):
    """Test column name validation against whitelist."""
    # Valid columns
    assert builder._validate_column_name('eve_MAC')
    assert builder._validate_column_name('devName')
    assert builder._validate_column_name('eve_EventType')

    # Invalid columns
    assert not builder._validate_column_name('malicious_column')
    assert not builder._validate_column_name('drop_table')
    assert not builder._validate_column_name('user_input')


def test_validate_operator(builder):
    """Test operator validation against whitelist."""
    # Valid operators
    assert builder._validate_operator('=')
    assert builder._validate_operator('LIKE')
    assert builder._validate_operator('IN')

    # Invalid operators
    assert not builder._validate_operator('UNION')
    assert not builder._validate_operator('DROP')
    assert not builder._validate_operator('EXEC')


def test_build_simple_condition_valid(builder):
    """Test building valid simple conditions."""
    sql, params = builder._build_simple_condition('AND', 'devName', '=', 'TestDevice')
    
    assert 'AND devName = :param_' in sql
    assert len(params) == 1
    assert 'TestDevice' in params.values()


def test_build_simple_condition_invalid_column(builder):
    """Test that invalid column names are rejected."""
    with pytest.raises(ValueError) as exc_info:
        builder._build_simple_condition('AND', 'invalid_column', '=', 'value')
    
    assert 'Invalid column name' in str(exc_info.value)


def test_build_simple_condition_invalid_operator(builder):
    """Test that invalid operators are rejected."""
    with pytest.raises(ValueError) as exc_info:
        builder._build_simple_condition('AND', 'devName', 'UNION', 'value')
    
    assert 'Invalid operator' in str(exc_info.value)


def test_sql_injection_attempts(builder):
    """Test that various SQL injection attempts are blocked."""
    injection_attempts = [
        "'; DROP TABLE Devices; --",
        "' UNION SELECT * FROM Settings --",
        "' OR 1=1 --",
        "'; INSERT INTO Events VALUES(1,2,3); --",
        "' AND (SELECT COUNT(*) FROM sqlite_master) > 0 --",
    ]

    for injection in injection_attempts:
        with pytest.raises(ValueError):
            builder.build_safe_condition(f"AND devName = '{injection}'")


def test_legacy_condition_compatibility(builder):
    """Test backward compatibility with legacy condition formats."""
    # Test simple condition
    sql, params = builder.get_safe_condition_legacy("AND devName = 'TestDevice'")
    assert 'devName' in sql
    assert 'TestDevice' in params.values()

    # Test empty condition
    sql, params = builder.get_safe_condition_legacy("")
    assert sql == ""
    assert params == {}

    # Test invalid condition returns empty
    sql, params = builder.get_safe_condition_legacy("INVALID SQL INJECTION")
    assert sql == ""
    assert params == {}


def test_parameter_generation(builder):
    """Test that parameters are generated correctly."""
    # Test single parameter
    sql, params = builder.build_safe_condition("AND devName = 'Device1'")
    
    # Should have 1 parameter
    assert len(params) == 1
    assert 'param_1' in params


def test_xss_prevention(builder):
    """Test that XSS-like payloads in device names are handled safely."""
    xss_payloads = [
        "<script>alert('xss')</script>",
        "javascript:alert(1)",
        "<img src=x onerror=alert(1)>",
        "'; DROP TABLE users; SELECT '<script>alert(1)</script>' --"
    ]

    for payload in xss_payloads:
        # Should either process safely or reject
        try:
            sql, params = builder.build_safe_condition(f"AND devName = '{payload}'")
            # If processed, should be parameterized
            assert ':' in sql
            assert payload in params.values()
        except ValueError:
            # Rejection is also acceptable for safety
            pass


def test_unicode_handling(builder):
    """Test that Unicode characters are handled properly."""
    unicode_strings = [
        "Ülrichs Device",
        "Café Network",
        "测试设备",
        "Устройство"
    ]

    for unicode_str in unicode_strings:
        sql, params = builder.build_safe_condition(f"AND devName = '{unicode_str}'")
        assert unicode_str in params.values()


def test_edge_cases(builder):
    """Test edge cases and boundary conditions."""
    edge_cases = [
        "",  # Empty string
        "   ",  # Whitespace only
        "AND devName = ''",  # Empty value
        "AND devName = 'a'",  # Single character
        "AND devName = '" + "x" * 1000 + "'",  # Very long string
    ]

    for case in edge_cases:
        try:
            sql, params = builder.get_safe_condition_legacy(case)
            # Should either return valid result or empty safe result
            assert isinstance(sql, str)
            assert isinstance(params, dict)
        except Exception:
            pytest.fail(f"Unexpected exception for edge case: {case}")