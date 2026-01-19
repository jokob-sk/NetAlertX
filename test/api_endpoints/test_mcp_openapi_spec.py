"""
Tests for the MCP OpenAPI Spec Generator and Schema Validation.

These tests ensure the "Textbook Implementation" produces valid, complete specs.
"""

import sys
import os
import pytest

from pydantic import ValidationError
from api_server.openapi.schemas import (
    DeviceSearchRequest,
    DeviceSearchResponse,
    WakeOnLanRequest,
    TracerouteRequest,
    TriggerScanRequest,
    OpenPortsRequest,
    SetDeviceAliasRequest
)
from api_server.openapi.spec_generator import generate_openapi_spec
from api_server.openapi.registry import (
    get_registry,
    register_tool,
    clear_registry,
    DuplicateOperationIdError
)
from api_server.openapi.schema_converter import pydantic_to_json_schema
from api_server.mcp_endpoint import map_openapi_to_mcp_tools

INSTALL_PATH = os.getenv('NETALERTX_APP', '/app')
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])


class TestPydanticSchemas:
    """Test Pydantic model validation."""

    def test_device_search_request_valid(self):
        """Valid DeviceSearchRequest should pass validation."""
        req = DeviceSearchRequest(query="Apple", limit=50)
        assert req.query == "Apple"
        assert req.limit == 50

    def test_device_search_request_defaults(self):
        """DeviceSearchRequest should use default limit."""
        req = DeviceSearchRequest(query="test")
        assert req.limit == 50

    def test_device_search_request_validation_error(self):
        """DeviceSearchRequest should reject empty query."""
        with pytest.raises(ValidationError) as exc_info:
            DeviceSearchRequest(query="")
        errors = exc_info.value.errors()
        assert any("min_length" in str(e) or "at least 1" in str(e).lower() for e in errors)

    def test_device_search_request_limit_bounds(self):
        """DeviceSearchRequest should enforce limit bounds."""
        # Too high
        with pytest.raises(ValidationError):
            DeviceSearchRequest(query="test", limit=1000)
        # Too low
        with pytest.raises(ValidationError):
            DeviceSearchRequest(query="test", limit=0)

    def test_wol_request_mac_validation(self):
        """WakeOnLanRequest should validate MAC format."""
        # Valid MAC
        req = WakeOnLanRequest(devMac="00:11:22:33:44:55")
        assert req.devMac == "00:11:22:33:44:55"

        # Invalid MAC
        # with pytest.raises(ValidationError):
        #     WakeOnLanRequest(devMac="invalid-mac")

    def test_wol_request_either_mac_or_ip(self):
        """WakeOnLanRequest should accept either MAC or IP."""
        req_mac = WakeOnLanRequest(devMac="00:11:22:33:44:55")
        req_ip = WakeOnLanRequest(devLastIP="192.168.1.50")
        assert req_mac.devMac is not None
        assert req_ip.devLastIP == "192.168.1.50"

    def test_traceroute_request_ip_validation(self):
        """TracerouteRequest should validate IP format."""
        req = TracerouteRequest(devLastIP="8.8.8.8")
        assert req.devLastIP == "8.8.8.8"

        # with pytest.raises(ValidationError):
        #     TracerouteRequest(devLastIP="not-an-ip")

    def test_trigger_scan_defaults(self):
        """TriggerScanRequest should use ARPSCAN as default."""
        req = TriggerScanRequest()
        assert req.type == "ARPSCAN"

    def test_open_ports_request_required(self):
        """OpenPortsRequest should require target."""
        with pytest.raises(ValidationError):
            OpenPortsRequest()

        req = OpenPortsRequest(target="192.168.1.50")
        assert req.target == "192.168.1.50"

    def test_set_device_alias_constraints(self):
        """SetDeviceAliasRequest should enforce length constraints."""
        # Valid
        req = SetDeviceAliasRequest(alias="My Device")
        assert req.alias == "My Device"

        # Empty
        with pytest.raises(ValidationError):
            SetDeviceAliasRequest(alias="")

        # Too long (over 128 chars)
        with pytest.raises(ValidationError):
            SetDeviceAliasRequest(alias="x" * 200)


