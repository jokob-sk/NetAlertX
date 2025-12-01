import threading
import sys
import os

from flask import Flask, request, jsonify, Response, stream_with_context
import json
import uuid
import queue
import requests
import logging
from datetime import datetime, timedelta
from models.device_instance import DeviceInstance  # noqa: E402
from flask_cors import CORS

# Register NetAlertX directories
INSTALL_PATH = os.getenv("NETALERTX_APP", "/app")
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from logger import mylog  # noqa: E402 [flake8 lint suppression]
from helper import get_setting_value  # noqa: E402 [flake8 lint suppression]
from db.db_helper import get_date_from_period  # noqa: E402 [flake8 lint suppression]
from app_state import updateState  # noqa: E402 [flake8 lint suppression]

from .graphql_endpoint import devicesSchema  # noqa: E402 [flake8 lint suppression]
from .device_endpoint import (  # noqa: E402 [flake8 lint suppression]
    get_device_data,
    set_device_data,
    delete_device,
    delete_device_events,
    reset_device_props,
    copy_device,
    update_device_column
)
from .devices_endpoint import (  # noqa: E402 [flake8 lint suppression]
    get_all_devices,
    delete_unknown_devices,
    delete_all_with_empty_macs,
    delete_devices,
    export_devices,
    import_csv,
    devices_totals,
    devices_by_status
)
from .events_endpoint import (  # noqa: E402 [flake8 lint suppression]
    delete_events,
    delete_events_older_than,
    get_events,
    create_event,
    get_events_totals
)
from .history_endpoint import delete_online_history  # noqa: E402 [flake8 lint suppression]
from .prometheus_endpoint import get_metric_stats  # noqa: E402 [flake8 lint suppression]
from .sessions_endpoint import (  # noqa: E402 [flake8 lint suppression]
    get_sessions,
    delete_session,
    create_session,
    get_sessions_calendar,
    get_device_sessions,
    get_session_events
)
from .nettools_endpoint import (  # noqa: E402 [flake8 lint suppression]
    wakeonlan,
    traceroute,
    speedtest,
    nslookup,
    nmap_scan,
    internet_info
)
from .dbquery_endpoint import read_query, write_query, update_query, delete_query  # noqa: E402 [flake8 lint suppression]
from .sync_endpoint import handle_sync_post, handle_sync_get  # noqa: E402 [flake8 lint suppression]
from .logs_endpoint import clean_log  # noqa: E402 [flake8 lint suppression]
from models.user_events_queue_instance import UserEventsQueueInstance  # noqa: E402 [flake8 lint suppression]
from database import DB  # noqa: E402 [flake8 lint suppression]
from models.plugin_object_instance import PluginObjectInstance  # noqa: E402 [flake8 lint suppression]
from plugin_helper import is_mac  # noqa: E402 [flake8 lint suppression]
from messaging.in_app import (  # noqa: E402 [flake8 lint suppression]
    write_notification,
    mark_all_notifications_read,
    delete_notifications,
    get_unread_notifications,
    delete_notification,
    mark_notification_as_read
)
from .tools_routes import openapi_spec as tools_openapi_spec  # noqa: E402 [flake8 lint suppression]
# tools and mcp routes have been moved into this module (api_server_start)

# Flask application
app = Flask(__name__)

# Register Blueprints
# No separate blueprints for tools or mcp - routes are registered below
CORS(
    app,
    resources={
        r"/metrics": {"origins": "*"},
        r"/device/*": {"origins": "*"},
        r"/devices/*": {"origins": "*"},
        r"/history/*": {"origins": "*"},
        r"/nettools/*": {"origins": "*"},
        r"/sessions/*": {"origins": "*"},
        r"/settings/*": {"origins": "*"},
        r"/dbquery/*": {"origins": "*"},
        r"/messaging/*": {"origins": "*"},
        r"/events/*": {"origins": "*"},
        r"/logs/*": {"origins": "*"},
        r"/api/tools/*": {"origins": "*"}
    },
    supports_credentials=True,
    allow_headers=["Authorization", "Content-Type"],
)

