import pytest
from unittest.mock import patch
from flask import Flask
from server.api_server import spec_generator, mcp_endpoint


# Helper to reset state between tests
@pytest.fixture(autouse=True)
def reset_registry():
    spec_generator.clear_registry()
    spec_generator._disabled_tools.clear()
    yield
    spec_generator.clear_registry()
    spec_generator._disabled_tools.clear()


def test_disable_tool_management():
    """Test enabling and disabling tools."""
    # Register a dummy tool
    spec_generator.register_tool(
        path="/test",
        method="GET",
        operation_id="test_tool",
        summary="Test Tool",
        description="A test tool"
    )

    # Initially enabled
    assert not spec_generator.is_tool_disabled("test_tool")
    assert "test_tool" not in spec_generator.get_disabled_tools()

    # Disable it
    assert spec_generator.set_tool_disabled("test_tool", True)
    assert spec_generator.is_tool_disabled("test_tool")
    assert "test_tool" in spec_generator.get_disabled_tools()

    # Enable it
    assert spec_generator.set_tool_disabled("test_tool", False)
    assert not spec_generator.is_tool_disabled("test_tool")
    assert "test_tool" not in spec_generator.get_disabled_tools()

    # Try to disable non-existent tool
    assert not spec_generator.set_tool_disabled("non_existent", True)


def test_get_tools_status():
    """Test getting the status of all tools."""
    spec_generator.register_tool(
        path="/tool1",
        method="GET",
        operation_id="tool1",
        summary="Tool 1",
        description="First tool"
    )
    spec_generator.register_tool(
        path="/tool2",
        method="GET",
        operation_id="tool2",
        summary="Tool 2",
        description="Second tool"
    )

    spec_generator.set_tool_disabled("tool1", True)

    status = spec_generator.get_tools_status()

    assert len(status) == 2

    t1 = next(t for t in status if t["operation_id"] == "tool1")
    t2 = next(t for t in status if t["operation_id"] == "tool2")

    assert t1["disabled"] is True
    assert t1["summary"] == "Tool 1"

    assert t2["disabled"] is False
    assert t2["summary"] == "Tool 2"


def test_openapi_spec_injection():
    """Test that x-mcp-disabled is injected into OpenAPI spec."""
    spec_generator.register_tool(
        path="/test",
        method="GET",
        operation_id="test_tool",
        summary="Test Tool",
        description="A test tool"
    )

    # Disable it
    spec_generator.set_tool_disabled("test_tool", True)

    spec = spec_generator.generate_openapi_spec()
    path_entry = spec["paths"]["/test"]
    method_key = next(iter(path_entry))
    operation = path_entry[method_key]

    assert "x-mcp-disabled" in operation
    assert operation["x-mcp-disabled"] is True

    # Re-enable
    spec_generator.set_tool_disabled("test_tool", False)
    spec = spec_generator.generate_openapi_spec()
    path_entry = spec["paths"]["/test"]
    method_key = next(iter(path_entry))
    operation = path_entry[method_key]

    assert "x-mcp-disabled" not in operation


@patch("server.api_server.mcp_endpoint.get_setting_value")
@patch("requests.get")
def test_execute_disabled_tool(mock_get, mock_setting):
    """Test that executing a disabled tool returns an error."""
    mock_setting.return_value = 8000

    # Create a dummy app for context
    app = Flask(__name__)

    # Register tool
    spec_generator.register_tool(
        path="/test",
        method="GET",
        operation_id="test_tool",
        summary="Test Tool",
        description="A test tool"
    )

    route = mcp_endpoint.find_route_for_tool("test_tool")

    with app.test_request_context():
        # 1. Test enabled (mock request)
        mock_get.return_value.json.return_value = {"success": True}
        mock_get.return_value.status_code = 200

        result = mcp_endpoint._execute_tool(route, {})
        assert not result["isError"]

        # 2. Disable tool
        spec_generator.set_tool_disabled("test_tool", True)

        result = mcp_endpoint._execute_tool(route, {})
        assert result["isError"]
        assert "is disabled" in result["content"][0]["text"]

        # Ensure no HTTP request was made for the second call
        assert mock_get.call_count == 1
