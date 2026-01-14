#!/usr/bin/env python
"""
NetAlertX MCP (Model Context Protocol) Server Endpoint

This module implements a standards-compliant MCP server that exposes NetAlertX API
endpoints as tools for AI assistants. It uses the registry-based OpenAPI spec generator
to ensure strict type safety and validation.

Key Features:
- JSON-RPC 2.0 over HTTP and Server-Sent Events (SSE)
- Dynamic tool mapping from OpenAPI registry
- Pydantic-based input validation
- Standard MCP capabilities (tools, resources, prompts)
- Session management with automatic cleanup

Architecture:
    ┌──────────────┐     ┌─────────────────┐     ┌─────────────────┐
    │  AI Client   │────▶│   MCP Server    │────▶│  Internal API   │
    │  (Claude)    │◀────│  (this module)  │◀────│  (Flask routes) │
    └──────────────┘     └─────────────────┘     └─────────────────┘
         SSE/JSON-RPC         Loopback HTTP
"""

from __future__ import annotations

import threading
import json
import uuid
import queue
import time
import os
from copy import deepcopy
from typing import Optional, Dict, Any, List
from urllib.parse import quote
from flask import Blueprint, request, jsonify, Response, stream_with_context
import requests
from pydantic import ValidationError

from helper import get_setting_value
from logger import mylog

# Import the spec generator (our source of truth)
from .spec_generator import generate_openapi_spec, get_registry, is_tool_disabled

# =============================================================================
# CONSTANTS & CONFIGURATION
# =============================================================================

MCP_PROTOCOL_VERSION = "2024-11-05"
MCP_SERVER_NAME = "NetAlertX"
MCP_SERVER_VERSION = "2.0.0"

# Session timeout in seconds (cleanup idle sessions)
SESSION_TIMEOUT = 300  # 5 minutes

# SSE keep-alive interval
SSE_KEEPALIVE_INTERVAL = 20  # seconds

# =============================================================================
# BLUEPRINTS
# =============================================================================

mcp_bp = Blueprint('mcp', __name__)
tools_bp = Blueprint('tools', __name__)

# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

# Thread-safe session storage
_mcp_sessions: Dict[str, Dict[str, Any]] = {}
_sessions_lock = threading.Lock()

# Background cleanup thread
_cleanup_thread: Optional[threading.Thread] = None
_cleanup_stop_event = threading.Event()
_cleanup_thread_lock = threading.Lock()


def _cleanup_sessions():
    """Background thread to clean up expired sessions."""
    while not _cleanup_stop_event.is_set():
        try:
            current_time = time.time()
            expired_sessions = []

            with _sessions_lock:
                for session_id, session_data in _mcp_sessions.items():
                    if current_time - session_data.get("last_activity", 0) > SESSION_TIMEOUT:
                        expired_sessions.append(session_id)

                for session_id in expired_sessions:
                    mylog("verbose", [f"[MCP] Cleaning up expired session: {session_id}"])
                    del _mcp_sessions[session_id]

        except Exception as e:
            mylog("none", [f"[MCP] Session cleanup error: {e}"])

        # Sleep in small increments to allow graceful shutdown
        for _ in range(60):  # Check every minute
            if _cleanup_stop_event.is_set():
                break
            time.sleep(1)


def _ensure_cleanup_thread():
    """Ensure the cleanup thread is running."""
    global _cleanup_thread
    if _cleanup_thread is None or not _cleanup_thread.is_alive():
        with _cleanup_thread_lock:
            if _cleanup_thread is None or not _cleanup_thread.is_alive():
                _cleanup_stop_event.clear()
                _cleanup_thread = threading.Thread(target=_cleanup_sessions, daemon=True)
                _cleanup_thread.start()


