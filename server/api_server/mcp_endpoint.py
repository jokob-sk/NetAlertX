#!/usr/bin/env python
"""
NetAlertX MCP (Model Context Protocol) Server Endpoint.

This module implements an MCP server that exposes NetAlertX API endpoints as tools
for AI assistants. It provides JSON-RPC over HTTP and Server-Sent Events (SSE)
for tool discovery and execution.

The server maps OpenAPI specifications to MCP tools, allowing AIs to list available
tools and call them with appropriate parameters. Tools include device management,
network scanning, event querying, and more.
"""

import threading
from flask import Blueprint, request, jsonify, Response, stream_with_context
from helper import get_setting_value
from helper import mylog
# from .events_endpoint import get_events  # will import locally where needed
import requests
import json
import uuid
import queue

# Blueprints
mcp_bp = Blueprint('mcp', __name__)
tools_bp = Blueprint('tools', __name__)

# Global session management for MCP SSE connections
mcp_sessions = {}
mcp_sessions_lock = threading.Lock()


def check_auth():
    """
    Check if the request has valid authorization.

    Returns:
        bool: True if the Authorization header matches the expected API token, False otherwise.
    """
    token = request.headers.get("Authorization")
    expected_token = f"Bearer {get_setting_value('API_TOKEN')}"
    return token == expected_token


# --------------------------
# Specs
# --------------------------
def openapi_spec():
    """
    Generate the OpenAPI specification for NetAlertX tools.

    This function returns a JSON representation of the available API endpoints
    that are exposed as MCP tools, including paths, methods, and operation IDs.

    Returns:
        flask.Response: A JSON response containing the OpenAPI spec.
    """
    # Spec matching actual available routes for MCP tools
    mylog("verbose", ["[MCP] OpenAPI spec requested"])
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "NetAlertX Tools", "version": "1.1.0"},
        "servers": [{"url": "/"}],
        "paths": {
            "/devices/by-status": {
                "post": {
                    "operationId": "list_devices",
                    "description": "List devices filtered by their online/offline status. "
                                   "Accepts optional 'status' query parameter (online/offline)."
                }
            },
            "/device/{mac}": {
                "post": {
                    "operationId": "get_device_info",
                    "description": "Retrieve detailed information about a specific device by MAC address."
                }
            },
            "/devices/search": {
                "post": {
                    "operationId": "search_devices",
                    "description": "Search for devices based on various criteria like name, IP, etc. "
                                   "Accepts JSON with 'query' field."
                }
            },
            "/devices/latest": {
                "get": {
                    "operationId": "get_latest_device",
                    "description": "Get information about the most recently seen device."
                }
            },
            "/devices/favorite": {
                "get": {
                    "operationId": "get_favorite_devices",
                    "description": "Get favorite devices."
                }
            },
            "/nettools/trigger-scan": {
                "post": {
                    "operationId": "trigger_scan",
                    "description": "Trigger a network scan to discover new devices. "
                                   "Accepts optional 'type' parameter for scan type - needs to match an enabled plugin name (e.g., ARPSCAN, NMAPDEV, NMAP)."
                }
            },
            "/device/open_ports": {
                "post": {
                    "operationId": "get_open_ports",
                    "description": "Get a list of open ports for a specific device. "
                                   "Accepts JSON with 'target' (IP or MAC address). Trigger NMAP scan if no previous ports found with the /nettools/trigger-scan endpoint."
                }
            },
            "/devices/network/topology": {
                "get": {
                    "operationId": "get_network_topology",
                    "description": "Retrieve the network topology information."
                }
            },
            "/events/recent": {
                "get": {
                    "operationId": "get_recent_alerts",
                    "description": "Get recent events/alerts from the system. Defaults to last 24 hours."
                },
                "post": {"operationId": "get_recent_alerts"}
            },
            "/events/last": {
                "get": {
                    "operationId": "get_last_events",
                    "description": "Get the last 10 events logged in the system."
                },
                "post": {"operationId": "get_last_events"}
            },
            "/device/{mac}/set-alias": {
                "post": {
                    "operationId": "set_device_alias",
                    "description": "Set or update the alias/name for a device. Accepts JSON with 'alias' field."
                }
            },
            "/nettools/wakeonlan": {
                "post": {
                    "operationId": "wol_wake_device",
                    "description": "Send a Wake-on-LAN packet to wake up a device. "
                                   "Accepts JSON with 'devMac' or 'devLastIP'."
                }
            },
            "/devices/export": {
                "get": {
                    "operationId": "export_devices",
                    "description": "Export devices in CSV or JSON format. "
                                   "Accepts optional 'format' query parameter (csv/json, defaults to csv)."
                }
            },
            "/devices/import": {
                "post": {
                    "operationId": "import_devices",
                    "description": "Import devices from CSV or JSON content. "
                                   "Accepts JSON with 'content' field containing base64-encoded data, or multipart file upload."
                }
            },
            "/devices/totals": {
                "get": {
                    "operationId": "get_device_totals",
                    "description": "Get device statistics and counts."
                }
            },
            "/nettools/traceroute": {
                "post": {
                    "operationId": "traceroute",
                    "description": "Perform a traceroute to a target IP address. "
                                   "Accepts JSON with 'devLastIP' field."
                }
            }
        }
    }
    return jsonify(spec)


