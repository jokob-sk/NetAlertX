
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Use cwd as fallback if env var is not set, assuming running from project root
INSTALL_PATH = os.getenv('NETALERTX_APP', os.getcwd())
sys.path.extend([f"{INSTALL_PATH}/server/plugins", f"{INSTALL_PATH}/server"])

from api_server.openapi.spec_generator import generate_openapi_spec
from api_server.api_server_start import app

class TestMCPDisabledTools:
    
    def test_disabled_tools_via_env_var(self):
        """Test that MCP_DISABLED_TOOLS env var disables specific tools."""
        # Clean registry first to ensure clean state
        from api_server.openapi.registry import clear_registry
        clear_registry()

        # Mock get_setting_value to return None (simulating no config setting)
        # and mock os.getenv to return our target list
        with patch("helper.get_setting_value", return_value=None), \
             patch.dict(os.environ, {"MCP_DISABLED_TOOLS": "search_devices_api"}):
            
            spec = generate_openapi_spec(flask_app=app)
            
            # Locate the operation
            # search_devices_api is usually mapped to /devices/search [POST] or similar
            # We search the spec for the operationId
            
            found = False
            for path, methods in spec["paths"].items():
                for method, op in methods.items():
                    if op["operationId"] == "search_devices_api":
                        assert op.get("x-mcp-disabled") is True
                        found = True
            
            assert found, "search_devices_api operation not found in spec"

    def test_disabled_tools_default_fallback(self):
        """Test fallback to defaults when no setting or env var exists."""
        from api_server.openapi.registry import clear_registry
        clear_registry()

        with patch("helper.get_setting_value", return_value=None), \
             patch.dict(os.environ, {}, clear=True): # Clear env to ensure no MCP_DISABLED_TOOLS
            
            spec = generate_openapi_spec(flask_app=app)
            
            # Default is "dbquery_read,dbquery_write"
            
            # Check dbquery_read
            found_read = False
            for path, methods in spec["paths"].items():
                for method, op in methods.items():
                    if op["operationId"] == "dbquery_read":
                        assert op.get("x-mcp-disabled") is True
                        found_read = True
            
            assert found_read, "dbquery_read should be disabled by default"