def create_session() -> str:
    """Create a new MCP session and return the session ID."""
    _ensure_cleanup_thread()

    session_id = uuid.uuid4().hex

    # Use configurable maxsize for message queue to prevent memory exhaustion
    # In production this could be loaded from settings
    try:
        raw_val = get_setting_value('MCP_QUEUE_MAXSIZE')
        queue_maxsize = int(str(raw_val).strip())
        # Clamp negative values to default
        if queue_maxsize < 0:
            queue_maxsize = 1000
    except (ValueError, TypeError):
        mylog("none", ["[MCP] Invalid MCP_QUEUE_MAXSIZE, defaulting to 1000"])
        queue_maxsize = 1000

    # queue.Queue(0) is unbounded, which corresponds to setting=0
    message_queue: queue.Queue = queue.Queue(maxsize=queue_maxsize)

    with _sessions_lock:
        _mcp_sessions[session_id] = {
            "queue": message_queue,
            "created_at": time.time(),
            "last_activity": time.time(),
            "initialized": False
        }

    mylog("verbose", [f"[MCP] Created session: {session_id}"])
    return session_id


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get a defensive copy of session data by ID, updating last activity."""
    with _sessions_lock:
        session = _mcp_sessions.get(session_id)
        if not session:
            return None

        session["last_activity"] = time.time()
        snapshot = deepcopy({k: v for k, v in session.items() if k != "queue"})
        snapshot["queue"] = session["queue"]
        return snapshot


def mark_session_initialized(session_id: str) -> None:
    """Mark a session as initialized while holding the session lock."""
    with _sessions_lock:
        session = _mcp_sessions.get(session_id)
        if session:
            session["initialized"] = True
            session["last_activity"] = time.time()


def delete_session(session_id: str) -> bool:
    """Delete a session by ID."""
    with _sessions_lock:
        if session_id in _mcp_sessions:
            del _mcp_sessions[session_id]
            mylog("verbose", [f"[MCP] Deleted session: {session_id}"])
            return True
    return False


# =============================================================================
# AUTHORIZATION
# =============================================================================

def check_auth() -> bool:
    """
    Check if the request has valid authorization.

    Returns:
        bool: True if the Authorization header matches the expected API token.
    """
    token = request.headers.get("Authorization")
    expected_token = f"Bearer {get_setting_value('API_TOKEN')}"
    return token == expected_token


# =============================================================================
# OPENAPI SPEC GENERATION
# =============================================================================

# Cached OpenAPI spec
_openapi_spec_cache: Optional[Dict[str, Any]] = None
_spec_cache_lock = threading.Lock()


def get_openapi_spec(force_refresh: bool = False, servers: Optional[List[Dict[str, str]]] = None, flask_app: Optional[Any] = None) -> Dict[str, Any]:
    """
    Get the OpenAPI specification, using cache when available.

    Args:
        force_refresh: If True, regenerate spec even if cached
        servers: Optional custom servers list
        flask_app: Optional Flask app for dynamic introspection

    Returns:
        OpenAPI specification dictionary
    """
    global _openapi_spec_cache

    with _spec_cache_lock:
        # If custom servers are provided, we always regenerate or at least update the cached one
        if servers:
            spec = generate_openapi_spec(servers=servers, flask_app=flask_app)
            # We don't necessarily want to cache a prefixed version as the "main" one
            # if multiple prefixes are used, so we just return it.
            return spec

        if _openapi_spec_cache is None or force_refresh:
            try:
                _openapi_spec_cache = generate_openapi_spec(flask_app=flask_app)
                mylog("verbose", ["[MCP] Generated OpenAPI spec from registry"])
            except Exception as e:
                mylog("none", [f"[MCP] Failed to generate OpenAPI spec: {e}"])
                # Return minimal valid spec on error
                return {
                    "openapi": "3.1.0",
                    "info": {"title": "NetAlertX", "version": "2.0.0"},
                    "paths": {}
                }

        return _openapi_spec_cache


def openapi_spec():
    """
    Flask route handler for OpenAPI spec endpoint.

    Returns:
        flask.Response: JSON response containing the OpenAPI spec.
    """
    from flask import current_app
    mylog("verbose", ["[MCP] OpenAPI spec requested"])

    # Detect base path from proxy headers
    # Nginx in this project often sets X-Forwarded-Prefix to /app
    prefix = request.headers.get('X-Forwarded-Prefix', '')

    # If the request came through a path like /mcp/sse/openapi.json,
    # and there's no prefix, we still use / as the root.
    # But if there IS a prefix, we should definitely use it.
    servers = None
    if prefix:
        servers = [{"url": prefix, "description": "Proxied server"}]

    spec = get_openapi_spec(servers=servers, flask_app=current_app)
    return jsonify(spec)


# =============================================================================
# MCP TOOL MAPPING
# =============================================================================

def map_openapi_to_mcp_tools(spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert OpenAPI specification into MCP tool definitions.

    This function transforms OpenAPI operations into MCP-compatible tool schemas,
    ensuring proper inputSchema derivation from request bodies and parameters.

    Args:
        spec: OpenAPI specification dictionary

    Returns:
        List of MCP tool definitions with name, description, and inputSchema
    """
    tools = []

    if not spec or "paths" not in spec:
        return tools

    for path, methods in spec["paths"].items():
        for method, details in methods.items():
            if "operationId" not in details:
                continue

            operation_id = details["operationId"]

            # Build inputSchema from requestBody and parameters
            input_schema = {
                "type": "object",
                "properties": {},
                "required": []
            }

            # Extract properties from requestBody (POST/PUT/PATCH)
            if "requestBody" in details:
                content = details["requestBody"].get("content", {})
                if "application/json" in content:
                    body_schema = content["application/json"].get("schema", {})

                    # Copy properties and required fields
                    if "properties" in body_schema:
                        input_schema["properties"].update(body_schema["properties"])
                    if "required" in body_schema:
                        input_schema["required"].extend(body_schema["required"])

                    # Handle $defs references (Pydantic nested models)
                    if "$defs" in body_schema:
                        input_schema["$defs"] = body_schema["$defs"]

            # Extract properties from parameters (path/query)
            for param in details.get("parameters", []):
                param_name = param["name"]
                param_schema = param.get("schema", {"type": "string"})

                input_schema["properties"][param_name] = {
                    "type": param_schema.get("type", "string"),
                    "description": param.get("description", "")
                }

                # Add enum if present
                if "enum" in param_schema:
                    input_schema["properties"][param_name]["enum"] = param_schema["enum"]

                # Add default if present
                if "default" in param_schema:
                    input_schema["properties"][param_name]["default"] = param_schema["default"]

                if param.get("required", False) and param_name not in input_schema["required"]:
                    input_schema["required"].append(param_name)

            if input_schema["required"]:
                input_schema["required"] = list(dict.fromkeys(input_schema["required"]))
            else:
                input_schema.pop("required", None)

            tool = {
                "name": operation_id,
                "description": details.get("description", details.get("summary", "")),
                "inputSchema": input_schema
            }

            tools.append(tool)

    return tools


