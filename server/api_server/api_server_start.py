import threading
import sys
import os

from flask import Flask, request, jsonify, Response
import requests
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

from models.event_instance import EventInstance  # noqa: E402 [flake8 lint suppression]
# Import tool logic from the MCP/tools module to reuse behavior (no blueprints)
from plugin_helper import is_mac  # noqa: E402 [flake8 lint suppression]
# is_mac is provided in mcp_endpoint and used by those handlers
# mcp_endpoint contains helper functions; routes moved into this module to keep a single place for routes
from messaging.in_app import (  # noqa: E402 [flake8 lint suppression]
    write_notification,
    mark_all_notifications_read,
    delete_notifications,
    get_unread_notifications,
    delete_notification,
    mark_notification_as_read
)
from .mcp_endpoint import (  # noqa: E402 [flake8 lint suppression]
    mcp_sse,
    mcp_messages,
    openapi_spec
)
# tools and mcp routes have been moved into this module (api_server_start)

# Flask application
app = Flask(__name__)


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
        r"/api/tools/*": {"origins": "*"},
        r"/auth/*": {"origins": "*"},
        r"/mcp/*": {"origins": "*"}
    },
    supports_credentials=True,
    allow_headers=["Authorization", "Content-Type"],
)

# -------------------------------------------------------------------------------
# MCP bridge variables + helpers (moved from mcp_routes)
# -------------------------------------------------------------------------------

mcp_openapi_spec_cache = None

BACKEND_PORT = get_setting_value("GRAPHQL_PORT")
API_BASE_URL = f"http://localhost:{BACKEND_PORT}"


def get_openapi_spec_local():
    global mcp_openapi_spec_cache
    if mcp_openapi_spec_cache:
        return mcp_openapi_spec_cache
    try:
        resp = requests.get(f"{API_BASE_URL}/mcp/openapi.json", timeout=10)
        resp.raise_for_status()
        mcp_openapi_spec_cache = resp.json()
        return mcp_openapi_spec_cache
    except Exception as e:
        mylog('minimal', [f"Error fetching OpenAPI spec: {e}"])
        return None


@app.route('/mcp/sse', methods=['GET', 'POST'])
def api_mcp_sse():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    return mcp_sse()