# -----------------------------------------------
# DB model instances for helper usage
# -----------------------------------------------
db_helper = DB()
db_helper.open()
device_handler = DeviceInstance(db_helper)
plugin_object_handler = PluginObjectInstance(db_helper)

# -------------------------------------------------------------------------------
# MCP bridge variables + helpers (moved from mcp_routes)
# -------------------------------------------------------------------------------
mcp_sessions = {}
mcp_sessions_lock = threading.Lock()
mcp_openapi_spec_cache = None

BACKEND_PORT = get_setting_value("GRAPHQL_PORT")
API_BASE_URL = f"http://localhost:{BACKEND_PORT}/api/tools"


def get_openapi_spec_local():
    global mcp_openapi_spec_cache
    if mcp_openapi_spec_cache:
        return mcp_openapi_spec_cache
    try:
        resp = requests.get(f"{API_BASE_URL}/openapi.json", timeout=10)
        resp.raise_for_status()
        mcp_openapi_spec_cache = resp.json()
        return mcp_openapi_spec_cache
    except Exception as e:
        mylog('minimal', [f"Error fetching OpenAPI spec: {e}"])
        return None


def map_openapi_to_mcp_tools(spec):
    tools = []
    if not spec or 'paths' not in spec:
        return tools
    for path, methods in spec['paths'].items():
        for method, details in methods.items():
            if 'operationId' in details:
                tool = {
                    'name': details['operationId'],
                    'description': details.get('description', details.get('summary', '')),
                    'inputSchema': {'type': 'object', 'properties': {}, 'required': []},
                }
                if 'requestBody' in details:
                    content = details['requestBody'].get('content', {})
                    if 'application/json' in content:
                        schema = content['application/json'].get('schema', {})
                        tool['inputSchema'] = schema.copy()
                        if 'properties' not in tool['inputSchema']:
                            tool['inputSchema']['properties'] = {}
                if 'parameters' in details:
                    for param in details['parameters']:
                        if param.get('in') == 'query':
                            tool['inputSchema']['properties'][param['name']] = {
                                'type': param.get('schema', {}).get('type', 'string'),
                                'description': param.get('description', ''),
                            }
                            if param.get('required'):
                                tool['inputSchema'].setdefault('required', []).append(param['name'])
                tools.append(tool)
    return tools


def process_mcp_request(data):
    method = data.get('method')
    msg_id = data.get('id')
    response = None
    if method == 'initialize':
        response = {
            'jsonrpc': '2.0',
            'id': msg_id,
            'result': {
                'protocolVersion': '2024-11-05',
                'capabilities': {'tools': {}},
                'serverInfo': {'name': 'NetAlertX', 'version': '1.0.0'},
            },
        }
    elif method == 'notifications/initialized':
        pass
    elif method == 'tools/list':
        spec = get_openapi_spec_local()
        tools = map_openapi_to_mcp_tools(spec)
        response = {'jsonrpc': '2.0', 'id': msg_id, 'result': {'tools': tools}}
    elif method == 'tools/call':
        params = data.get('params', {})
        tool_name = params.get('name')
        tool_args = params.get('arguments', {})
        spec = get_openapi_spec_local()
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
        if target_path:
            try:
                headers = {'Content-Type': 'application/json'}
                if 'Authorization' in request.headers:
                    headers['Authorization'] = request.headers['Authorization']
                url = f"{API_BASE_URL}{target_path}"
                if target_method == 'POST':
                    api_res = requests.post(url, json=tool_args, headers=headers, timeout=30)
                elif target_method == 'GET':
                    api_res = requests.get(url, params=tool_args, headers=headers, timeout=30)
                else:
                    api_res = None
                if api_res:
                    content = []
                    try:
                        json_content = api_res.json()
                        content.append({'type': 'text', 'text': json.dumps(json_content, indent=2)})
                    except Exception:
                        content.append({'type': 'text', 'text': api_res.text})
                    is_error = api_res.status_code >= 400
                    response = {'jsonrpc': '2.0', 'id': msg_id, 'result': {'content': content, 'isError': is_error}}
                else:
                    response = {'jsonrpc': '2.0', 'id': msg_id, 'error': {'code': -32601, 'message': f"Method {target_method} not supported"}}
            except Exception as e:
                response = {'jsonrpc': '2.0', 'id': msg_id, 'result': {'content': [{'type': 'text', 'text': f"Error calling tool: {str(e)}"}], 'isError': True}}
        else:
            response = {'jsonrpc': '2.0', 'id': msg_id, 'error': {'code': -32601, 'message': f"Tool {tool_name} not found"}}
    elif method == 'ping':
        response = {'jsonrpc': '2.0', 'id': msg_id, 'result': {}}
    else:
        if msg_id:
            response = {'jsonrpc': '2.0', 'id': msg_id, 'error': {'code': -32601, 'message': 'Method not found'}}
    return response