# --------------------------
# MCP SSE/JSON-RPC Endpoint
# --------------------------


# Sessions for SSE
_openapi_spec_cache = None  # Cached OpenAPI spec to avoid repeated generation
API_BASE_URL = f"http://localhost:{get_setting_value('GRAPHQL_PORT')}"  # Base URL for internal API calls


def get_openapi_spec():
    """
    Retrieve the cached OpenAPI specification for MCP tools.

    This function caches the OpenAPI spec to avoid repeated generation.
    If the cache is empty, it calls openapi_spec() to generate it.

    Returns:
        dict or None: The OpenAPI spec as a dictionary, or None if generation fails.
    """
    global _openapi_spec_cache

    if _openapi_spec_cache:
        return _openapi_spec_cache
    try:
        # Call the openapi_spec function directly instead of making HTTP request
        # to avoid circular requests and authorization issues
        response = openapi_spec()
        _openapi_spec_cache = response.get_json()
        return _openapi_spec_cache
    except Exception as e:
        mylog("none", [f"[MCP] Failed to fetch OpenAPI spec: {e}"])
        return None


def map_openapi_to_mcp_tools(spec):
    """
    Convert an OpenAPI specification into MCP tool definitions.

    Args:
        spec (dict): The OpenAPI spec dictionary.

    Returns:
        list: A list of MCP tool dictionaries, each containing name, description, and inputSchema.
    """
    tools = []
    if not spec or 'paths' not in spec:
        return tools
    for path, methods in spec['paths'].items():
        for method, details in methods.items():
            if 'operationId' in details:
                tool = {'name': details['operationId'], 'description': details.get('description', ''), 'inputSchema': {'type': 'object', 'properties': {}, 'required': []}}
                if 'requestBody' in details:
                    content = details['requestBody'].get('content', {})
                    if 'application/json' in content:
                        schema = content['application/json'].get('schema', {})
                        tool['inputSchema'] = schema.copy()
                if 'parameters' in details:
                    for param in details['parameters']:
                        if param.get('in') == 'query':
                            tool['inputSchema']['properties'][param['name']] = {'type': param.get('schema', {}).get('type', 'string'), 'description': param.get('description', '')}
                            if param.get('required'):
                                tool['inputSchema']['required'].append(param['name'])
                tools.append(tool)
    return tools