def find_route_for_tool(tool_name: str) -> Optional[Dict[str, Any]]:
    """
    Find the registered route for a given tool name (operationId).

    Args:
        tool_name: The operationId to look up

    Returns:
        Route dictionary with path, method, and models, or None if not found
    """
    registry = get_registry()

    for entry in registry:
        if entry["operation_id"] == tool_name:
            return entry

    return None


# =============================================================================
# MCP REQUEST PROCESSING
# =============================================================================

def process_mcp_request(data: Dict[str, Any], session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Process an incoming MCP JSON-RPC request.

    Handles MCP protocol methods:
    - initialize: Protocol handshake
    - notifications/initialized: Initialization confirmation
    - tools/list: List available tools
    - tools/call: Execute a tool
    - resources/list: List available resources
    - prompts/list: List available prompts
    - ping: Keep-alive check

    Args:
        data: JSON-RPC request data
        session_id: Optional session identifier

    Returns:
        JSON-RPC response dictionary, or None for notifications
    """
    method = data.get("method")
    msg_id = data.get("id")
    params = data.get("params", {})

    mylog("debug", [f"[MCP] Processing request: method={method}, id={msg_id}"])

    # -------------------------------------------------------------------------
    # initialize - Protocol handshake
    # -------------------------------------------------------------------------
    if method == "initialize":
        # Mark session as initialized
        if session_id:
            mark_session_initialized(session_id)

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"subscribe": False, "listChanged": False},
                    "prompts": {"listChanged": False}
                },
                "serverInfo": {
                    "name": MCP_SERVER_NAME,
                    "version": MCP_SERVER_VERSION
                }
            }
        }

    # -------------------------------------------------------------------------
    # notifications/initialized - No response needed
    # -------------------------------------------------------------------------
    if method == "notifications/initialized":
        return None

    # -------------------------------------------------------------------------
    # tools/list - List available tools
    # -------------------------------------------------------------------------
    if method == "tools/list":
        from flask import current_app
        spec = get_openapi_spec(flask_app=current_app)
        tools = map_openapi_to_mcp_tools(spec)

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "tools": tools
            }
        }

    # -------------------------------------------------------------------------
    # tools/call - Execute a tool
    # -------------------------------------------------------------------------
    if method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})

        if not tool_name:
            return _error_response(msg_id, -32602, "Missing tool name")

        # Find the route for this tool
        route = find_route_for_tool(tool_name)
        if not route:
            return _error_response(msg_id, -32601, f"Tool '{tool_name}' not found")

        # Execute the tool via loopback HTTP call
        result = _execute_tool(route, tool_args)
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": result
        }

    # -------------------------------------------------------------------------
    # resources/list - List available resources
    # -------------------------------------------------------------------------
    if method == "resources/list":
        resources = _list_resources()
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "resources": resources
            }
        }

    # -------------------------------------------------------------------------
    # resources/read - Read a resource
    # -------------------------------------------------------------------------
    if method == "resources/read":
        uri = params.get("uri")
        if not uri:
            return _error_response(msg_id, -32602, "Missing resource URI")

        content = _read_resource(uri)
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "contents": content
            }
        }

    # -------------------------------------------------------------------------
    # prompts/list - List available prompts
    # -------------------------------------------------------------------------
    if method == "prompts/list":
        prompts = _list_prompts()
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "prompts": prompts
            }
        }

    # -------------------------------------------------------------------------
    # prompts/get - Get a specific prompt
    # -------------------------------------------------------------------------
    if method == "prompts/get":
        prompt_name = params.get("name")
        prompt_args = params.get("arguments", {})

        if not prompt_name:
            return _error_response(msg_id, -32602, "Missing prompt name")

        prompt_result = _get_prompt(prompt_name, prompt_args)
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": prompt_result
        }

    # -------------------------------------------------------------------------
    # ping - Keep-alive
    # -------------------------------------------------------------------------
    if method == "ping":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {}
        }

    # -------------------------------------------------------------------------
    # Unknown method
    # -------------------------------------------------------------------------
    if msg_id:
        return _error_response(msg_id, -32601, f"Method '{method}' not found")

    return None


def _error_response(msg_id: Any, code: int, message: str) -> Dict[str, Any]:
    """Create a JSON-RPC error response."""
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {
            "code": code,
            "message": message
        }
    }


def _execute_tool(route: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool by making a loopback HTTP call to the internal API.

    Args:
        route: Route definition from registry
        args: Tool arguments

    Returns:
        MCP tool result with content and isError flag
    """
    path_template = route["path"]
    path = path_template
    method = route["method"]

    # Substitute path parameters
    for key, value in args.items():
        placeholder = f"{{{key}}}"
        if placeholder in path:
            encoded_value = quote(str(value), safe="")
            path = path.replace(placeholder, encoded_value)

    # Check if tool is disabled
    if is_tool_disabled(route['operation_id']):
        return {
            "content": [{"type": "text", "text": f"Error: Tool '{route['operation_id']}' is disabled"}],
            "isError": True
        }

    # Build request
    api_base_url = f"http://localhost:{get_setting_value('GRAPHQL_PORT')}"
    url = f"{api_base_url}{path}"

    headers = {"Content-Type": "application/json"}
    if "Authorization" in request.headers:
        headers["Authorization"] = request.headers["Authorization"]

    filtered_body_args = {k: v for k, v in args.items() if f"{{{k}}}" not in route['path']}

    try:
        # Validate input if request model exists
        request_model = route.get("request_model")
        if request_model and method in ("POST", "PUT", "PATCH"):
            try:
                # Validate args against Pydantic model
                request_model(**filtered_body_args)
            except ValidationError as e:
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({
                            "success": False,
                            "error": "Validation error",
                            "details": e.errors()
                        }, indent=2)
                    }],
                    "isError": True
                }

        # Make the HTTP request
        if method == "POST":
            api_response = requests.post(url, json=filtered_body_args, headers=headers, timeout=60)
        elif method == "PUT":
            api_response = requests.put(url, json=filtered_body_args, headers=headers, timeout=60)
        elif method == "PATCH":
            api_response = requests.patch(url, json=filtered_body_args, headers=headers, timeout=60)
        elif method == "DELETE":
            api_response = requests.delete(url, headers=headers, timeout=60)
        else:  # GET
            # For GET, we also filter out keys already substituted into the path
            filtered_params = {k: v for k, v in args.items() if f"{{{k}}}" not in route['path']}
            api_response = requests.get(url, params=filtered_params, headers=headers, timeout=60)

        # Parse response
        content = []
        try:
            json_content = api_response.json()
            content.append({
                "type": "text",
                "text": json.dumps(json_content, indent=2)
            })
        except json.JSONDecodeError:
            content.append({
                "type": "text",
                "text": api_response.text
            })

        is_error = api_response.status_code >= 400

        return {
            "content": content,
            "isError": is_error
        }

    except requests.Timeout:
        return {
            "content": [{"type": "text", "text": "Request timed out"}],
            "isError": True
        }
    except Exception as e:
        mylog("none", [f"[MCP] Error executing tool {route['operation_id']}: {e}"])
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "isError": True
        }