@app.route('/api/mcp/sse', methods=['GET', 'POST'])
def api_mcp_sse():
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
            logging.getLogger(__name__).debug(f'SSE POST processing error: {e}')
        return jsonify({'status': 'ok', 'message': 'MCP SSE endpoint active'}), 200

    session_id = uuid.uuid4().hex
    q = queue.Queue()
    with mcp_sessions_lock:
        mcp_sessions[session_id] = q

    def stream():
        yield f"event: endpoint\ndata: /api/mcp/messages?session_id={session_id}\n\n"
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


@app.route('/api/mcp/messages', methods=['POST'])
def api_mcp_messages():
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


# -------------------------------------------------------------------
# Custom handler for 404 - Route not found
# -------------------------------------------------------------------
@app.before_request
def log_request_info():
    """Log details of every incoming request."""
    # Filter out noisy requests if needed, but user asked for drastic logging
    mylog("verbose", [f"[HTTP] {request.method} {request.path} from {request.remote_addr}"])
    # Filter sensitive headers before logging
    safe_headers = {k: v for k, v in request.headers if k.lower() not in ('authorization', 'cookie', 'x-api-key')}
    mylog("debug", [f"[HTTP] Headers: {safe_headers}"])
    if request.method == "POST":
        # Be careful with large bodies, but log first 1000 chars
        data = request.get_data(as_text=True)
        mylog("debug", [f"[HTTP] Body length: {len(data)} chars"])


@app.errorhandler(404)
def not_found(error):
    response = {
        "success": False,
        "error": "API route not found",
        "message": f"The requested URL {error.description if hasattr(error, 'description') else ''} was not found on the server.",
    }
    return jsonify(response), 404

# --------------------------
# GraphQL Endpoints
# --------------------------


# Endpoint used when accessed via browser
@app.route("/graphql", methods=["GET"])
def graphql_debug():
    # Handles GET requests
    return "NetAlertX GraphQL server running."


# Endpoint for GraphQL queries
@app.route("/graphql", methods=["POST"])
def graphql_endpoint():
    # Check for API token in headers
    if not is_authorized():
        msg = '[graphql_server] Unauthorized access attempt - make sure your GRAPHQL_PORT and API_TOKEN settings are correct.'
        mylog('verbose', [msg])
        return jsonify({"success": False, "message": msg, "error": "Forbidden"}), 401

    # Retrieve and log request data
    data = request.get_json()
    mylog("verbose", [f"[graphql_server] data: {data}"])

    # Execute the GraphQL query
    result = devicesSchema.execute(data.get("query"), variables=data.get("variables"))

    # Initialize response
    response = {}

    if result.errors:
        response["errors"] = [str(e) for e in result.errors]
    if result.data:
        response["data"] = result.data

    return jsonify(response)


