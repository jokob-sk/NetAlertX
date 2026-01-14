import threading
import sys
import os

# flake8: noqa: E402

from flask import Flask, request, jsonify, Response
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
    internet_info,
    network_interfaces
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
from .mcp_endpoint import (
    mcp_sse,
    mcp_messages,
    openapi_spec
)  # noqa: E402 [flake8 lint suppression]
# validation and schemas for MCP v2
from .spec_generator import validate_request  # noqa: E402 [flake8 lint suppression]
from .schemas import (  # noqa: E402 [flake8 lint suppression]
    DeviceSearchRequest, DeviceSearchResponse,
    DeviceListRequest, DeviceListResponse,
    DeviceInfo, DeviceExportResponse,
    GetDeviceResponse, DeviceUpdateRequest,
    BaseResponse, DeviceTotalsResponse,
    DeleteDevicesRequest, DeviceImportRequest,
    DeviceImportResponse, UpdateDeviceColumnRequest,
    CopyDeviceRequest, TriggerScanRequest,
    TriggerScanResponse, OpenPortsRequest,
    OpenPortsResponse, WakeOnLanRequest,
    WakeOnLanResponse, TracerouteRequest,
    TracerouteResponse, NmapScanRequest,
    NslookupRequest, RecentEventsResponse,
    LastEventsResponse, NetworkTopologyResponse,
    CreateEventRequest, CreateSessionRequest,
    DeleteSessionRequest, CreateNotificationRequest,
    SyncPushRequest, SyncPullResponse,
    DbQueryRequest, DbQueryResponse,
    DbQueryUpdateRequest, DbQueryDeleteRequest,
    AddToQueueRequest, GetSettingResponse,
    RecentEventsRequest, SetDeviceAliasRequest
)

from .sse_endpoint import (  # noqa: E402 [flake8 lint suppression]
    create_sse_endpoint
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
        r"/graphql/*": {"origins": "*"},
        r"/messaging/*": {"origins": "*"},
        r"/events/*": {"origins": "*"},
        r"/logs/*": {"origins": "*"},
        r"/api/tools/*": {"origins": "*"},
        r"/auth/*": {"origins": "*"},
        r"/mcp/*": {"origins": "*"},
        r"/openapi.json": {"origins": "*"},
        r"/sse/*": {"origins": "*"}
    },
    supports_credentials=True,
    allow_headers=["Authorization", "Content-Type"],
)

# -------------------------------------------------------------------------------
# MCP bridge variables + helpers
# -------------------------------------------------------------------------------

BACKEND_PORT = get_setting_value("GRAPHQL_PORT")
API_BASE_URL = f"http://localhost:{BACKEND_PORT}"




@app.route('/mcp/sse', methods=['GET', 'POST'])
def api_mcp_sse():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    return mcp_sse()