# =============================================================================
# MCP RESOURCES
# =============================================================================

def _list_resources() -> List[Dict[str, Any]]:
    """List available MCP resources (read-only data like logs)."""
    resources = []

    # Log files
    log_dir = os.getenv("NETALERTX_LOG", "/tmp/log")
    log_files = [
        ("stdout.log", "Backend stdout log"),
        ("stderr.log", "Backend stderr log"),
        ("app_front.log", "Frontend commands log"),
        ("app.php_errors.log", "PHP errors log")
    ]

    for filename, description in log_files:
        log_path = os.path.join(log_dir, filename)
        if os.path.exists(log_path):
            resources.append({
                "uri": f"netalertx://logs/{filename}",
                "name": filename,
                "description": description,
                "mimeType": "text/plain"
            })

    # Plugin logs
    plugin_log_dir = os.path.join(log_dir, "plugins")
    if os.path.exists(plugin_log_dir):
        for filename in os.listdir(plugin_log_dir):
            if filename.endswith(".log"):
                resources.append({
                    "uri": f"netalertx://logs/plugins/{filename}",
                    "name": f"plugins/{filename}",
                    "description": f"Plugin log: {filename}",
                    "mimeType": "text/plain"
                })

    return resources


def _read_resource(uri: str) -> List[Dict[str, Any]]:
    """Read a resource by URI."""
    log_dir = os.getenv("NETALERTX_LOG", "/tmp/log")

    if uri.startswith("netalertx://logs/"):
        relative_path = uri.replace("netalertx://logs/", "")
        file_path = os.path.join(log_dir, relative_path)

        # Security: ensure path is within log directory
        real_path = os.path.realpath(file_path)
        if not real_path.startswith(os.path.realpath(log_dir)):
            return [{"uri": uri, "text": "Access denied: path outside log directory"}]

        if os.path.exists(file_path):
            try:
                # Read last 500 lines to avoid overwhelming context
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                    content = "".join(lines[-500:])
                    return [{"uri": uri, "mimeType": "text/plain", "text": content}]
            except Exception as e:
                return [{"uri": uri, "text": f"Error reading file: {e}"}]

        return [{"uri": uri, "text": "File not found"}]

    return [{"uri": uri, "text": "Unknown resource type"}]