# --------------------------
# Tools endpoints (moved from tools_routes)
# --------------------------


@app.route('/api/tools/trigger_scan', methods=['POST'])
def api_trigger_scan():
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    scan_type = data.get('scan_type', 'nmap_fast')
    # Map requested scan type to plugin prefix
    plugin_prefix = None
    if scan_type in ['nmap_fast', 'nmap_deep']:
        plugin_prefix = 'NMAPDEV'
    elif scan_type == 'arp':
        plugin_prefix = 'ARPSCAN'
    else:
        return jsonify({"error": "Invalid scan_type. Must be 'arp', 'nmap_fast', or 'nmap_deep'"}), 400

    queue_instance = UserEventsQueueInstance()
    action = f"run|{plugin_prefix}"
    success, message = queue_instance.add_event(action)
    if success:
        return jsonify({"success": True, "message": f"Triggered plugin {plugin_prefix} via ad-hoc queue."})
    else:
        return jsonify({"success": False, "error": message}), 500


@app.route('/api/tools/list_devices', methods=['POST'])
def api_tools_list_devices():
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 401
    return get_all_devices()


@app.route('/api/tools/get_device_info', methods=['POST'])
def api_tools_get_device_info():
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    query = data.get('query')
    if not query:
        return jsonify({"error": "Missing 'query' parameter"}), 400
    # if MAC -> device endpoint
    if is_mac(query):
        return get_device_data(query)
    # search by name or IP
    matches = device_handler.search(query)
    if not matches:
        return jsonify({"message": "No devices found"}), 404
    return jsonify(matches)


@app.route('/api/tools/get_latest_device', methods=['POST'])
def api_tools_get_latest_device():
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 401
    latest = device_handler.getLatest()
    if not latest:
        return jsonify({"message": "No devices found"}), 404
    return jsonify([latest])


@app.route('/api/tools/get_open_ports', methods=['POST'])
def api_tools_get_open_ports():
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    target = data.get('target')
    if not target:
        return jsonify({"error": "Target is required"}), 400

    # If MAC is provided, use plugin objects to get port entries
    if is_mac(target):
        entries = plugin_object_handler.getByPrimary('NMAP', target.lower())
        open_ports = []
        for e in entries:
            try:
                port = int(e.get('Object_SecondaryID', 0))
            except (ValueError, TypeError):
                continue
            service = e.get('Watched_Value2', 'unknown')
            open_ports.append({"port": port, "service": service})
        return jsonify({"success": True, "target": target, "open_ports": open_ports, "raw": entries})

    # If IP provided, try to resolve to MAC and proceed
    # Use device handler to resolve IP
    device = device_handler.getByIP(target)
    if device and device.get('devMac'):
        mac = device.get('devMac')
        entries = plugin_object_handler.getByPrimary('NMAP', mac.lower())
        open_ports = []
        for e in entries:
            try:
                port = int(e.get('Object_SecondaryID', 0))
            except (ValueError, TypeError):
                continue
            service = e.get('Watched_Value2', 'unknown')
            open_ports.append({"port": port, "service": service})
        return jsonify({"success": True, "target": target, "open_ports": open_ports, "raw": entries})

    # No plugin data found; as fallback use nettools nmap_scan (may run subprocess)
    # Note: Prefer plugin data (NMAP) when available
    res = nmap_scan(target, 'fast')
    return res


@app.route('/api/tools/get_network_topology', methods=['GET'])
def api_tools_get_network_topology():
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 401
    topo = device_handler.getNetworkTopology()
    return jsonify(topo)


