#!/usr/bin/env python

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

mcp_sessions = {}
mcp_sessions_lock = threading.Lock()


def check_auth():
    token = request.headers.get("Authorization")
    expected_token = f"Bearer {get_setting_value('API_TOKEN')}"
    return token == expected_token


# --------------------------
# Specs
# --------------------------
def openapi_spec():
    # Spec matching actual available routes for MCP tools
    mylog("verbose", ["[MCP] OpenAPI spec requested"])
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "NetAlertX Tools", "version": "1.1.0"},
        "servers": [{"url": "/"}],
        "paths": {
            "/devices/by-status": {"post": {"operationId": "list_devices"}},
            "/device/{mac}": {"post": {"operationId": "get_device_info"}},
            "/devices/search": {"post": {"operationId": "search_devices"}},
            "/devices/latest": {"get": {"operationId": "get_latest_device"}},
            "/nettools/trigger-scan": {"post": {"operationId": "trigger_scan"}},
            "/device/open_ports": {"post": {"operationId": "get_open_ports"}},
            "/devices/network/topology": {"get": {"operationId": "get_network_topology"}},
            "/events/recent": {"get": {"operationId": "get_recent_alerts"}, "post": {"operationId": "get_recent_alerts"}},
            "/events/last": {"get": {"operationId": "get_last_events"}, "post": {"operationId": "get_last_events"}},
            "/device/{mac}/set-alias": {"post": {"operationId": "set_device_alias"}},
            "/nettools/wakeonlan": {"post": {"operationId": "wol_wake_device"}}
        }
    }
    return jsonify(spec)


# --------------------------
# MCP SSE/JSON-RPC Endpoint
# --------------------------


# Sessions for SSE
_sessions = {}
_sessions_lock = __import__('threading').Lock()
_openapi_spec_cache = None
API_BASE_URL = f"http://localhost:{get_setting_value('GRAPHQL_PORT')}"


def get_openapi_spec():
    global _openapi_spec_cache
    # Clear cache on each call for now to ensure fresh spec
    _openapi_spec_cache = None
    if _openapi_spec_cache:
        return _openapi_spec_cache
    try:
        r = requests.get(f"{API_BASE_URL}/mcp/openapi.json", timeout=10)
        r.raise_for_status()
        _openapi_spec_cache = r.json()
        return _openapi_spec_cache
    except Exception:
        return None


def map_openapi_to_mcp_tools(spec):
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
            except Exception:
                content.append({'type': 'text', 'text': api_res.text})
            is_error = api_res.status_code >= 400
            return {'jsonrpc': '2.0', 'id': msg_id, 'result': {'content': content, 'isError': is_error}}
        except Exception as e:
            return {'jsonrpc': '2.0', 'id': msg_id, 'result': {'content': [{'type': 'text', 'text': f"Error calling tool: {str(e)}"}], 'isError': True}}
    if method == 'ping':
        return {'jsonrpc': '2.0', 'id': msg_id, 'result': {}}
    if msg_id:
        return {'jsonrpc': '2.0', 'id': msg_id, 'error': {'code': -32601, 'message': 'Method not found'}}


def mcp_messages():
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
            mylog("none", f'SSE POST processing error: {e}')
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
