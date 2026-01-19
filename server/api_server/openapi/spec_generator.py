#!/usr/bin/env python
"""
NetAlertX OpenAPI Specification Generator

This module provides a registry-based approach to OpenAPI spec generation.
It converts Pydantic models to JSON Schema and assembles a complete OpenAPI 3.1 spec.

Key Features:
- Automatic Pydantic -> JSON Schema conversion
- Centralized endpoint registry
- Unique operationId enforcement
- Complete request/response schema generation

Usage:
    from spec_generator import registry, generate_openapi_spec, register_tool

    # Register endpoints (typically done at module load)
    register_tool(
        path="/devices/search",
        method="POST",
        operation_id="search_devices",
        description="Search for devices",
        request_model=DeviceSearchRequest,
        response_model=DeviceSearchResponse
    )

    # Generate spec (called by MCP endpoint)
    spec = generate_openapi_spec()
"""

from __future__ import annotations

import threading
from typing import Optional, List, Dict, Any

from .registry import (
    clear_registry,
    _registry,
    _registry_lock,
    _disabled_tools
)
from .introspection import introspect_flask_app, introspect_graphql_schema
from .schema_converter import (
    build_parameters,
    build_request_body,
    build_responses
)

_rebuild_lock = threading.Lock()


def generate_openapi_spec(
    title: str = "NetAlertX API",
    version: str = "2.0.0",
    description: str = "NetAlertX Network Monitoring API - MCP Compatible",
    servers: Optional[List[Dict[str, str]]] = None,
    flask_app: Optional[Any] = None
) -> Dict[str, Any]:
    """Assemble a complete OpenAPI specification from the registered endpoints."""

    with _rebuild_lock:
        # If no app provided and registry is empty, try to use the one from api_server_start
        if not flask_app and not _registry:
            try:
                from ..api_server_start import app as start_app
                flask_app = start_app
            except (ImportError, AttributeError):
                pass

        # If we are in "dynamic mode", we rebuild the registry from code
        if flask_app:
            from ..graphql_endpoint import devicesSchema
            clear_registry()
            introspect_graphql_schema(devicesSchema)
            introspect_flask_app(flask_app)

        spec = {
            "openapi": "3.1.0",
            "info": {
                "title": title,
                "version": version,
                "description": description,
                "contact": {
                    "name": "NetAlertX",
                    "url": "https://github.com/jokob-sk/NetAlertX"
                }
            },
            "servers": servers or [{"url": "/", "description": "Local server"}],
            "security": [
                {"BearerAuth": []}
            ],
            "components": {
                "securitySchemes": {
                    "BearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "description": "API token from NetAlertX settings (API_TOKEN)"
                    }
                },
                "schemas": {}
            },
            "paths": {},
            "tags": []
        }

        definitions = {}

        # Collect unique tags
        tag_set = set()

        with _registry_lock:
            disabled_snapshot = _disabled_tools.copy()
            for entry in _registry:
                path = entry["path"]
                method = entry["method"].lower()

                # Initialize path if not exists
                if path not in spec["paths"]:
                    spec["paths"][path] = {}

                # Build operation object
                operation = {
                    "operationId": entry["operation_id"],
                    "summary": entry["summary"],
                    "description": entry["description"],
                    "tags": entry["tags"],
                    "deprecated": entry["deprecated"]
                }

                # Inject disabled status if applicable
                if entry["operation_id"] in disabled_snapshot:
                    operation["x-mcp-disabled"] = True

                # Inject original ID if suffixed (Coderabbit fix)
                if entry.get("original_operation_id"):
                    operation["x-original-operationId"] = entry["original_operation_id"]

                # Add parameters (path + query)
                parameters = build_parameters(entry)
                if parameters:
                    operation["parameters"] = parameters

                # Add request body for POST/PUT/PATCH/DELETE
                if method in ("post", "put", "patch", "delete") and entry.get("request_model"):
                    request_body = build_request_body(
                        entry["request_model"],
                        definitions,
                        allow_multipart_payload=entry.get("allow_multipart_payload", False)
                    )
                    if request_body:
                        operation["requestBody"] = request_body

                # Add responses
                operation["responses"] = build_responses(
                    entry.get("response_model"), definitions
                )

                spec["paths"][path][method] = operation

                # Collect tags
                for tag in entry["tags"]:
                    tag_set.add(tag)

        spec["components"]["schemas"] = definitions

        # Build tags array with descriptions
        tag_descriptions = {
            "devices": "Device management and queries",
            "nettools": "Network diagnostic tools",
            "events": "Event and alert management",
            "sessions": "Session history tracking",
            "messaging": "In-app notifications",
            "settings": "Configuration management",
            "sync": "Data synchronization",
            "logs": "Log file access",
            "dbquery": "Direct database queries"
        }

        spec["tags"] = [
            {"name": tag, "description": tag_descriptions.get(tag, f"{tag.title()} operations")}
            for tag in sorted(tag_set)
        ]

        return spec


# Initialize registry on module load
# Registry is now populated dynamically via introspection in generate_openapi_spec
def _register_all_endpoints():
    """Dummy function for compatibility with legacy tests."""
    pass