@app.route('/api/tools/get_recent_alerts', methods=['POST'])
def api_tools_get_recent_alerts():
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    hours = int(data.get('hours', 24))
    # Reuse get_events() - which returns a Flask response with JSON containing 'events'
    res = get_events()
    events_json = res.get_json() if hasattr(res, 'get_json') else None
    events = events_json.get('events', []) if events_json else []
    cutoff = datetime.now() - timedelta(hours=hours)
    filtered = [e for e in events if 'eve_DateTime' in e and datetime.strptime(e['eve_DateTime'], '%Y-%m-%d %H:%M:%S') > cutoff]
    return jsonify(filtered)


@app.route('/api/tools/set_device_alias', methods=['POST'])
def api_tools_set_device_alias():
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    mac = data.get('mac')
    alias = data.get('alias')
    if not mac or not alias:
        return jsonify({"error": "MAC and Alias are required"}), 400
    return update_device_column(mac, 'devName', alias)


@app.route('/api/tools/wol_wake_device', methods=['POST'])
def api_tools_wol_wake_device():
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    mac = data.get('mac')
    ip = data.get('ip')
    if not mac and not ip:
        return jsonify({"error": "MAC or IP is required"}), 400
    # Resolve IP to MAC if needed
    if not mac and ip:
        device = device_handler.getByIP(ip)
        if not device or not device.get('devMac'):
            return jsonify({"error": f"Could not resolve MAC for IP {ip}"}), 404
        mac = device.get('devMac')
    # Validate mac using is_mac helper
    if not is_mac(mac):
        return jsonify({"success": False, "error": f"Invalid MAC: {mac}"}), 400
    return wakeonlan(mac)


@app.route('/api/tools/openapi.json', methods=['GET'])
def api_tools_openapi_spec():
    # Minimal OpenAPI spec for tools
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "NetAlertX Tools", "version": "1.1.0"},
        "servers": [{"url": "/api/tools"}],
        "paths": {}
    }
    return jsonify(spec)


# --------------------------
# Settings Endpoints
# --------------------------


@app.route("/settings/<setKey>", methods=["GET"])
def api_get_setting(setKey):
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    value = get_setting_value(setKey)
    return jsonify({"success": True, "value": value})


# --------------------------
# Device Endpoints
# --------------------------


@app.route("/device/<mac>", methods=["GET"])
def api_get_device(mac):
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    return get_device_data(mac)


@app.route("/device/<mac>", methods=["POST"])
def api_set_device(mac):
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    return set_device_data(mac, request.json)


@app.route("/device/<mac>/delete", methods=["DELETE"])
def api_delete_device(mac):
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    return delete_device(mac)


@app.route("/device/<mac>/events/delete", methods=["DELETE"])
def api_delete_device_events(mac):
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    return delete_device_events(mac)


@app.route("/device/<mac>/reset-props", methods=["POST"])
def api_reset_device_props(mac):
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    return reset_device_props(mac, request.json)


@app.route("/device/copy", methods=["POST"])
def api_copy_device():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    data = request.get_json() or {}
    mac_from = data.get("macFrom")
    mac_to = data.get("macTo")

    if not mac_from or not mac_to:
        return jsonify({"success": False, "message": "ERROR: Missing parameters", "error": "macFrom and macTo are required"}), 400

    return copy_device(mac_from, mac_to)


@app.route("/device/<mac>/update-column", methods=["POST"])
def api_update_device_column(mac):
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    data = request.get_json() or {}
    column_name = data.get("columnName")
    column_value = data.get("columnValue")

    if not column_name or not column_value:
        return jsonify({"success": False, "message": "ERROR: Missing parameters", "error": "columnName and columnValue are required"}), 400

    return update_device_column(mac, column_name, column_value)


# --------------------------
# Devices Collections
# --------------------------


@app.route("/devices", methods=["GET"])
def api_get_devices():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    return get_all_devices()


@app.route("/devices", methods=["DELETE"])
def api_delete_devices():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    macs = request.json.get("macs") if request.is_json else None

    return delete_devices(macs)


@app.route("/devices/empty-macs", methods=["DELETE"])
def api_delete_all_empty_macs():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    return delete_all_with_empty_macs()