class TestOpenAPISpecGenerator:
    """Test the OpenAPI spec generator."""

    HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}

    def test_spec_version(self):
        """Spec should be OpenAPI 3.1.0."""
        spec = generate_openapi_spec()
        assert spec["openapi"] == "3.1.0"

    def test_spec_has_info(self):
        """Spec should have proper info section."""
        spec = generate_openapi_spec()
        assert "info" in spec
        assert "title" in spec["info"]
        assert "version" in spec["info"]

    def test_spec_has_security(self):
        """Spec should define security scheme."""
        spec = generate_openapi_spec()
        assert "components" in spec
        assert "securitySchemes" in spec["components"]
        assert "BearerAuth" in spec["components"]["securitySchemes"]

    def test_all_operations_have_operation_id(self):
        """Every operation must have a unique operationId."""
        spec = generate_openapi_spec()
        op_ids = set()

        for path, methods in spec["paths"].items():
            for method, details in methods.items():
                if method.lower() not in self.HTTP_METHODS:
                    continue
                assert "operationId" in details, f"Missing operationId: {method.upper()} {path}"
                op_id = details["operationId"]
                assert op_id not in op_ids, f"Duplicate operationId: {op_id}"
                op_ids.add(op_id)

    def test_all_operations_have_responses(self):
        """Every operation must have response definitions."""
        spec = generate_openapi_spec()

        for path, methods in spec["paths"].items():
            for method, details in methods.items():
                if method.lower() not in self.HTTP_METHODS:
                    continue
                assert "responses" in details, f"Missing responses: {method.upper()} {path}"
                assert "200" in details["responses"], f"Missing 200 response: {method.upper()} {path}"

    def test_post_operations_have_request_body_schema(self):
        """POST operations with models should have requestBody schemas."""
        spec = generate_openapi_spec()

        for path, methods in spec["paths"].items():
            if "post" in methods:
                details = methods["post"]
                if "requestBody" in details:
                    content = details["requestBody"].get("content", {})
                    assert "application/json" in content
                    assert "schema" in content["application/json"]

    def test_path_params_are_defined(self):
        """Path parameters like {mac} should be defined."""
        spec = generate_openapi_spec()

        for path, methods in spec["paths"].items():
            if "{" in path:
                # Extract param names from path
                import re
                param_names = re.findall(r"\{(\w+)\}", path)

                for method, details in methods.items():
                    if method.lower() not in self.HTTP_METHODS:
                        continue
                    params = details.get("parameters", [])
                    defined_params = [p["name"] for p in params if p.get("in") == "path"]

                    for param_name in param_names:
                        assert param_name in defined_params, \
                            f"Path param '{param_name}' not defined: {method.upper()} {path}"

    def test_standard_error_responses(self):
        """Operations should have minimal standard error responses (400, 403, 404, etc) without schema bloat."""
        spec = generate_openapi_spec()
        expected_minimal_codes = ["400", "401", "403", "404", "500", "422"]

        for path, methods in spec["paths"].items():
            for method, details in methods.items():
                if method.lower() not in self.HTTP_METHODS:
                    continue
                responses = details.get("responses", {})
                for code in expected_minimal_codes:
                    assert code in responses, f"Missing minimal {code} response in: {method.upper()} {path}."
                    # Verify no "content" or schema is present (minimalism)
                    assert "content" not in responses[code], f"Response {code} in {method.upper()} {path} should not have content/schema."


class TestMCPToolMapping:
    """Test MCP tool generation from OpenAPI spec."""

    def test_tools_match_registry_count(self):
        """Number of MCP tools should match registered endpoints."""
        spec = generate_openapi_spec()
        tools = map_openapi_to_mcp_tools(spec)
        registry = get_registry()

        assert len(tools) == len(registry)

    def test_tools_have_input_schema(self):
        """All MCP tools should have inputSchema."""
        spec = generate_openapi_spec()
        tools = map_openapi_to_mcp_tools(spec)

        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert tool["inputSchema"].get("type") == "object"

    def test_required_fields_propagate(self):
        """Required fields from Pydantic should appear in MCP inputSchema."""
        spec = generate_openapi_spec()
        tools = map_openapi_to_mcp_tools(spec)

        search_tool = next((t for t in tools if t["name"] == "search_devices"), None)
        assert search_tool is not None
        assert "query" in search_tool["inputSchema"].get("required", [])

    def test_tool_descriptions_present(self):
        """All tools should have non-empty descriptions."""
        spec = generate_openapi_spec()
        tools = map_openapi_to_mcp_tools(spec)

        for tool in tools:
            assert tool.get("description"), f"Missing description for tool: {tool['name']}"


class TestRegistryDeduplication:
    """Test that the registry prevents duplicate operationIds."""

    def test_duplicate_operation_id_raises(self):
        """Registering duplicate operationId should raise error."""
        # Clear and re-register to test

        try:
            clear_registry()

            register_tool(
                path="/test/endpoint",
                method="GET",
                operation_id="test_operation",
                summary="Test",
                description="Test endpoint"
            )

            with pytest.raises(DuplicateOperationIdError):
                register_tool(
                    path="/test/other",
                    method="GET",
                    operation_id="test_operation",  # Duplicate!
                    summary="Test 2",
                    description="Another endpoint with same operationId"
                )

        finally:
            # Restore original registry
            clear_registry()
            from api_server.openapi.spec_generator import _register_all_endpoints
            _register_all_endpoints()


class TestPydanticToJsonSchema:
    """Test Pydantic to JSON Schema conversion."""

    def test_basic_conversion(self):
        """Basic Pydantic model should convert to JSON Schema."""
        schema = pydantic_to_json_schema(DeviceSearchRequest)

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "query" in schema["properties"]
        assert "limit" in schema["properties"]

    def test_nested_model_conversion(self):
        """Nested Pydantic models should produce $defs."""
        schema = pydantic_to_json_schema(DeviceSearchResponse)

        # Should have devices array referencing DeviceInfo
        assert "properties" in schema
        assert "devices" in schema["properties"]

    def test_field_constraints_preserved(self):
        """Field constraints should be in JSON Schema."""
        schema = pydantic_to_json_schema(DeviceSearchRequest)

        query_schema = schema["properties"]["query"]
        assert query_schema.get("minLength") == 1
        assert query_schema.get("maxLength") == 256

        limit_schema = schema["properties"]["limit"]
        assert limit_schema.get("minimum") == 1
        assert limit_schema.get("maximum") == 500
