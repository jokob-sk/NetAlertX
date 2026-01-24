"""
Unit tests for device field locking scenarios.

Tests all combinations of field sources (LOCKED, USER, NEWDEV, plugin name)
and verifies that plugin updates are correctly allowed/rejected based on
field source and SET_ALWAYS/SET_EMPTY configuration.
"""

from server.db.authoritative_handler import can_overwrite_field


def test_locked_source_prevents_plugin_overwrite():
    """Field with LOCKED source should NOT be updated by plugins."""
    result = can_overwrite_field(
        field_name="devName",
        current_source="LOCKED",
        plugin_prefix="ARPSCAN",
        plugin_settings={"set_always": [], "set_empty": []},
        field_value="New Name",
    )
    assert result is False, "LOCKED source should prevent plugin overwrites"


def test_user_source_prevents_plugin_overwrite():
    """Field with USER source should NOT be updated by plugins."""
    result = can_overwrite_field(
        field_name="devName",
        current_source="USER",
        plugin_prefix="NBTSCAN",
        plugin_settings={"set_always": [], "set_empty": []},
        field_value="Plugin Discovered Name",
    )
    assert result is False, "USER source should prevent plugin overwrites"


def test_newdev_source_allows_plugin_overwrite():
    """Field with NEWDEV source should be updated by plugins."""
    result = can_overwrite_field(
        field_name="devName",
        current_source="NEWDEV",
        plugin_prefix="NBTSCAN",
        plugin_settings={"set_always": [], "set_empty": []},
        field_value="DiscoveredName",
    )
    assert result is True, "NEWDEV source should allow plugin overwrites"


def test_empty_current_source_allows_plugin_overwrite():
    """Field with empty source should be updated by plugins."""
    result = can_overwrite_field(
        field_name="devName",
        current_source="",
        plugin_prefix="NBTSCAN",
        plugin_settings={"set_always": [], "set_empty": []},
        field_value="DiscoveredName",
    )
    assert result is True, "Empty source should allow plugin overwrites"


def test_plugin_source_allows_same_plugin_overwrite_with_set_always():
    """Field owned by plugin can be updated by same plugin if SET_ALWAYS enabled."""
    result = can_overwrite_field(
        field_name="devName",
        current_source="NBTSCAN",
        plugin_prefix="NBTSCAN",
        plugin_settings={"set_always": ["devName"], "set_empty": []},
        field_value="NewName",
    )
    assert result is True, "Same plugin with SET_ALWAYS should update its own fields"


def test_plugin_source_cannot_overwrite_without_authorization():
    """Plugin cannot update field it already owns without SET_ALWAYS/SET_EMPTY."""
    result = can_overwrite_field(
        field_name="devName",
        current_source="NBTSCAN",
        plugin_prefix="NBTSCAN",
        plugin_settings={"set_always": [], "set_empty": []},
        field_value="NewName",
    )
    assert result is False, "Plugin cannot update owned field without SET_ALWAYS/SET_EMPTY"


def test_plugin_source_allows_different_plugin_overwrite_with_set_always():
    """Field owned by plugin can be overwritten by different plugin if SET_ALWAYS enabled."""
    result = can_overwrite_field(
        field_name="devVendor",
        current_source="ARPSCAN",
        plugin_prefix="PIHOLEAPI",
        plugin_settings={"set_always": ["devVendor"], "set_empty": []},
        field_value="NewVendor",
    )
    assert result is True, "Different plugin with SET_ALWAYS should be able to overwrite"


def test_plugin_source_rejects_different_plugin_without_set_always():
    """Field owned by plugin should NOT be updated by different plugin without SET_ALWAYS."""
    result = can_overwrite_field(
        field_name="devVendor",
        current_source="ARPSCAN",
        plugin_prefix="PIHOLEAPI",
        plugin_settings={"set_always": [], "set_empty": []},
        field_value="NewVendor",
    )
    assert result is False, "Different plugin without SET_ALWAYS should not overwrite plugin-owned fields"


def test_set_empty_allows_overwrite_on_empty_field():
    """SET_EMPTY allows overwriting when field is truly empty."""
    result = can_overwrite_field(
        field_name="devName",
        current_source="NEWDEV",
        plugin_prefix="PIHOLEAPI",
        plugin_settings={"set_always": [], "set_empty": ["devName"]},
        field_value="DiscoveredName",
    )
    assert result is True, "SET_EMPTY should allow overwrite on NEWDEV source"


def test_set_empty_rejects_overwrite_on_non_empty_field():
    """SET_EMPTY should NOT allow overwriting non-empty plugin-owned fields."""
    result = can_overwrite_field(
        field_name="devName",
        current_source="ARPSCAN",
        plugin_prefix="PIHOLEAPI",
        plugin_settings={"set_always": [], "set_empty": ["devName"]},
        field_value="NewName",
    )
    assert result is False, "SET_EMPTY should not allow overwrite on non-empty plugin field"