@app.route("/devices/unknown", methods=["DELETE"])
def api_delete_unknown_devices():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    return delete_unknown_devices()


@app.route("/devices/export", methods=["GET"])
@app.route("/devices/export/<format>", methods=["GET"])
def api_export_devices(format=None):
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    export_format = (format or request.args.get("format", "csv")).lower()
    return export_devices(export_format)


@app.route("/devices/import", methods=["POST"])
def api_import_csv():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    return import_csv(request.files.get("file"))


@app.route("/devices/totals", methods=["GET"])
def api_devices_totals():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    return devices_totals()


@app.route("/devices/by-status", methods=["GET"])
def api_devices_by_status():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    status = request.args.get("status", "") if request.args else None

    return devices_by_status(status)


# --------------------------
# Net tools
# --------------------------
@app.route("/nettools/wakeonlan", methods=["POST"])
def api_wakeonlan():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    mac = request.json.get("devMac")
    return wakeonlan(mac)


@app.route("/nettools/traceroute", methods=["POST"])
def api_traceroute():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    ip = request.json.get("devLastIP")
    return traceroute(ip)


@app.route("/nettools/speedtest", methods=["GET"])
def api_speedtest():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    return speedtest()


@app.route("/nettools/nslookup", methods=["POST"])
def api_nslookup():
    """
    API endpoint to handle nslookup requests.
    Expects JSON with 'devLastIP'.
    """
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    data = request.get_json(silent=True)
    if not data or "devLastIP" not in data:
        return jsonify({"success": False, "message": "ERROR: Missing parameters", "error": "Missing 'devLastIP'"}), 400

    ip = data["devLastIP"]
    return nslookup(ip)


@app.route("/nettools/nmap", methods=["POST"])
def api_nmap():
    """
    API endpoint to handle nmap scan requests.
    Expects JSON with 'scan' (IP address) and 'mode' (scan mode).
    """
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    data = request.get_json(silent=True)
    if not data or "scan" not in data or "mode" not in data:
        return jsonify({"success": False, "message": "ERROR: Missing parameters", "error": "Missing 'scan' or 'mode'"}), 400

    ip = data["scan"]
    mode = data["mode"]
    return nmap_scan(ip, mode)


@app.route("/nettools/internetinfo", methods=["GET"])
def api_internet_info():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    return internet_info()


# --------------------------
# DB query
# --------------------------


@app.route("/dbquery/read", methods=["POST"])
def dbquery_read():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    data = request.get_json() or {}
    raw_sql_b64 = data.get("rawSql")

    if not raw_sql_b64:
        return jsonify({"success": False, "message": "ERROR: Missing parameters", "error": "rawSql is required"}), 400

    return read_query(raw_sql_b64)


@app.route("/dbquery/write", methods=["POST"])
def dbquery_write():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    data = request.get_json() or {}
    raw_sql_b64 = data.get("rawSql")
    if not raw_sql_b64:
        return jsonify({"success": False, "message": "ERROR: Missing parameters", "error": "rawSql is required"}), 400

    return write_query(raw_sql_b64)


@app.route("/dbquery/update", methods=["POST"])
def dbquery_update():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    data = request.get_json() or {}
    required = ["columnName", "id", "dbtable", "columns", "values"]
    if not all(data.get(k) for k in required):
        return jsonify(
            {
                "success": False,
                "message": "ERROR: Missing parameters",
                "error": "Missing required 'columnName', 'id', 'dbtable', 'columns', or 'values' query parameter"
            }
        ), 400

    return update_query(
        column_name=data["columnName"],
        ids=data["id"],
        dbtable=data["dbtable"],
        columns=data["columns"],
        values=data["values"],
    )


