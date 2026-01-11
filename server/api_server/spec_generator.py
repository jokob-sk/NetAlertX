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
from typing import Optional, Type, Any, Dict, List, Literal
from pydantic import BaseModel

# Thread-safe registry
_registry: List[Dict[str, Any]] = []
_registry_lock = threading.Lock()
_operation_ids: set = set()
_disabled_tools: set = set()


class DuplicateOperationIdError(Exception):
    """Raised when an operationId is registered more than once."""
    pass


def set_tool_disabled(operation_id: str, disabled: bool = True) -> bool:
    """
    Enable or disable a tool by operation_id.

    Args:
        operation_id: The unique operation_id of the tool
        disabled: True to disable, False to enable

    Returns:
        bool: True if operation_id exists, False otherwise
    """
    with _registry_lock:
        if operation_id not in _operation_ids:
            return False

        if disabled:
            _disabled_tools.add(operation_id)
        else:
            _disabled_tools.discard(operation_id)
        return True


def is_tool_disabled(operation_id: str) -> bool:
    """Check if a tool is disabled."""
    with _registry_lock:
        return operation_id in _disabled_tools


def get_disabled_tools() -> List[str]:
    """Get list of all disabled operation_ids."""
    with _registry_lock:
        return list(_disabled_tools)


def get_tools_status() -> List[Dict[str, Any]]:
    """
    Get a list of all registered tools and their disabled status.
    Useful for backend-to-frontend communication.
    """
    tools = []
    with _registry_lock:
        disabled_snapshot = _disabled_tools.copy()
        for entry in _registry:
            tools.append({
                "operation_id": entry["operation_id"],
                "summary": entry["summary"],
                "disabled": entry["operation_id"] in disabled_snapshot
            })
    return tools


def register_tool(
    path: str,
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"],
    operation_id: str,
    summary: str,
    description: str,
    request_model: Optional[Type[BaseModel]] = None,
    response_model: Optional[Type[BaseModel]] = None,
    path_params: Optional[List[Dict[str, Any]]] = None,
    query_params: Optional[List[Dict[str, Any]]] = None,
    tags: Optional[List[str]] = None,
    deprecated: bool = False
) -> None:
    """
    Register an API endpoint for OpenAPI spec generation.

    Args:
        path: URL path (e.g., "/devices/{mac}")
        method: HTTP method
        operation_id: Unique identifier for this operation (MUST be unique across entire spec)
        summary: Short summary for the operation
        description: Detailed description
        request_model: Pydantic model for request body (POST/PUT/PATCH)
        response_model: Pydantic model for success response
        path_params: List of path parameter definitions
        query_params: List of query parameter definitions
        tags: OpenAPI tags for grouping
        deprecated: Whether this endpoint is deprecated

    Raises:
        DuplicateOperationIdError: If operation_id already exists in registry
    """
    with _registry_lock:
        if operation_id in _operation_ids:
            raise DuplicateOperationIdError(
                f"operationId '{operation_id}' is already registered. "
                "Each operationId must be unique across the entire API."
            )
        _operation_ids.add(operation_id)

        _registry.append({
            "path": path,
            "method": method.upper(),
            "operation_id": operation_id,
            "summary": summary,
            "description": description,
            "request_model": request_model,
            "response_model": response_model,
            "path_params": path_params or [],
            "query_params": query_params or [],
            "tags": tags or ["default"],
            "deprecated": deprecated
        })


def clear_registry() -> None:
    """Clear all registered endpoints (useful for testing)."""
    with _registry_lock:
        _registry.clear()
        _operation_ids.clear()
        _disabled_tools.clear()


def get_registry() -> List[Dict[str, Any]]:
    """Get a copy of the current registry."""
    with _registry_lock:
        return _registry.copy()