@app.route('/api/mcp/messages', methods=['POST'])
def api_mcp_messages():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    return mcp_messages()


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
    # Get the requested path from the request object instead of error.description
    requested_url = request.path if request else "unknown"
    response = {
        "success": False,
        "error": "API route not found",
        "message": f"The requested URL {requested_url} was not found on the server.",
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


# Tools endpoints are registered via `mcp_endpoint.tools_bp` blueprint.


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
@app.route('/mcp/sse/device/<mac>', methods=['GET', 'POST'])
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


@app.route('/mcp/sse/device/<mac>/set-alias', methods=['POST'])
@app.route('/device/<mac>/set-alias', methods=['POST'])
def api_device_set_alias(mac):
    """Set the device alias - convenience wrapper around update_device_column."""
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    data = request.get_json() or {}
    alias = data.get('alias')
    if not alias:
        return jsonify({"success": False, "message": "ERROR: Missing parameters", "error": "alias is required"}), 400
    return update_device_column(mac, 'devName', alias)


@app.route('/mcp/sse/device/open_ports', methods=['POST'])
@app.route('/device/open_ports', methods=['POST'])
def api_device_open_ports():
    """Get stored NMAP open ports for a target IP or MAC."""
    if not is_authorized():
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    target = data.get('target')
    if not target:
        return jsonify({"success": False, "error": "Target (IP or MAC) is required"}), 400

    device_handler = DeviceInstance()

    # Use DeviceInstance method to get stored open ports
    open_ports = device_handler.getOpenPorts(target)

    if not open_ports:
        return jsonify({"success": False, "error": f"No stored open ports for {target}. Run a scan with `/nettools/trigger-scan`"}), 404

    return jsonify({"success": True, "target": target, "open_ports": open_ports})


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


@app.route('/mcp/sse/devices/by-status', methods=['GET', 'POST'])
@app.route("/devices/by-status", methods=["GET"])
def api_devices_by_status():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    status = request.args.get("status", "") if request.args else None

    return devices_by_status(status)


@app.route('/mcp/sse/devices/search', methods=['POST'])
@app.route('/devices/search', methods=['POST'])
def api_devices_search():
    """Device search: accepts 'query' in JSON and maps to device info/search."""
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    query = data.get('query')

    if not query:
        return jsonify({"error": "Missing 'query' parameter"}), 400

    if is_mac(query):
        device_data = get_device_data(query)
        if device_data.status_code == 200:
            return jsonify({"success": True, "devices": [device_data.get_json()]})
        else:
            return jsonify({"success": False, "error": "Device not found"}), 404

    # Create fresh DB instance for this thread
    device_handler = DeviceInstance()

    matches = device_handler.search(query)

    if not matches:
        return jsonify({"success": False, "error": "No devices found"}), 404

    return jsonify({"success": True, "devices": matches})


@app.route('/mcp/sse/devices/latest', methods=['GET'])
@app.route('/devices/latest', methods=['GET'])
def api_devices_latest():
    """Get latest device (most recent) - maps to DeviceInstance.getLatest()."""
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 401

    device_handler = DeviceInstance()

    latest = device_handler.getLatest()

    if not latest:
        return jsonify({"message": "No devices found"}), 404
    return jsonify([latest])


@app.route('/mcp/sse/devices/network/topology', methods=['GET'])
@app.route('/devices/network/topology', methods=['GET'])
def api_devices_network_topology():
    """Network topology mapping."""
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 401

    device_handler = DeviceInstance()

    result = device_handler.getNetworkTopology()

    return jsonify(result)


# --------------------------
# Net tools
# --------------------------
@app.route('/mcp/sse/nettools/wakeonlan', methods=['POST'])
@app.route("/nettools/wakeonlan", methods=["POST"])
def api_wakeonlan():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    data = request.json or {}
    mac = data.get("devMac")
    ip = data.get("devLastIP") or data.get('ip')
    if not mac and ip:

        device_handler = DeviceInstance()

        dev = device_handler.getByIP(ip)

        if not dev or not dev.get('devMac'):
            return jsonify({"success": False, "message": "ERROR: Device not found", "error": "MAC not resolved"}), 404
        mac = dev.get('devMac')

    # Validate that we have a valid MAC address
    if not mac:
        return jsonify({"success": False, "message": "ERROR: Missing device MAC or IP", "error": "Bad Request"}), 400

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


@app.route('/mcp/sse/nettools/trigger-scan', methods=['POST'])
@app.route("/nettools/trigger-scan", methods=["GET"])
def api_trigger_scan():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    data = request.get_json(silent=True) or {}
    scan_type = data.get('type', 'ARPSCAN')

    # Validate scan type
    loaded_plugins = get_setting_value('LOADED_PLUGINS')
    if scan_type not in loaded_plugins:
        return jsonify({"success": False, "error": f"Invalid scan type. Must be one of: {', '.join(loaded_plugins)}"}), 400

    queue = UserEventsQueueInstance()

    action = f"run|{scan_type}"

    queue.add_event(action)

    return jsonify({"success": True, "message": f"Scan triggered for type: {scan_type}"}), 200


# --------------------------
# MCP Server
# --------------------------
@app.route('/mcp/sse/openapi.json', methods=['GET'])
def api_openapi_spec():
    if not is_authorized():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    return openapi_spec()


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


@app.route('/mcp/sse/events/recent', methods=['GET', 'POST'])
@app.route('/events/recent', methods=['GET'])
def api_events_default_24h():
    return api_events_recent(24)  # Reuse handler


@app.route('/mcp/sse/events/last', methods=['GET', 'POST'])
@app.route('/events/last', methods=['GET'])
def get_last_events():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    # Create fresh DB instance for this thread
    event_handler = EventInstance()

    events = event_handler.get_last_n(10)
    return jsonify({"success": True, "count": len(events), "events": events}), 200


@app.route('/events/<int:hours>', methods=['GET'])
def api_events_recent(hours):
    """Return events from the last <hours> hours using EventInstance."""

    if not is_authorized():
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    # Validate hours input
    if hours <= 0:
        return jsonify({"success": False, "error": "Hours must be > 0"}), 400
    try:
        # Create fresh DB instance for this thread
        event_handler = EventInstance()

        events = event_handler.get_by_hours(hours)

        return jsonify({"success": True, "hours": hours, "count": len(events), "events": events}), 200

    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)}), 500

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
# Auth endpoint
# --------------------------
@app.route("/auth", methods=["GET"])
def check_auth():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    elif request.method == "GET":
        return jsonify({"success": True, "message": "Authentication check successful"}), 200
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
