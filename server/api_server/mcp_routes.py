"""MCP bridge routes exposing NetAlertX tool endpoints via JSON-RPC."""

import json
import uuid
import queue
import requests
import threading
import logging
from flask import Blueprint, request, Response, stream_with_context, jsonify
from helper import get_setting_value

mcp_bp = Blueprint('mcp', __name__)

# Store active sessions: session_id -> Queue
sessions = {}
sessions_lock = threading.Lock()

# Cache for OpenAPI spec to avoid fetching on every request
openapi_spec_cache = None

BACKEND_PORT = get_setting_value("GRAPHQL_PORT")

API_BASE_URL = f"http://localhost:{BACKEND_PORT}/api/tools"


def get_openapi_spec():
    """Fetch and cache the tools OpenAPI specification from the local API server."""
    global openapi_spec_cache
    if openapi_spec_cache:
        return openapi_spec_cache

    try:
        # Fetch from local server
        # We use localhost because this code runs on the server
        response = requests.get(f"{API_BASE_URL}/openapi.json", timeout=10)
        response.raise_for_status()
        openapi_spec_cache = response.json()
        return openapi_spec_cache
    except Exception as e:
        print(f"Error fetching OpenAPI spec: {e}")
        return None


def map_openapi_to_mcp_tools(spec):
    """Convert OpenAPI paths into MCP tool descriptors."""
    tools = []
    if not spec or "paths" not in spec:
        return tools

    for path, methods in spec["paths"].items():
        for method, details in methods.items():
            if "operationId" in details:
                tool = {
                    "name": details["operationId"],
                    "description": details.get("description", details.get("summary", "")),
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }

                # Extract parameters from requestBody if present
                if "requestBody" in details:
                    content = details["requestBody"].get("content", {})
                    if "application/json" in content:
                        schema = content["application/json"].get("schema", {})
                        tool["inputSchema"] = schema.copy()
                        if "properties" not in tool["inputSchema"]:
                            tool["inputSchema"]["properties"] = {}
                        if "required" not in tool["inputSchema"]:
                            tool["inputSchema"]["required"] = []

                # Extract parameters from 'parameters' list (query/path params) - simplistic support
                if "parameters" in details:
                    for param in details["parameters"]:
                        if param.get("in") == "query":
                            tool["inputSchema"]["properties"][param["name"]] = {
                                "type": param.get("schema", {}).get("type", "string"),
                                "description": param.get("description", "")
                            }
                            if param.get("required"):
                                if "required" not in tool["inputSchema"]:
                                    tool["inputSchema"]["required"] = []
                                tool["inputSchema"]["required"].append(param["name"])

                tools.append(tool)
    return tools


def process_mcp_request(data):
    """Handle incoming MCP JSON-RPC requests and route them to tools."""
    method = data.get("method")
    msg_id = data.get("id")

    response = None

    if method == "initialize":
        response = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "NetAlertX",
                    "version": "1.0.0"
                }
            }
        }

    elif method == "notifications/initialized":
        # No response needed for notification
        pass

    elif method == "tools/list":
        spec = get_openapi_spec()
        tools = map_openapi_to_mcp_tools(spec)
        response = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "tools": tools
            }
        }

    elif method == "tools/call":
        params = data.get("params", {})
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})

        # Find the endpoint for this tool
        spec = get_openapi_spec()
        target_path = None
        target_method = None

        if spec and "paths" in spec:
            for path, methods in spec["paths"].items():
                for m, details in methods.items():
                    if details.get("operationId") == tool_name:
                        target_path = path
                        target_method = m.upper()
                        break
                if target_path:
                    break

        if target_path:
            try:
                # Make the request to the local API
                # We forward the Authorization header from the incoming request if present
                headers = {
                    "Content-Type": "application/json"
                }

                if "Authorization" in request.headers:
                    headers["Authorization"] = request.headers["Authorization"]

                url = f"{API_BASE_URL}{target_path}"

                if target_method == "POST":
                    api_res = requests.post(url, json=tool_args, headers=headers, timeout=30)
                elif target_method == "GET":
                    api_res = requests.get(url, params=tool_args, headers=headers, timeout=30)
                else:
                    api_res = None

                if api_res:
                    content = []
                    try:
                        json_content = api_res.json()
                        content.append({
                            "type": "text",
                            "text": json.dumps(json_content, indent=2)
                        })
                    except (ValueError, json.JSONDecodeError):
                        content.append({
                            "type": "text",
                            "text": api_res.text
                        })

                    is_error = api_res.status_code >= 400
                    response = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": content,
                            "isError": is_error
                        }
                    }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {"code": -32601, "message": f"Method {target_method} not supported"}
                    }

            except Exception as e:
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error calling tool: {str(e)}"}],
                        "isError": True
                    }
                }
        else:
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Tool {tool_name} not found"}
            }

    elif method == "ping":
        response = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {}
        }

    else:
        # Unknown method
        if msg_id:  # Only respond if it's a request (has id)
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": "Method not found"}
            }

    return response


@mcp_bp.route('/sse', methods=['GET', 'POST'])
def handle_sse():
    """Expose an SSE endpoint that streams MCP responses to connected clients."""
    if request.method == 'POST':
        # Handle verification or keep-alive pings
        try:
            data = request.get_json(silent=True)
            if data and "method" in data and "jsonrpc" in data:
                response = process_mcp_request(data)
                if response:
                    return jsonify(response)
                else:
                    # Notification or no response needed
                    return "", 202
        except Exception as e:
            # Log but don't fail - malformed requests shouldn't crash the endpoint
            logging.getLogger(__name__).debug(f"SSE POST processing error: {e}")

        return jsonify({"status": "ok", "message": "MCP SSE endpoint active"}), 200

    session_id = uuid.uuid4().hex
    q = queue.Queue()

    with sessions_lock:
        sessions[session_id] = q

    def stream():
        """Yield SSE messages for queued MCP responses until the client disconnects."""
        # Send the endpoint event
        # The client should POST to /api/mcp/messages?session_id=<session_id>
        yield f"event: endpoint\ndata: /api/mcp/messages?session_id={session_id}\n\n"

        try:
            while True:
                try:
                    # Wait for messages
                    message = q.get(timeout=20)  # Keep-alive timeout
                    yield f"event: message\ndata: {json.dumps(message)}\n\n"
                except queue.Empty:
                    # Send keep-alive comment
                    yield ": keep-alive\n\n"
        except GeneratorExit:
            with sessions_lock:
                if session_id in sessions:
                    del sessions[session_id]

    return Response(stream_with_context(stream()), mimetype='text/event-stream')


@mcp_bp.route('/messages', methods=['POST'])
def handle_messages():
    """Receive MCP JSON-RPC messages and enqueue responses for an SSE session."""
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400

    with sessions_lock:
        if session_id not in sessions:
            return jsonify({"error": "Session not found"}), 404
        q = sessions[session_id]

    data = request.json
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    response = process_mcp_request(data)

    if response:
        q.put(response)

    return jsonify({"status": "accepted"}), 202