@app.route("/dbquery/delete", methods=["POST"])
def dbquery_delete():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    data = request.get_json() or {}
    required = ["columnName", "id", "dbtable"]
    if not all(data.get(k) for k in required):
        return jsonify({"success": False, "message": "ERROR: Missing parameters", "error": "Missing required 'columnName', 'id', or 'dbtable' query parameter"}), 400

    return delete_query(
        column_name=data["columnName"],
        ids=data["id"],
        dbtable=data["dbtable"],
    )


# --------------------------
# Online history
# --------------------------


@app.route("/history", methods=["DELETE"])
def api_delete_online_history():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    return delete_online_history()


# --------------------------
# Logs
# --------------------------

@app.route("/logs", methods=["DELETE"])
def api_clean_log():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    file = request.args.get("file")
    if not file:
        return jsonify({"success": False, "message": "ERROR: Missing parameters", "error": "Missing 'file' query parameter"}), 400

    return clean_log(file)


@app.route("/logs/add-to-execution-queue", methods=["POST"])
def api_add_to_execution_queue():

    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    queue = UserEventsQueueInstance()

    # Get JSON payload safely
    data = request.get_json(silent=True) or {}
    action = data.get("action")

    if not action:
        return jsonify({
            "success": False, "message": "ERROR: Missing parameters", "error": "Missing required 'action' field in JSON body"}), 400

    success, message = queue.add_event(action)
    status_code = 200 if success else 400

    response = {"success": success, "message": message}
    if not success:
        response["error"] = "ERROR"

    return jsonify(response), status_code


# --------------------------
# Device Events
# --------------------------


@app.route("/events/create/<mac>", methods=["POST"])
def api_create_event(mac):
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    data = request.json or {}
    ip = data.get("ip", "0.0.0.0")
    event_type = data.get("event_type", "Device Down")
    additional_info = data.get("additional_info", "")
    pending_alert = data.get("pending_alert", 1)
    event_time = data.get("event_time", None)

    # Call the helper to insert into DB
    create_event(mac, ip, event_type, additional_info, pending_alert, event_time)

    # Return consistent JSON response
    return jsonify({"success": True, "message": f"Event created for {mac}"})


@app.route("/events/<mac>", methods=["DELETE"])
def api_events_by_mac(mac):
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    return delete_device_events(mac)


@app.route("/events", methods=["DELETE"])
def api_delete_all_events():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    return delete_events()


@app.route("/events", methods=["GET"])
def api_get_events():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    mac = request.args.get("mac")
    return get_events(mac)


@app.route("/events/<int:days>", methods=["DELETE"])
def api_delete_old_events(days: int):
    """
    Delete events older than <days> days.
    Example: DELETE /events/30
    """
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    return delete_events_older_than(days)


@app.route("/sessions/totals", methods=["GET"])
def api_get_events_totals():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    period = get_date_from_period(request.args.get("period", "7 days"))
    return get_events_totals(period)


# --------------------------
# Sessions
# --------------------------


@app.route("/sessions/create", methods=["POST"])
def api_create_session():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    data = request.json
    mac = data.get("mac")
    ip = data.get("ip")
    start_time = data.get("start_time")
    end_time = data.get("end_time")
    event_type_conn = data.get("event_type_conn", "Connected")
    event_type_disc = data.get("event_type_disc", "Disconnected")

    if not mac or not ip or not start_time:
        return jsonify({"success": False, "message": "ERROR: Missing parameters", "error": "Missing required 'mac', 'ip', or 'start_time' query parameter"}), 400

    return create_session(
        mac, ip, start_time, end_time, event_type_conn, event_type_disc
    )


@app.route("/sessions/delete", methods=["DELETE"])
def api_delete_session():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    mac = request.json.get("mac") if request.is_json else None
    if not mac:
        return jsonify({"success": False, "message": "ERROR: Missing parameters", "error": "Missing 'mac' query parameter"}), 400

    return delete_session(mac)


@app.route("/sessions/list", methods=["GET"])
def api_get_sessions():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    mac = request.args.get("mac")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    return get_sessions(mac, start_date, end_date)