def pydantic_to_json_schema(model: Type[BaseModel]) -> Dict[str, Any]:
    """
    Convert a Pydantic model to JSON Schema (OpenAPI 3.1 compatible).

    Uses Pydantic's built-in schema generation which produces
    JSON Schema Draft 2020-12 compatible output.

    Args:
        model: Pydantic BaseModel class

    Returns:
        JSON Schema dictionary
    """
    # Pydantic v2 uses model_json_schema()
    schema = model.model_json_schema(mode="serialization")

    # Remove $defs if empty (cleaner output)
    if "$defs" in schema and not schema["$defs"]:
        del schema["$defs"]

    return schema


def _build_parameters(entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build OpenAPI parameters array from path and query params."""
    parameters = []

    # Path parameters
    for param in entry.get("path_params", []):
        parameters.append({
            "name": param["name"],
            "in": "path",
            "required": True,
            "description": param.get("description", ""),
            "schema": param.get("schema", {"type": "string"})
        })

    # Query parameters
    for param in entry.get("query_params", []):
        parameters.append({
            "name": param["name"],
            "in": "query",
            "required": param.get("required", False),
            "description": param.get("description", ""),
            "schema": param.get("schema", {"type": "string"})
        })

    return parameters


def _build_request_body(model: Optional[Type[BaseModel]]) -> Optional[Dict[str, Any]]:
    """Build OpenAPI requestBody from Pydantic model."""
    if model is None:
        return None

    schema = pydantic_to_json_schema(model)

    return {
        "required": True,
        "content": {
            "application/json": {
                "schema": schema
            }
        }
    }


def _strip_validation(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively remove validation constraints from a JSON schema.
    Keeps structure and descriptions, but removes pattern, minLength, etc.
    This saves context tokens for LLMs which don't validate server output.
    """
    if not isinstance(schema, dict):
        return schema

    # Keys to remove
    validation_keys = [
        "pattern", "minLength", "maxLength", "minimum", "maximum",
        "exclusiveMinimum", "exclusiveMaximum", "multipleOf", "minItems",
        "maxItems", "uniqueItems", "minProperties", "maxProperties"
    ]

    clean_schema = {k: v for k, v in schema.items() if k not in validation_keys}

    # Recursively clean sub-schemas
    if "properties" in clean_schema:
        clean_schema["properties"] = {
            k: _strip_validation(v) for k, v in clean_schema["properties"].items()
        }

    if "items" in clean_schema:
        clean_schema["items"] = _strip_validation(clean_schema["items"])

    if "allOf" in clean_schema:
        clean_schema["allOf"] = [_strip_validation(x) for x in clean_schema["allOf"]]

    if "anyOf" in clean_schema:
        clean_schema["anyOf"] = [_strip_validation(x) for x in clean_schema["anyOf"]]

    if "oneOf" in clean_schema:
        clean_schema["oneOf"] = [_strip_validation(x) for x in clean_schema["oneOf"]]

    if "$defs" in clean_schema:
        clean_schema["$defs"] = {
            k: _strip_validation(v) for k, v in clean_schema["$defs"].items()
        }

    return clean_schema


def _build_responses(
    response_model: Optional[Type[BaseModel]]
) -> Dict[str, Any]:
    """Build OpenAPI responses object."""
    responses = {}

    # Success response (200)
    if response_model:
        # Strip validation from response schema to save tokens
        schema = _strip_validation(pydantic_to_json_schema(response_model))
        responses["200"] = {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "schema": schema
                }
            }
        }
    else:
        responses["200"] = {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean"},
                            "message": {"type": "string"}
                        }
                    }
                }
            }
        }

    # Standard error responses - MINIMIZED context
    # Annotate that these errors can occur, but provide no schema/content to save tokens.
    # The LLM knows what "Bad Request" or "Not Found" means.
    error_codes = {
        "400": "Bad Request",
        "401": "Unauthorized",
        "403": "Forbidden",
        "404": "Not Found",
        "422": "Validation Error",
        "500": "Internal Server Error"
    }

    for code, desc in error_codes.items():
        responses[code] = {
            "description": desc
            # No "content" schema provided
        }

    return responses