def process_mcp_request(data):
    """
    Process an incoming MCP JSON-RPC request.

    Handles various MCP methods like initialize, tools/list, tools/call, etc.
    For tools/call, it maps the tool name to an API endpoint and makes the call.

    Args:
        data (dict): The JSON-RPC request data containing method, id, params, etc.

    Returns:
        dict or None: The JSON-RPC response, or None for notifications.
    """
    method = data.get('method')
    msg_id = data.get('id')
    if method == 'initialize':
        return {'jsonrpc': '2.0', 'id': msg_id, 'result': {'protocolVersion': '2024-11-05', 'capabilities': {'tools': {}}, 'serverInfo': {'name': 'NetAlertX', 'version': '1.0.0'}}}
    if method == 'notifications/initialized':
        return None
    if method == 'tools/list':
        spec = get_openapi_spec()
        tools = map_openapi_to_mcp_tools(spec)
        return {'jsonrpc': '2.0', 'id': msg_id, 'result': {'tools': tools}}
    if method == 'tools/call':
        params = data.get('params', {})
        tool_name = params.get('name')
        tool_args = params.get('arguments', {})
        spec = get_openapi_spec()
        target_path = None
        target_method = None
        if spec and 'paths' in spec:
            for path, methods in spec['paths'].items():
                for m, details in methods.items():
                    if details.get('operationId') == tool_name:
                        target_path = path
                        target_method = m.upper()
                        break
                if target_path:
                    break
        if not target_path:
            return {'jsonrpc': '2.0', 'id': msg_id, 'error': {'code': -32601, 'message': f"Tool {tool_name} not found"}}
        try:
            headers = {'Content-Type': 'application/json'}
            if 'Authorization' in request.headers:
                headers['Authorization'] = request.headers['Authorization']
            url = f"{API_BASE_URL}{target_path}"
            if target_method == 'POST':
                api_res = requests.post(url, json=tool_args, headers=headers, timeout=30)
            else:
                api_res = requests.get(url, params=tool_args, headers=headers, timeout=30)
            content = []
            try:
                json_content = api_res.json()
                content.append({'type': 'text', 'text': json.dumps(json_content, indent=2)})
            except Exception as e:
                mylog("none", [f"[MCP] Failed to parse API response as JSON: {e}"])
                content.append({'type': 'text', 'text': api_res.text})
            is_error = api_res.status_code >= 400
            return {'jsonrpc': '2.0', 'id': msg_id, 'result': {'content': content, 'isError': is_error}}
        except Exception as e:
            mylog("none", [f"[MCP] Error calling tool {tool_name}: {e}"])
            return {'jsonrpc': '2.0', 'id': msg_id, 'result': {'content': [{'type': 'text', 'text': f"Error calling tool: {str(e)}"}], 'isError': True}}
    if method == 'ping':
        return {'jsonrpc': '2.0', 'id': msg_id, 'result': {}}
    if msg_id:
        return {'jsonrpc': '2.0', 'id': msg_id, 'error': {'code': -32601, 'message': 'Method not found'}}


def mcp_messages():
    """
    Handle MCP messages for a specific session via HTTP POST.

    This endpoint processes JSON-RPC requests for an existing MCP session.
    The session_id is passed as a query parameter.

    Returns:
        flask.Response: JSON response indicating acceptance or error.
    """
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400
    with mcp_sessions_lock:
        if session_id not in mcp_sessions:
            return jsonify({"error": "Session not found"}), 404
        q = mcp_sessions[session_id]
    data = request.json
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    response = process_mcp_request(data)
    if response:
        q.put(response)
    return jsonify({"status": "accepted"}), 202


def mcp_sse():
    """
    Handle MCP Server-Sent Events (SSE) endpoint.

    Supports both GET (for establishing SSE stream) and POST (for direct JSON-RPC).
    For GET, creates a new session and streams responses.
    For POST, processes the request directly and returns the response.

    Returns:
        flask.Response: SSE stream for GET, JSON response for POST.
    """
    if request.method == 'POST':
        try:
            data = request.get_json(silent=True)
            if data and 'method' in data and 'jsonrpc' in data:
                response = process_mcp_request(data)
                if response:
                    return jsonify(response)
                else:
                    return '', 202
        except Exception as e:
            mylog("none", [f"[MCP] SSE POST processing error: {e}"])
        return jsonify({'status': 'ok', 'message': 'MCP SSE endpoint active'}), 200

    session_id = uuid.uuid4().hex
    q = queue.Queue()
    with mcp_sessions_lock:
        mcp_sessions[session_id] = q

    def stream():
        yield f"event: endpoint\ndata: /mcp/messages?session_id={session_id}\n\n"
        try:
            while True:
                try:
                    message = q.get(timeout=20)
                    yield f"event: message\ndata: {json.dumps(message)}\n\n"
                except queue.Empty:
                    yield ": keep-alive\n\n"
        except GeneratorExit:
            with mcp_sessions_lock:
                if session_id in mcp_sessions:
                    del mcp_sessions[session_id]
    return Response(stream_with_context(stream()), mimetype='text/event-stream')