@app.route("/sessions/calendar", methods=["GET"])
def api_get_sessions_calendar():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    # Query params: /sessions/calendar?start=2025-08-01&end=2025-08-21
    start_date = request.args.get("start")
    end_date = request.args.get("end")

    return get_sessions_calendar(start_date, end_date)


@app.route("/sessions/<mac>", methods=["GET"])
def api_device_sessions(mac):
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    period = request.args.get("period", "1 day")
    return get_device_sessions(mac, period)


@app.route("/sessions/session-events", methods=["GET"])
def api_get_session_events():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    session_event_type = request.args.get("type", "all")
    period = get_date_from_period(request.args.get("period", "7 days"))
    return get_session_events(session_event_type, period)


# --------------------------
# Prometheus metrics endpoint
# --------------------------
@app.route("/metrics")
def metrics():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    # Return Prometheus metrics as plain text
    return Response(get_metric_stats(), mimetype="text/plain")


# --------------------------
# In-app notifications
# --------------------------
@app.route("/messaging/in-app/write", methods=["POST"])
def api_write_notification():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    data = request.json or {}
    content = data.get("content")
    level = data.get("level", "alert")

    if not content:
        return jsonify({"success": False, "message": "ERROR: Missing parameters", "error": "Missing content"}), 400

    write_notification(content, level)
    return jsonify({"success": True})


@app.route("/messaging/in-app/unread", methods=["GET"])
def api_get_unread_notifications():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    return get_unread_notifications()


@app.route("/messaging/in-app/read/all", methods=["POST"])
def api_mark_all_notifications_read():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    return jsonify(mark_all_notifications_read())


@app.route("/messaging/in-app/delete", methods=["DELETE"])
def api_delete_all_notifications():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    return delete_notifications()


@app.route("/messaging/in-app/delete/<guid>", methods=["DELETE"])
def api_delete_notification(guid):
    """Delete a single notification by GUID."""
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    result = delete_notification(guid)
    if result.get("success"):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "ERROR", "error": result.get("error")}), 500


@app.route("/messaging/in-app/read/<guid>", methods=["POST"])
def api_mark_notification_read(guid):
    """Mark a single notification as read by GUID."""
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    result = mark_notification_as_read(guid)
    if result.get("success"):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "ERROR", "error": result.get("error")}), 500


# --------------------------
# SYNC endpoint
# --------------------------
@app.route("/sync", methods=["GET", "POST"])
def sync_endpoint():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    if request.method == "GET":
        return handle_sync_get()
    elif request.method == "POST":
        return handle_sync_post()
    else:
        msg = "[sync endpoint] Method Not Allowed"
        write_notification(msg, "alert")
        mylog("verbose", [msg])
        return jsonify({"success": False, "message": "ERROR: No allowed", "error": "Method Not Allowed"}), 405


# --------------------------
# Background Server Start
# --------------------------
def is_authorized():
    token = request.headers.get("Authorization")
    is_authorized = token == f"Bearer {get_setting_value('API_TOKEN')}"

    if not is_authorized:
        msg = "[api] Unauthorized access attempt - make sure your GRAPHQL_PORT and API_TOKEN settings are correct."
        write_notification(msg, "alert")
        mylog("verbose", [msg])

    return is_authorized


def start_server(graphql_port, app_state):
    """Start the GraphQL server in a background thread."""

    if app_state.graphQLServerStarted == 0:
        mylog("verbose", [f"[graphql endpoint] Starting on port: {graphql_port}"])

        # Start Flask app in a separate thread
        thread = threading.Thread(
            target=lambda: app.run(
                host="0.0.0.0", port=graphql_port, debug=True, use_reloader=False
            )
        )
        thread.start()

        # Update the state to indicate the server has started
        app_state = updateState("Process: Idle", None, None, None, 1)


if __name__ == "__main__":
    # This block is for running the server directly for testing purposes
    # In production, start_server is called from api.py
    pass