def _flatten_defs(spec: Dict[str, Any]) -> None:
    """
    Experimental: Flatten $defs if they are single-use or small.
    This is complex in pure Python without deep traversal logic.
    For now, we will rely on Pydantic's optimized output, but ensures
    we strip unused defs if any remain.
    """
    pass


def generate_openapi_spec(
    title: str = "NetAlertX API",
    version: str = "2.0.0",
    description: str = "NetAlertX Network Monitoring API - MCP Compatible",
    servers: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """Assemble a complete OpenAPI specification from the registered endpoints."""
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
            }
        },
        "paths": {},
        "tags": []
    }

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

            # Add parameters (path + query)
            parameters = _build_parameters(entry)
            if parameters:
                operation["parameters"] = parameters

            # Add request body for POST/PUT/PATCH
            if method in ("post", "put", "patch") and entry.get("request_model"):
                request_body = _build_request_body(entry["request_model"])
                if request_body:
                    operation["requestBody"] = request_body

            # Add responses
            operation["responses"] = _build_responses(
                entry.get("response_model")
            )

            spec["paths"][path][method] = operation

            # Collect tags
            for tag in entry["tags"]:
                tag_set.add(tag)

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


# =============================================================================
# REGISTER ALL NETALERTX ENDPOINTS
# =============================================================================