# =============================================================================
# MCP PROMPTS
# =============================================================================

def _list_prompts() -> List[Dict[str, Any]]:
    """List available MCP prompts (curated interactions)."""
    return [
        {
            "name": "analyze_network_health",
            "description": "Analyze overall network health including device status, recent alerts, and connectivity issues",
            "arguments": []
        },
        {
            "name": "investigate_device",
            "description": "Investigate a specific device's status, history, and potential issues",
            "arguments": [
                {
                    "name": "device_identifier",
                    "description": "MAC address, IP, or device name to investigate",
                    "required": True
                }
            ]
        },
        {
            "name": "troubleshoot_connectivity",
            "description": "Help troubleshoot connectivity issues for a device",
            "arguments": [
                {
                    "name": "target_ip",
                    "description": "IP address experiencing connectivity issues",
                    "required": True
                }
            ]
        }
    ]


def _get_prompt(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Get a specific prompt with its content."""
    if name == "analyze_network_health":
        return {
            "description": "Network health analysis",
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": (
                            "Please analyze the network health by:\n"
                            "1. Getting device totals to see overall status\n"
                            "2. Checking recent events for any alerts\n"
                            "3. Looking at network topology for connectivity\n"
                            "Summarize findings and highlight any concerns."
                        )
                    }
                }
            ]
        }

    elif name == "investigate_device":
        device_id = args.get("device_identifier", "")
        return {
            "description": f"Investigation of device: {device_id}",
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": (
                            f"Please investigate the device '{device_id}' by:\n"
                            f"1. Search for the device to get its details\n"
                            f"2. Check any recent events for this device\n"
                            f"3. Check open ports if available\n"
                            "Provide a summary of the device's status and any notable findings."
                        )
                    }
                }
            ]
        }

    elif name == "troubleshoot_connectivity":
        target_ip = args.get("target_ip", "")
        return {
            "description": f"Connectivity troubleshooting for: {target_ip}",
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": (
                            f"Please help troubleshoot connectivity to '{target_ip}' by:\n"
                            f"1. Run a traceroute to identify network hops\n"
                            f"2. Search for the device by IP to get its info\n"
                            f"3. Check recent events for connection issues\n"
                            "Provide analysis of the network path and potential issues."
                        )
                    }
                }
            ]
        }

    return {
        "description": "Unknown prompt",
        "messages": []
    }


# =============================================================================
# FLASK ROUTE HANDLERS
# =============================================================================

def mcp_sse():
    """
    Handle MCP Server-Sent Events (SSE) endpoint.

    Supports both GET (establishing SSE stream) and POST (direct JSON-RPC).

    GET: Creates a new session and streams responses via SSE.
    POST: Processes JSON-RPC request directly and returns response.

    Returns:
        flask.Response: SSE stream for GET, JSON response for POST
    """
    if not check_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    # Handle POST (direct JSON-RPC, stateless)
    if request.method == "POST":
        try:
            data = request.get_json(silent=True)
            if data and "method" in data and "jsonrpc" in data:
                response = process_mcp_request(data)
                if response:
                    return jsonify(response)
                return "", 202
        except Exception as e:
            mylog("none", [f"[MCP] SSE POST processing error: {e}"])
            return jsonify(_error_response(None, -32603, str(e))), 500

        return jsonify({"status": "ok", "message": "MCP SSE endpoint active"}), 200

    # Handle GET (establish SSE stream)
    session_id = create_session()
    session = None
    for _ in range(3):
        session = get_session(session_id)
        if session:
            break
        time.sleep(0.05)

    if not session:
        delete_session(session_id)
        return jsonify({"success": False, "error": "Failed to initialize MCP session"}), 500

    message_queue = session["queue"]

    def stream():
        """Generator for SSE stream."""
        # Send endpoint event with session ID
        yield f"event: endpoint\ndata: /mcp/messages?session_id={session_id}\n\n"

        try:
            while True:
                try:
                    # Wait for messages with timeout
                    message = message_queue.get(timeout=SSE_KEEPALIVE_INTERVAL)
                    yield f"event: message\ndata: {json.dumps(message)}\n\n"
                except queue.Empty:
                    # Send keep-alive comment
                    yield ": keep-alive\n\n"

        except GeneratorExit:
            # Clean up session when client disconnects
            delete_session(session_id)

    return Response(
        stream_with_context(stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


def mcp_messages():
    """
    Handle MCP messages for a specific session via HTTP POST.

    Processes JSON-RPC requests and queues responses for SSE delivery.

    Returns:
        flask.Response: JSON response indicating acceptance or error
    """
    if not check_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400

    session = get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found or expired"}), 404

    message_queue: queue.Queue = session["queue"]

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    response = process_mcp_request(data, session_id)
    if response:
        try:
            # Handle bounded queue full
            message_queue.put(response, timeout=5)
        except queue.Full:
            mylog("none", [f"[MCP] Message queue full for session {session_id}. Dropping message."])
            return jsonify({"status": "error", "message": "Queue full"}), 503

    return jsonify({"status": "accepted"}), 202