def test_empty_plugin_value_not_used():
    """Plugin must provide non-empty value for update to occur."""
    result = can_overwrite_field(
        field_name="devName",
        current_source="NEWDEV",
        plugin_prefix="NBTSCAN",
        plugin_settings={"set_always": [], "set_empty": []},
        field_value="",
    )
    assert result is False, "Empty plugin value should be rejected"


def test_whitespace_only_plugin_value_not_used():
    """Plugin providing whitespace-only value should be rejected."""
    result = can_overwrite_field(
        field_name="devName",
        current_source="NEWDEV",
        plugin_prefix="NBTSCAN",
        plugin_settings={"set_always": [], "set_empty": []},
        field_value="   ",
    )
    assert result is False, "Whitespace-only plugin value should be rejected"


def test_none_plugin_value_not_used():
    """Plugin providing None value should be rejected."""
    result = can_overwrite_field(
        field_name="devName",
        current_source="NEWDEV",
        plugin_prefix="NBTSCAN",
        plugin_settings={"set_always": [], "set_empty": []},
        field_value=None,
    )
    assert result is False, "None plugin value should be rejected"


def test_set_always_overrides_plugin_ownership():
    """SET_ALWAYS should allow overwriting any non-protected field."""
    # Test 1: SET_ALWAYS overrides other plugin ownership
    result = can_overwrite_field(
        field_name="devVendor",
        current_source="ARPSCAN",
        plugin_prefix="UNIFIAPI",
        plugin_settings={"set_always": ["devVendor"], "set_empty": []},
        field_value="NewVendor",
    )
    assert result is True, "SET_ALWAYS should override plugin ownership"

    # Test 2: SET_ALWAYS does NOT override USER
    result = can_overwrite_field(
        field_name="devVendor",
        current_source="USER",
        plugin_prefix="UNIFIAPI",
        plugin_settings={"set_always": ["devVendor"], "set_empty": []},
        field_value="NewVendor",
    )
    assert result is False, "SET_ALWAYS should not override USER source"

    # Test 3: SET_ALWAYS does NOT override LOCKED
    result = can_overwrite_field(
        field_name="devVendor",
        current_source="LOCKED",
        plugin_prefix="UNIFIAPI",
        plugin_settings={"set_always": ["devVendor"], "set_empty": []},
        field_value="NewVendor",
    )
    assert result is False, "SET_ALWAYS should not override LOCKED source"


def test_multiple_plugins_set_always_scenarios():
    """Test SET_ALWAYS with multiple different plugins."""
    # current_source, plugin_prefix, has_set_always 
    plugins_scenarios = [
        ("ARPSCAN", "ARPSCAN", False),  # Same plugin, no SET_ALWAYS - BLOCKED
        ("ARPSCAN", "ARPSCAN", True),   # Same plugin, WITH SET_ALWAYS - ALLOWED
        ("ARPSCAN", "NBTSCAN", False),  # Different plugin, no SET_ALWAYS - BLOCKED
        ("ARPSCAN", "PIHOLEAPI", True),  # Different plugin, PIHOLEAPI has SET_ALWAYS - ALLOWED
        ("ARPSCAN", "UNIFIAPI", True),  # Different plugin, UNIFIAPI has SET_ALWAYS - ALLOWED
    ]

    for current_source, plugin_prefix, has_set_always in plugins_scenarios:
        result = can_overwrite_field(
            field_name="devName",
            current_source=current_source,
            plugin_prefix=plugin_prefix,
            plugin_settings={"set_always": ["devName"] if has_set_always else [], "set_empty": []},
            field_value="NewName",
        )

        if has_set_always:
            assert result is True, f"Should allow with SET_ALWAYS: {current_source} -> {plugin_prefix}"
        else:
            assert result is False, f"Should reject without SET_ALWAYS: {current_source} -> {plugin_prefix}"


def test_different_fields_with_different_sources():
    """Test that each field respects its own source tracking."""
    # Device has mixed sources
    fields_sources = [
        ("devName", "USER"),  # User-owned
        ("devVendor", "ARPSCAN"),  # Plugin-owned
        ("devLastIP", "NEWDEV"),  # Default
        ("devFQDN", "LOCKED"),  # Locked
    ]

    results = {}
    for field_name, current_source in fields_sources:
        results[field_name] = can_overwrite_field(
            field_name=field_name,
            current_source=current_source,
            plugin_prefix="NBTSCAN",
            plugin_settings={"set_always": [], "set_empty": []},
            field_value="NewValue",
        )

    # Verify each field's result based on its source
    assert results["devName"] is False, "USER source should prevent overwrite"
    assert results["devVendor"] is False, "Plugin source without SET_ALWAYS should prevent overwrite"
    assert results["devLastIP"] is True, "NEWDEV source should allow overwrite"
    assert results["devFQDN"] is False, "LOCKED source should prevent overwrite"


def test_set_empty_with_empty_string_source():
    """SET_EMPTY with empty string source should allow overwrite."""
    result = can_overwrite_field(
        field_name="devName",
        current_source="",
        plugin_prefix="PIHOLEAPI",
        plugin_settings={"set_always": [], "set_empty": ["devName"]},
        field_value="DiscoveredName",
    )
    assert result is True, "SET_EMPTY with empty source should allow overwrite"