def _register_all_endpoints():
    """Register all NetAlertX API endpoints."""
    # Import schemas here to avoid circular imports
    from .schemas import (
        DeviceSearchRequest, DeviceSearchResponse,
        DeviceListRequest, DeviceListResponse,
        DeviceInfo, DeviceExportResponse,
        GetDeviceResponse, DeviceUpdateRequest,
        SetDeviceAliasRequest, BaseResponse,
        DeviceTotalsResponse, DeleteDevicesRequest,
        DeviceImportRequest, DeviceImportResponse,
        UpdateDeviceColumnRequest, CopyDeviceRequest,
        TriggerScanRequest, TriggerScanResponse,
        OpenPortsRequest, OpenPortsResponse,
        WakeOnLanRequest, WakeOnLanResponse,
        TracerouteRequest, TracerouteResponse,
        NmapScanRequest, NslookupRequest,
        RecentEventsResponse, LastEventsResponse,
        NetworkTopologyResponse, CreateEventRequest,
        CreateSessionRequest, DeleteSessionRequest,
        CreateNotificationRequest, SyncPushRequest,
        SyncPullResponse, DbQueryRequest,
        DbQueryResponse, DbQueryUpdateRequest,
        DbQueryDeleteRequest, AddToQueueRequest,
        GetSettingResponse
    )

    # -------------------------------------------------------------------------
    # DEVICES
    # -------------------------------------------------------------------------
    register_tool(
        path="/devices/search",
        method="POST",
        operation_id="search_devices",
        summary="Search Devices",
        description="Search for devices based on various criteria like name, IP, MAC, or vendor. "
                    "Returns matching devices with full details.",
        request_model=DeviceSearchRequest,
        response_model=DeviceSearchResponse,
        tags=["devices"]
    )

    register_tool(
        path="/devices/by-status",
        method="POST",
        operation_id="list_devices_by_status",
        summary="List Devices by Status",
        description="List devices filtered by their online/offline status. "
                    "Accepts optional 'status' field (online/offline/all).",
        request_model=DeviceListRequest,
        response_model=DeviceListResponse,
        tags=["devices"]
    )

    register_tool(
        path="/device/{mac}",
        method="GET",
        operation_id="get_device_info",
        summary="Get Device Info",
        description="Retrieve detailed information about a specific device by MAC address.",
        path_params=[{
            "name": "mac",
            "description": "Device MAC address (e.g., 00:11:22:33:44:55)",
            "schema": {"type": "string", "pattern": "^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"}
        }],
        response_model=DeviceInfo,
        tags=["devices"]
    )

    register_tool(
        path="/device/{mac}",
        method="POST",
        operation_id="update_device",
        summary="Update Device",
        description="Update a device's fields or create a new one if createNew is set to True.",
        path_params=[{
            "name": "mac",
            "description": "Device MAC address",
            "schema": {"type": "string"}
        }],
        request_model=DeviceUpdateRequest,
        response_model=BaseResponse,
        tags=["devices"]
    )

    register_tool(
        path="/device/{mac}/delete",
        method="DELETE",
        operation_id="delete_device",
        summary="Delete Device",
        description="Delete a device by MAC address.",
        path_params=[{
            "name": "mac",
            "description": "Device MAC address",
            "schema": {"type": "string"}
        }],
        response_model=BaseResponse,
        tags=["devices"]
    )

    register_tool(
        path="/device/{mac}/events/delete",
        method="DELETE",
        operation_id="delete_device_events",
        summary="Delete Device Events",
        description="Delete all events associated with a device.",
        path_params=[{
            "name": "mac",
            "description": "Device MAC address",
            "schema": {"type": "string"}
        }],
        response_model=BaseResponse,
        tags=["devices"]
    )

    register_tool(
        path="/device/{mac}/reset-props",
        method="POST",
        operation_id="reset_device_props",
        summary="Reset Device Props",
        description="Reset custom properties of a device.",
        path_params=[{
            "name": "mac",
            "description": "Device MAC address",
            "schema": {"type": "string"}
        }],
        response_model=BaseResponse,
        tags=["devices"]
    )

    register_tool(
        path="/device/{mac}/set-alias",
        method="POST",
        operation_id="set_device_alias",
        summary="Set Device Alias",
        description="Set or update the display name/alias for a device.",
        path_params=[{
            "name": "mac",
            "description": "Device MAC address",
            "schema": {"type": "string"}
        }],
        request_model=SetDeviceAliasRequest,
        response_model=BaseResponse,
        tags=["devices"]
    )

    register_tool(
        path="/devices",
        method="GET",
        operation_id="get_all_devices",
        summary="Get All Devices",
        description="Retrieve a list of all devices in the system.",
        response_model=DeviceListResponse,
        tags=["devices"]
    )

    register_tool(
        path="/devices",
        method="DELETE",
        operation_id="delete_devices",
        summary="Delete Multiple Devices",
        description="Delete multiple devices by MAC address.",
        request_model=DeleteDevicesRequest,
        response_model=BaseResponse,
        tags=["devices"]
    )

    register_tool(
        path="/devices/empty-macs",
        method="DELETE",
        operation_id="delete_empty_mac_devices",
        summary="Delete Devices with Empty MACs",
        description="Delete all devices that do not have a valid MAC address.",
        response_model=BaseResponse,
        tags=["devices"]
    )

    register_tool(
        path="/devices/unknown",
        method="DELETE",
        operation_id="delete_unknown_devices",
        summary="Delete Unknown Devices",
        description="Delete devices marked as unknown.",
        response_model=BaseResponse,
        tags=["devices"]
    )

    register_tool(
        path="/devices/totals",
        method="GET",
        operation_id="get_device_totals",
        summary="Get Device Totals",
        description="Get device statistics including total count, online/offline counts, "
                    "new devices, and archived devices.",
        response_model=DeviceTotalsResponse,
        tags=["devices"]
    )

    register_tool(
        path="/devices/latest",
        method="GET",
        operation_id="get_latest_device",
        summary="Get Latest Device",
        description="Get information about the most recently seen/discovered device.",
        response_model=GetDeviceResponse,
        tags=["devices"]
    )

    register_tool(
        path="/devices/favorite",
        method="GET",
        operation_id="get_favorite_devices",
        summary="Get Favorite Devices",
        description="Get list of devices marked as favorites.",
        response_model=DeviceListResponse,
        tags=["devices"]
    )

    register_tool(
        path="/devices/export",
        method="GET",
        operation_id="export_devices",
        summary="Export Devices",
        description="Export all devices in CSV or JSON format. "
                    "Use 'format' query parameter (csv/json, defaults to csv).",
        query_params=[{
            "name": "format",
            "description": "Export format: csv or json",
            "required": False,
            "schema": {"type": "string", "enum": ["csv", "json"], "default": "csv"}
        }],
        response_model=DeviceExportResponse,
        tags=["devices"]
    )

    register_tool(
        path="/devices/import",
        method="POST",
        operation_id="import_devices",
        summary="Import Devices",
        description="Import devices from CSV or JSON content. "
                    "Content should be base64-encoded or sent as multipart file upload.",
        request_model=DeviceImportRequest,
        response_model=DeviceImportResponse,
        tags=["devices"]
    )

    register_tool(
        path="/devices/network/topology",
        method="GET",
        operation_id="get_network_topology",
        summary="Get Network Topology",
        description="Retrieve the network topology information showing device connections "
                    "and network structure.",
        response_model=NetworkTopologyResponse,
        tags=["devices"]
    )

    register_tool(
        path="/device/{mac}/update-column",
        method="POST",
        operation_id="update_device_column",
        summary="Update Device Column",
        description="Update a specific database column for a device. "
                    "Available columns include: devName, devType, devVendor, devNote, devGroup, etc.",
        path_params=[{
            "name": "mac",
            "description": "Device MAC address",
            "schema": {"type": "string"}
        }],
        request_model=UpdateDeviceColumnRequest,
        response_model=BaseResponse,
        tags=["devices"]
    )

    register_tool(
        path="/device/copy",
        method="POST",
        operation_id="copy_device",
        summary="Copy Device Settings",
        description="Copy settings and history from one device MAC address to another.",
        request_model=CopyDeviceRequest,
        response_model=BaseResponse,
        tags=["devices"]
    )

    # -------------------------------------------------------------------------
    # SETTINGS
    # -------------------------------------------------------------------------
    register_tool(
        path="/settings/{key}",
        method="GET",
        operation_id="get_setting",
        summary="Get Setting",
        description="Retrieve the value of a specific setting by key.",
        path_params=[{
            "name": "key",
            "description": "Setting key",
            "schema": {"type": "string"}
        }],
        response_model=GetSettingResponse,
        tags=["settings"]
    )

    # -------------------------------------------------------------------------
    # NETWORK TOOLS
    # -------------------------------------------------------------------------
    register_tool(
        path="/nettools/trigger-scan",
        method="POST",
        operation_id="trigger_network_scan",
        summary="Trigger Network Scan",
        description="Trigger a network scan to discover devices. "
                    "Specify scan type (ARPSCAN, NMAPDEV, NMAP) matching an enabled plugin.",
        request_model=TriggerScanRequest,
        response_model=TriggerScanResponse,
        tags=["nettools"]
    )

    register_tool(
        path="/device/open_ports",
        method="POST",
        operation_id="get_open_ports",
        summary="Get Open Ports",
        description="Retrieve open ports for a target IP or MAC address. "
                    "Returns cached NMAP scan results. Trigger a scan first if no data exists.",
        request_model=OpenPortsRequest,
        response_model=OpenPortsResponse,
        tags=["nettools"]
    )

    register_tool(
        path="/nettools/wakeonlan",
        method="POST",
        operation_id="wake_on_lan",
        summary="Wake-on-LAN",
        description="Send a Wake-on-LAN magic packet to wake up a device. "
                    "Provide either MAC address directly or IP (MAC will be resolved).",
        request_model=WakeOnLanRequest,
        response_model=WakeOnLanResponse,
        tags=["nettools"]
    )

    register_tool(
        path="/nettools/traceroute",
        method="POST",
        operation_id="perform_traceroute",
        summary="Traceroute",
        description="Perform a traceroute to a target IP address, showing network hops.",
        request_model=TracerouteRequest,
        response_model=TracerouteResponse,
        tags=["nettools"]
    )

    register_tool(
        path="/nettools/speedtest",
        method="GET",
        operation_id="run_speedtest",
        summary="Run Speedtest",
        description="Run an internet speed test.",
        response_model=BaseResponse,
        tags=["nettools"]
    )

    register_tool(
        path="/nettools/nslookup",
        method="POST",
        operation_id="run_nslookup",
        summary="NSLookup",
        description="Perform a DNS lookup for a given IP.",
        request_model=NslookupRequest,
        response_model=BaseResponse,
        tags=["nettools"]
    )

    register_tool(
        path="/nettools/nmap",
        method="POST",
        operation_id="run_nmap",
        summary="Run NMAP",
        description="Run an NMAP scan on a target.",
        request_model=NmapScanRequest,
        response_model=BaseResponse,
        tags=["nettools"]
    )

    register_tool(
        path="/nettools/internetinfo",
        method="GET",
        operation_id="get_internet_info",
        summary="Get Internet Info",
        description="Retrieve public internet connection information.",
        response_model=BaseResponse,
        tags=["nettools"]
    )

    register_tool(
        path="/nettools/interfaces",
        method="GET",
        operation_id="get_network_interfaces",
        summary="Get Network Interfaces",
        description="Retrieve information about network interfaces on the server.",
        response_model=BaseResponse,
        tags=["nettools"]
    )

    # -------------------------------------------------------------------------
    # EVENTS
    # -------------------------------------------------------------------------
    register_tool(
        path="/events/create/{mac}",
        method="POST",
        operation_id="create_device_event",
        summary="Create Event",
        description="Manually create an event for a device.",
        path_params=[{
            "name": "mac",
            "description": "Device MAC address",
            "schema": {"type": "string"}
        }],
        request_model=CreateEventRequest,
        response_model=BaseResponse,
        tags=["events"]
    )

    register_tool(
        path="/events/{mac}",
        method="DELETE",
        operation_id="delete_events_by_mac",
        summary="Delete Events by MAC",
        description="Delete all events for a specific device MAC address.",
        path_params=[{
            "name": "mac",
            "description": "Device MAC address",
            "schema": {"type": "string"}
        }],
        response_model=BaseResponse,
        tags=["events"]
    )

    register_tool(
        path="/events",
        method="DELETE",
        operation_id="delete_all_events",
        summary="Delete All Events",
        description="Delete all events in the system.",
        response_model=BaseResponse,
        tags=["events"]
    )

    register_tool(
        path="/events",
        method="GET",
        operation_id="get_all_events",
        summary="Get Events",
        description="Retrieve a list of events, optionally filtered by MAC.",
        query_params=[{
            "name": "mac",
            "description": "Filter by Device MAC",
            "required": False,
            "schema": {"type": "string"}
        }],
        response_model=BaseResponse,
        tags=["events"]
    )

    register_tool(
        path="/events/{days}",
        method="DELETE",
        operation_id="delete_old_events",
        summary="Delete Old Events",
        description="Delete events older than a specified number of days.",
        path_params=[{
            "name": "days",
            "description": "Number of days",
            "schema": {"type": "integer"}
        }],
        response_model=BaseResponse,
        tags=["events"]
    )

    register_tool(
        path="/events/recent",
        method="GET",
        operation_id="get_recent_events",
        summary="Get Recent Events",
        description="Get recent events/alerts from the system. "
                    "Defaults to last 24 hours. Use query params to adjust timeframe.",
        query_params=[{
            "name": "hours",
            "description": "Number of hours to look back",
            "required": False,
            "schema": {"type": "integer", "default": 24, "minimum": 1, "maximum": 720}
        }],
        response_model=RecentEventsResponse,
        tags=["events"]
    )

    register_tool(
        path="/events/last",
        method="GET",
        operation_id="get_last_events",
        summary="Get Last Events",
        description="Get the most recent 10 events logged in the system.",
        response_model=LastEventsResponse,
        tags=["events"]
    )

    register_tool(
        path="/sessions/totals",
        method="GET",
        operation_id="get_event_totals",
        summary="Get Event Totals",
        description="Get event and session totals over a specified period.",
        query_params=[{
            "name": "period",
            "description": "Time period (e.g., '7 days')",
            "required": False,
            "schema": {"type": "string", "default": "7 days"}
        }],
        response_model=BaseResponse,
        tags=["events"]
    )

    # -------------------------------------------------------------------------
    # SESSIONS
    # -------------------------------------------------------------------------
    register_tool(
        path="/sessions/create",
        method="POST",
        operation_id="create_session",
        summary="Create Session",
        description="Manually create a session record.",
        request_model=CreateSessionRequest,
        response_model=BaseResponse,
        tags=["sessions"]
    )

    register_tool(
        path="/sessions/delete",
        method="DELETE",
        operation_id="delete_session",
        summary="Delete Session",
        description="Delete sessions for a specific device.",
        request_model=DeleteSessionRequest,
        response_model=BaseResponse,
        tags=["sessions"]
    )

    register_tool(
        path="/sessions/list",
        method="GET",
        operation_id="list_sessions",
        summary="List Sessions",
        description="List sessions filtered by criteria.",
        query_params=[
            {"name": "mac", "required": False, "schema": {"type": "string"}},
            {"name": "start_date", "required": False, "schema": {"type": "string"}},
            {"name": "end_date", "required": False, "schema": {"type": "string"}}
        ],
        response_model=BaseResponse,
        tags=["sessions"]
    )

    register_tool(
        path="/sessions/calendar",
        method="GET",
        operation_id="get_sessions_calendar",
        summary="Get Sessions Calendar",
        description="Get sessions in a format suitable for calendar display.",
        query_params=[
            {"name": "start", "required": False, "schema": {"type": "string"}},
            {"name": "end", "required": False, "schema": {"type": "string"}},
            {"name": "mac", "required": False, "schema": {"type": "string"}}
        ],
        response_model=BaseResponse,
        tags=["sessions"]
    )

    register_tool(
        path="/sessions/{mac}",
        method="GET",
        operation_id="get_device_sessions",
        summary="Get Device Sessions",
        description="Get sessions for a specific device over a period.",
        path_params=[{
            "name": "mac",
            "description": "Device MAC address",
            "schema": {"type": "string"}
        }],
        query_params=[{
            "name": "period",
            "required": False,
            "schema": {"type": "string", "default": "1 day"}
        }],
        response_model=BaseResponse,
        tags=["sessions"]
    )

    register_tool(
        path="/sessions/session-events",
        method="GET",
        operation_id="get_session_events_summary",
        summary="Get Session Events Summary",
        description="Get a summary of session events.",
        query_params=[
            {"name": "type", "required": False, "schema": {"type": "string", "default": "all"}},
            {"name": "period", "required": False, "schema": {"type": "string", "default": "7 days"}}
        ],
        response_model=BaseResponse,
        tags=["sessions"]
    )

    # -------------------------------------------------------------------------
    # MESSAGING
    # -------------------------------------------------------------------------
    register_tool(
        path="/messaging/in-app/write",
        method="POST",
        operation_id="write_notification",
        summary="Write Notification",
        description="Create a new in-app notification.",
        request_model=CreateNotificationRequest,
        response_model=BaseResponse,
        tags=["messaging"]
    )

    register_tool(
        path="/messaging/in-app/unread",
        method="GET",
        operation_id="get_unread_notifications",
        summary="Get Unread Notifications",
        description="Retrieve all unread in-app notifications.",
        response_model=BaseResponse,  # Can refine to list model later
        tags=["messaging"]
    )

    register_tool(
        path="/messaging/in-app/read/all",
        method="POST",
        operation_id="mark_all_notifications_read",
        summary="Mark All Read",
        description="Mark all in-app notifications as read.",
        response_model=BaseResponse,
        tags=["messaging"]
    )

    register_tool(
        path="/messaging/in-app/delete",
        method="DELETE",
        operation_id="delete_all_notifications",
        summary="Delete All Notifications",
        description="Delete all in-app notifications.",
        response_model=BaseResponse,
        tags=["messaging"]
    )

    register_tool(
        path="/messaging/in-app/delete/{guid}",
        method="DELETE",
        operation_id="delete_notification",
        summary="Delete Notification",
        description="Delete a specific notification by GUID.",
        path_params=[{
            "name": "guid",
            "description": "Notification GUID",
            "schema": {"type": "string"}
        }],
        response_model=BaseResponse,
        tags=["messaging"]
    )

    register_tool(
        path="/messaging/in-app/read/{guid}",
        method="POST",
        operation_id="mark_notification_read",
        summary="Mark Notification Read",
        description="Mark a specific notification as read by GUID.",
        path_params=[{
            "name": "guid",
            "description": "Notification GUID",
            "schema": {"type": "string"}
        }],
        response_model=BaseResponse,
        tags=["messaging"]
    )

    # -------------------------------------------------------------------------
    # SYNC
    # -------------------------------------------------------------------------
    register_tool(
        path="/sync",
        method="GET",
        operation_id="sync_pull",
        summary="Sync Pull",
        description="Pull data for synchronization.",
        response_model=SyncPullResponse,
        tags=["sync"]
    )

    register_tool(
        path="/sync",
        method="POST",
        operation_id="sync_push",
        summary="Sync Push",
        description="Push data for synchronization.",
        request_model=SyncPushRequest,
        response_model=BaseResponse,
        tags=["sync"]
    )

    # -------------------------------------------------------------------------
    # HISTORY & LOGS & METRICS
    # -------------------------------------------------------------------------
    register_tool(
        path="/history",
        method="DELETE",
        operation_id="delete_online_history",
        summary="Delete Online History",
        description="Delete all online history records.",
        response_model=BaseResponse,
        tags=["logs"]
    )

    register_tool(
        path="/logs",
        method="DELETE",
        operation_id="clean_log",
        summary="Clean Log",
        description="Clean or truncate a specified log file.",
        query_params=[{
            "name": "file",
            "description": "Log file name",
            "required": True,
            "schema": {"type": "string"}
        }],
        response_model=BaseResponse,
        tags=["logs"]
    )

    register_tool(
        path="/logs/add-to-execution-queue",
        method="POST",
        operation_id="add_to_execution_queue",
        summary="Add to Execution Queue",
        description="Add an action to the system execution queue.",
        request_model=AddToQueueRequest,
        response_model=BaseResponse,
        tags=["logs"]
    )

    register_tool(
        path="/metrics",
        method="GET",
        operation_id="get_metrics",
        summary="Get Metrics",
        description="Get Prometheus-compatible metrics.",
        response_model=None,  # Returns plain text
        tags=["logs"]
    )

    # -------------------------------------------------------------------------
    # DB QUERY
    # -------------------------------------------------------------------------
    register_tool(
        path="/dbquery/read",
        method="POST",
        operation_id="db_read",
        summary="DB Read Query",
        description="Execute a raw SQL SELECT query.",
        request_model=DbQueryRequest,
        response_model=DbQueryResponse,
        tags=["dbquery"]
    )

    register_tool(
        path="/dbquery/write",
        method="POST",
        operation_id="db_write",
        summary="DB Write Query",
        description="Execute a raw SQL INSERT/UPDATE/DELETE query.",
        request_model=DbQueryRequest,
        response_model=BaseResponse,
        tags=["dbquery"]
    )

    register_tool(
        path="/dbquery/update",
        method="POST",
        operation_id="db_update",
        summary="DB Update",
        description="Update database records using structured parameters.",
        request_model=DbQueryUpdateRequest,
        response_model=BaseResponse,
        tags=["dbquery"]
    )

    register_tool(
        path="/dbquery/delete",
        method="POST",
        operation_id="db_delete",
        summary="DB Delete",
        description="Delete database records using structured parameters.",
        request_model=DbQueryDeleteRequest,
        response_model=BaseResponse,
        tags=["dbquery"]
    )


# Initialize registry on module load
try:
    _register_all_endpoints()
except Exception as e:
    # Log but don't crash import - allows for testing
    import sys
    print(f"Warning: Failed to register endpoints: {e}", file=sys.stderr)