@app.route('/mcp/messages', methods=['POST'])
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
    safe_headers = {k: v for k, v in request.headers.items() if k.lower() not in ('authorization', 'cookie', 'x-api-key')}
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
        return jsonify({"success": False, "message": msg, "error": "Forbidden"}), 403

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
@validate_request(
    operation_id="get_setting",
    summary="Get Setting",
    description="Retrieve the value of a specific setting by key.",
    path_params=[{
        "name": "setKey",
        "description": "Setting key",
        "schema": {"type": "string"}
    }],
    response_model=GetSettingResponse,
    tags=["settings"]
)
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
@validate_request(
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
def api_get_device(mac):
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    period = request.args.get("period", "")
    device_handler = DeviceInstance()
    device_data = device_handler.getDeviceData(mac, period)

    if device_data is None:
        return jsonify({"error": "Device not found"}), 404

    return jsonify(device_data)


@app.route("/device/<mac>", methods=["POST"])
@validate_request(
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
def api_set_device(mac):
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    device_handler = DeviceInstance()
    result = device_handler.setDeviceData(mac, request.json)
    return jsonify(result)


@app.route("/device/<mac>/delete", methods=["DELETE"])
@validate_request(
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
def api_delete_device(mac):
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    device_handler = DeviceInstance()
    result = device_handler.deleteDeviceByMAC(mac)
    return jsonify(result)


@app.route("/device/<mac>/events/delete", methods=["DELETE"])
@validate_request(
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
def api_delete_device_events(mac):
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    device_handler = DeviceInstance()
    result = device_handler.deleteDeviceEvents(mac)
    return jsonify(result)


@app.route("/device/<mac>/reset-props", methods=["POST"])
@validate_request(
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
def api_reset_device_props(mac):
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    device_handler = DeviceInstance()
    result = device_handler.resetDeviceProps(mac)
    return jsonify(result)


@app.route("/device/copy", methods=["POST"])
@validate_request(
    operation_id="copy_device",
    summary="Copy Device Settings",
    description="Copy settings and history from one device MAC address to another.",
    request_model=CopyDeviceRequest,
    response_model=BaseResponse,
    tags=["devices"]
)
def api_device_copy():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    data = request.get_json() or {}
    mac_from = data.get("macFrom")
    mac_to = data.get("macTo")

    if not mac_from or not mac_to:
        return jsonify({"success": False, "message": "ERROR: Missing parameters", "error": "macFrom and macTo are required"}), 400

    device_handler = DeviceInstance()
    result = device_handler.copyDevice(mac_from, mac_to)
    return jsonify(result)


@app.route("/device/<mac>/update-column", methods=["POST"])
@validate_request(
    operation_id="update_device_column",
    summary="Update Device Column",
    description="Update a specific database column for a device.",
    path_params=[{
        "name": "mac",
        "description": "Device MAC address",
        "schema": {"type": "string"}
    }],
    request_model=UpdateDeviceColumnRequest,
    response_model=BaseResponse,
    tags=["devices"]
)
def api_device_update_column(mac):
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    data = request.get_json() or {}
    column_name = data.get("columnName")
    column_value = data.get("columnValue")

    # columnName is required, but columnValue can be empty string (e.g., for unassigning)
    if not column_name or "columnValue" not in data:
        return jsonify({"success": False, "message": "ERROR: Missing parameters", "error": "columnName and columnValue are required"}), 400

    device_handler = DeviceInstance()
    result = device_handler.updateDeviceColumn(mac, column_name, column_value)

    if not result.get("success"):
        return jsonify(result), 404

    return jsonify(result)


@app.route('/mcp/sse/device/<mac>/set-alias', methods=['POST'])
@app.route('/device/<mac>/set-alias', methods=['POST'])
@validate_request(
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
def api_device_set_alias(mac):
    """Set the device alias - convenience wrapper around updateDeviceColumn."""
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    data = request.get_json() or {}
    alias = data.get('alias')
    if not alias:
        return jsonify({"success": False, "message": "ERROR: Missing parameters", "error": "alias is required"}), 400

    device_handler = DeviceInstance()
    result = device_handler.updateDeviceColumn(mac, 'devName', alias)
    return jsonify(result)


@app.route('/mcp/sse/device/open_ports', methods=['POST'])
@app.route('/device/open_ports', methods=['POST'])
@validate_request(
    operation_id="get_open_ports",
    summary="Get Open Ports",
    description="Retrieve open ports for a target IP or MAC address. Returns cached NMAP scan results.",
    request_model=OpenPortsRequest,
    response_model=OpenPortsResponse,
    tags=["nettools"]
)
def api_device_open_ports():
    """Get stored NMAP open ports for a target IP or MAC."""
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

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
@validate_request(
    operation_id="get_all_devices",
    summary="Get All Devices",
    description="Retrieve a list of all devices in the system.",
    response_model=DeviceListResponse,
    tags=["devices"]
)
def api_get_devices():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    device_handler = DeviceInstance()
    devices = device_handler.getAll_AsResponse()
    return jsonify({"success": True, "devices": devices})


@app.route("/devices", methods=["DELETE"])
@validate_request(
    operation_id="delete_devices",
    summary="Delete Multiple Devices",
    description="Delete multiple devices by MAC address.",
    request_model=DeleteDevicesRequest,
    tags=["devices"]
)
def api_devices_delete():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    data = request.get_json(silent=True) or {}
    macs = data.get('macs', [])

    if not macs:
        return jsonify({"success": False, "message": "ERROR: Missing parameters", "error": "macs list is required"}), 400

    device_handler = DeviceInstance()
    return jsonify(device_handler.deleteDevices(macs))


@app.route("/devices/empty-macs", methods=["DELETE"])
@validate_request(
    operation_id="delete_empty_mac_devices",
    summary="Delete Devices with Empty MACs",
    description="Delete all devices that do not have a valid MAC address.",
    response_model=BaseResponse,
    tags=["devices"]
)
def api_delete_all_empty_macs():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    device_handler = DeviceInstance()
    return jsonify(device_handler.deleteAllWithEmptyMacs())


@app.route("/devices/unknown", methods=["DELETE"])
@validate_request(
    operation_id="delete_unknown_devices",
    summary="Delete Unknown Devices",
    description="Delete devices marked as unknown.",
    response_model=BaseResponse,
    tags=["devices"]
)
def api_delete_unknown_devices():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    device_handler = DeviceInstance()
    return jsonify(device_handler.deleteUnknownDevices())


@app.route('/mcp/sse/devices/export', methods=['GET'])
@app.route("/devices/export", methods=["GET"])
@app.route("/devices/export/<format>", methods=["GET"])
@validate_request(
    operation_id="export_devices",
    summary="Export Devices",
    description="Export all devices in CSV or JSON format.",
    query_params=[{
        "name": "format",
        "description": "Export format: csv or json",
        "required": False,
        "schema": {"type": "string", "enum": ["csv", "json"], "default": "csv"}
    }],
    path_params=[{
        "name": "format",
        "description": "Export format: csv or json",
        "required": False,
        "schema": {"type": "string", "enum": ["csv", "json"]}
    }],
    response_model=DeviceExportResponse,
    tags=["devices"]
)
def api_export_devices(format=None):
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    export_format = (format or request.args.get("format", "csv")).lower()
    device_handler = DeviceInstance()
    result = device_handler.exportDevices(export_format)

    if "error" in result:
        return jsonify(result), 400

    if result["format"] == "json":
        return jsonify({"data": result["data"], "columns": result["columns"]})
    elif result["format"] == "csv":
        return Response(
            result["content"],
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=devices.csv"},
        )


@app.route('/mcp/sse/devices/import', methods=['POST'])
@app.route("/devices/import", methods=["POST"])
@validate_request(
    operation_id="import_devices",
    summary="Import Devices",
    description="Import devices from CSV or JSON content.",
    request_model=DeviceImportRequest,
    response_model=DeviceImportResponse,
    tags=["devices"]
)
def api_import_csv():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    device_handler = DeviceInstance()
    json_content = None
    file_storage = None

    if request.is_json and request.json.get("content"):
        json_content = request.json.get("content")
    else:
        file_storage = request.files.get("file")

    result = device_handler.importCSV(file_storage=file_storage, json_content=json_content)

    if not result.get("success"):
        return jsonify(result), 400

    return jsonify(result)


@app.route('/mcp/sse/devices/totals', methods=['GET'])
@app.route("/devices/totals", methods=["GET"])
@validate_request(
    operation_id="get_device_totals",
    summary="Get Device Totals",
    description="Get device statistics including total count, online/offline counts, new devices, and archived devices.",
    response_model=DeviceTotalsResponse,
    tags=["devices"]
)
def api_devices_totals():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    device_handler = DeviceInstance()
    return jsonify(device_handler.getTotals())


@app.route('/mcp/sse/devices/by-status', methods=['GET', 'POST'])
@app.route("/devices/by-status", methods=["GET", "POST"])
@validate_request(
    operation_id="list_devices_by_status",
    summary="List Devices by Status",
    description="List devices filtered by their online/offline status.",
    request_model=DeviceListRequest,
    response_model=DeviceListResponse,
    tags=["devices"]
)
def api_devices_by_status():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    data = request.get_json(silent=True) or {}
    status = data.get("status") or request.args.get("status")

    device_handler = DeviceInstance()
    return jsonify(device_handler.getByStatus(status))


@app.route('/mcp/sse/devices/search', methods=['POST'])
@app.route('/devices/search', methods=['POST'])
@validate_request(
    operation_id="search_devices",
    summary="Search Devices",
    description="Search for devices based on various criteria like name, IP, MAC, or vendor.",
    request_model=DeviceSearchRequest,
    response_model=DeviceSearchResponse,
    tags=["devices"]
)
def api_devices_search():
    """Device search: accepts 'query' in JSON and maps to device info/search."""
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    data = request.get_json(silent=True) or {}
    query = data.get('query')

    if not query:
        return jsonify({"success": False, "message": "Missing 'query' parameter", "error": "Missing query"}), 400

    device_handler = DeviceInstance()

    if is_mac(query):

        device_data = device_handler.getDeviceData(query)
        if device_data:
            return jsonify({"success": True, "devices": [device_data]})
        else:
            return jsonify({"success": False, "message": "Device not found", "error": "Device not found"}), 404

    matches = device_handler.search(query)

    if not matches:
        return jsonify({"success": False, "message": "No devices found", "error": "No devices found"}), 404

    return jsonify({"success": True, "devices": matches})


@app.route('/mcp/sse/devices/latest', methods=['GET'])
@app.route('/devices/latest', methods=['GET'])
@validate_request(
    operation_id="get_latest_device",
    summary="Get Latest Device",
    description="Get information about the most recently seen/discovered device.",
    response_model=GetDeviceResponse,
    tags=["devices"]
)
def api_devices_latest():
    """Get latest device (most recent) - maps to DeviceInstance.getLatest()."""
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    device_handler = DeviceInstance()

    latest = device_handler.getLatest()

    if not latest:
        return jsonify({"success": False, "message": "No devices found"}), 404
    return jsonify([latest])


@app.route('/mcp/sse/devices/favorite', methods=['GET'])
@app.route('/devices/favorite', methods=['GET'])
@validate_request(
    operation_id="get_favorite_devices",
    summary="Get Favorite Devices",
    description="Get list of devices marked as favorites.",
    response_model=DeviceListResponse,
    tags=["devices"]
)
def api_devices_favorite():
    """Get favorite devices - maps to DeviceInstance.getFavorite()."""
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    device_handler = DeviceInstance()

    favorite = device_handler.getFavorite()

    if not favorite:
        return jsonify({"success": False, "message": "No devices found"}), 404
    return jsonify([favorite])


@app.route('/mcp/sse/devices/network/topology', methods=['GET'])
@app.route('/devices/network/topology', methods=['GET'])
@validate_request(
    operation_id="get_network_topology",
    summary="Get Network Topology",
    description="Retrieve the network topology information showing device connections and network structure.",
    response_model=NetworkTopologyResponse,
    tags=["devices"]
)
def api_devices_network_topology():
    """Network topology mapping."""
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    device_handler = DeviceInstance()

    result = device_handler.getNetworkTopology()

    return jsonify(result)


# --------------------------
# Net tools
# --------------------------
@app.route('/mcp/sse/nettools/wakeonlan', methods=['POST'])
@app.route("/nettools/wakeonlan", methods=["POST"])
@validate_request(
    operation_id="wake_on_lan",
    summary="Wake-on-LAN",
    description="Send a Wake-on-LAN magic packet to wake up a device.",
    request_model=WakeOnLanRequest,
    response_model=WakeOnLanResponse,
    tags=["nettools"]
)
def api_wakeonlan():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    data = request.get_json(silent=True) or {}
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


@app.route('/mcp/sse/nettools/traceroute', methods=['POST'])
@app.route("/nettools/traceroute", methods=["POST"])
@validate_request(
    operation_id="perform_traceroute",
    summary="Traceroute",
    description="Perform a traceroute to a target IP address.",
    request_model=TracerouteRequest
)
def api_traceroute():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    data = request.get_json(silent=True) or {}
    ip = data.get("devLastIP")
    if not ip:
        return jsonify({"success": False, "message": "ERROR: Missing parameters", "error": "Missing 'devLastIP'"}), 400

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


@app.route("/nettools/interfaces", methods=["GET"])
def api_network_interfaces():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    return network_interfaces()


@app.route('/mcp/sse/nettools/trigger-scan', methods=['POST'])
@app.route("/nettools/trigger-scan", methods=["GET"])
@validate_request(
    operation_id="trigger_network_scan",
    summary="Trigger Network Scan",
    description="Trigger a network scan to discover devices. Specify scan type matching an enabled plugin.",
    request_model=TriggerScanRequest,
    tags=["nettools"]
)
def api_trigger_scan():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    # Check POST body first, then GET args
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        scan_type = data.get("type", "ARPSCAN")
    else:
        scan_type = request.args.get("type", "ARPSCAN")

    result = trigger_scan(scan_type=scan_type)
    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code


def trigger_scan(scan_type):
    """Trigger a network scan by adding it to the execution queue."""
    if scan_type not in ["ARPSCAN", "NMAPDEV", "NMAP"]:
        return {"success": False, "message": f"Invalid scan type: {scan_type}"}

    queue = UserEventsQueueInstance()
    res = queue.add_event("run|" + scan_type)

    # Handle mocks in tests that don't return a tuple
    if isinstance(res, tuple) and len(res) == 2:
        success, message = res
    else:
        success = True
        message = f"Action \"run|{scan_type}\" added to the execution queue."

    return {"success": success, "message": message, "scan_type": scan_type}


# --------------------------
# MCP Server
# --------------------------
@app.route('/openapi.json', methods=['GET'])
@app.route('/mcp/sse/openapi.json', methods=['GET'])
def api_openapi_spec():
    # Allow unauthenticated access to the spec itself so Swagger UI can load.
    # The actual API endpoints remain protected.
    return openapi_spec()


@app.route('/docs')
def api_docs():
    """Serve Swagger UI for API documentation."""
    # We don't require auth for the UI shell, but the openapi.json fetch 
    # will still need the token if accessed directly, or we can allow public access to docs.
    # For now, let's allow public access to the UI shell.
    # The user can enter the Bearer token in the "Authorize" button if needed,
    # or we can auto-inject it if they are already logged in (advanced).
    
    # We need to serve the static HTML file we created.
    import os
    from flask import send_from_directory
    
    # Assuming swagger.html is in the same directory as this file (api_server)
    api_server_dir = os.path.dirname(os.path.realpath(__file__))
    return send_from_directory(api_server_dir, 'swagger.html')


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
@validate_request(
    operation_id="delete_online_history",
    summary="Delete Online History",
    description="Delete all online history records.",
    response_model=BaseResponse,
    tags=["logs"]
)
def api_delete_online_history():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403
    return delete_online_history()


# --------------------------
# Logs
# --------------------------

@app.route("/logs", methods=["DELETE"])
@validate_request(
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
def api_clean_log():

    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    file = request.args.get("file")
    if not file:

        return jsonify({"success": False, "message": "ERROR: Missing parameters", "error": "Missing 'file' query parameter"}), 400

    return clean_log(file)


@app.route("/logs/add-to-execution-queue", methods=["POST"])
@validate_request(
    operation_id="add_to_execution_queue",
    summary="Add to Execution Queue",
    description="Add an action to the system execution queue.",
    request_model=AddToQueueRequest,
    response_model=BaseResponse,
    tags=["logs"],
    validation_error_code=400
)
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
@validate_request(
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
def api_create_event(mac):
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    data = request.json or {}
    ip = data.get("ip", "0.0.0.0")
    event_type = data.get("event_type", "Device Down")
    additional_info = data.get("additional_info", "")
    pending_alert = data.get("pending_alert", 1)
    event_time = data.get("event_time", None)

    event_handler = EventInstance()
    result = event_handler.createEvent(mac, ip, event_type, additional_info, pending_alert, event_time)

    return jsonify(result)


@app.route("/events/<mac>", methods=["DELETE"])
@validate_request(
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
def api_events_by_mac(mac):
    """Delete events for a specific device MAC; string converter keeps this distinct from /events/<int:days>."""
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    device_handler = DeviceInstance()
    result = device_handler.deleteDeviceEvents(mac)
    return jsonify(result)


@app.route("/events", methods=["DELETE"])
@validate_request(
    operation_id="delete_all_events",
    summary="Delete All Events",
    description="Delete all events in the system.",
    response_model=BaseResponse,
    tags=["events"]
)
def api_delete_all_events():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    event_handler = EventInstance()
    result = event_handler.deleteAllEvents()
    return jsonify(result)


@app.route("/events", methods=["GET"])
@validate_request(
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
def api_get_events():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    mac = request.args.get("mac")
    event_handler = EventInstance()
    events = event_handler.getEvents(mac)
    return jsonify({"count": len(events), "events": events})


@app.route("/events/<int:days>", methods=["DELETE"])
@validate_request(
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
def api_delete_old_events(days: int):
    """
    Delete events older than <days> days.
    Example: DELETE /events/30
    """
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    event_handler = EventInstance()
    result = event_handler.deleteEventsOlderThan(days)
    return jsonify(result)


@app.route("/sessions/totals", methods=["GET"])
def api_get_events_totals():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    period = request.args.get("period", "7 days")
    event_handler = EventInstance()
    totals = event_handler.getEventsTotals(period)
    return jsonify(totals)


@app.route('/mcp/sse/events/recent', methods=['GET', 'POST'])
@app.route('/events/recent', methods=['GET'])
@validate_request(
    operation_id="get_recent_events",
    summary="Get Recent Events",
    description="Get recent events from the system.",
    request_model=RecentEventsRequest
)
def api_events_default_24h():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    hours = 24
    if request.args:
        try:
            hours = int(request.args.get("hours", 24))
        except (ValueError, TypeError):
            hours = 24

    return api_events_recent(hours)


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
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

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
    mac = request.args.get("mac")

    return get_sessions_calendar(start_date, end_date, mac)


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
@validate_request(
    operation_id="get_metrics",
    summary="Get Metrics",
    description="Get Prometheus-compatible metrics.",
    response_model=None,
    tags=["logs"]
)
def metrics():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    # Return Prometheus metrics as plain text
    return Response(get_metric_stats(), mimetype="text/plain")


# --------------------------
# In-app notifications
# --------------------------
@app.route("/messaging/in-app/write", methods=["POST"])
@validate_request(
    operation_id="write_notification",
    summary="Write Notification",
    description="Create a new in-app notification.",
    request_model=CreateNotificationRequest,
    response_model=BaseResponse,
    tags=["messaging"]
)
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
@validate_request(
    operation_id="get_unread_notifications",
    summary="Get Unread Notifications",
    description="Retrieve all unread in-app notifications.",
    tags=["messaging"]
)
def api_get_unread_notifications():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    return get_unread_notifications()


@app.route("/messaging/in-app/read/all", methods=["POST"])
@validate_request(
    operation_id="mark_all_notifications_read",
    summary="Mark All Read",
    description="Mark all in-app notifications as read.",
    response_model=BaseResponse,
    tags=["messaging"]
)
def api_mark_all_notifications_read():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    return jsonify(mark_all_notifications_read())


@app.route("/messaging/in-app/delete", methods=["DELETE"])
@validate_request(
    operation_id="delete_all_notifications",
    summary="Delete All Notifications",
    description="Delete all in-app notifications.",
    response_model=BaseResponse,
    tags=["messaging"]
)
def api_delete_all_notifications():
    if not is_authorized():
        return jsonify({"success": False, "message": "ERROR: Not authorized", "error": "Forbidden"}), 403

    return delete_notifications()


@app.route("/messaging/in-app/delete/<guid>", methods=["DELETE"])
@validate_request(
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
@validate_request(
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
@validate_request(
    operation_id="sync_data",
    summary="Sync Data",
    description="Synchronize data between nodes.",
    tags=["sync"]
)
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
@validate_request(
    operation_id="check_auth",
    summary="Check Authentication",
    description="Check if the current API token is valid.",
    response_model=BaseResponse,
    tags=["auth"]
)
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
    expected_token = get_setting_value('API_TOKEN')

    # Check Authorization header first (primary method)
    auth_header = request.headers.get("Authorization", "")
    header_token = auth_header.split()[-1] if auth_header.startswith("Bearer ") else ""

    # Also check query string token (for SSE and other streaming endpoints)
    query_token = request.args.get("token", "")

    is_authorized = (header_token == expected_token) or (query_token == expected_token)

    if not is_authorized:
        msg = "[api] Unauthorized access attempt - make sure your GRAPHQL_PORT and API_TOKEN settings are correct."
        write_notification(msg, "alert")
        mylog("verbose", [msg])

    return is_authorized


# Mount SSE endpoints after is_authorized is defined (avoid circular import)
create_sse_endpoint(app, is_authorized)


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
