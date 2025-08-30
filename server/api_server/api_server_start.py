import threading
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from .graphql_endpoint import devicesSchema
from .device_endpoint import get_device_data, set_device_data, delete_device, delete_device_events, reset_device_props, copy_device, update_device_column
from .devices_endpoint import get_all_devices, delete_unknown_devices, delete_all_with_empty_macs, delete_devices, export_devices, import_csv, devices_totals, devices_by_status
from .events_endpoint import delete_events, delete_events_older_than, get_events, create_event, get_events_totals
from .history_endpoint import delete_online_history
from .prometheus_endpoint import get_metric_stats
from .sessions_endpoint import get_sessions, delete_session, create_session, get_sessions_calendar, get_device_sessions, get_session_events
from .nettools_endpoint import wakeonlan, traceroute, speedtest, nslookup, nmap_scan, internet_info
from .dbquery_endpoint import read_query, write_query, update_query, delete_query
from .sync_endpoint import handle_sync_post, handle_sync_get
import sys

# Register NetAlertX directories
INSTALL_PATH = "/app"
sys.path.extend([f"{INSTALL_PATH}/server"])

from logger import mylog
from helper import get_setting_value, timeNowTZ
from db.db_helper import get_date_from_period
from app_state import updateState
from messaging.in_app import write_notification

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
        r"/events/*": {"origins": "*"}
    },
    supports_credentials=True,
    allow_headers=["Authorization", "Content-Type"]
)

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
        return jsonify({"error": msg}), 401

    # Retrieve and log request data
    data = request.get_json()
    mylog('verbose', [f'[graphql_server] data: {data}'])

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
# Settings Endpoints
# --------------------------

@app.route("/settings/<setKey>", methods=["GET"])
def api_get_setting(setKey):
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403
    value = get_setting_value(setKey)
    return jsonify({"success": True, "value": value})

# --------------------------
# Device Endpoints
# --------------------------

@app.route("/device/<mac>", methods=["GET"])
def api_get_device(mac):
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403
    return get_device_data(mac)

@app.route("/device/<mac>", methods=["POST"])
def api_set_device(mac):
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403
    return set_device_data(mac, request.json)

@app.route("/device/<mac>/delete", methods=["DELETE"])
def api_delete_device(mac):
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403
    return delete_device(mac)

@app.route("/device/<mac>/events/delete", methods=["DELETE"])
def api_delete_device_events(mac):
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403
    return delete_device_events(mac)

@app.route("/device/<mac>/reset-props", methods=["POST"])
def api_reset_device_props(mac):
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403
    return reset_device_props(mac, request.json)

@app.route("/device/copy", methods=["POST"])
def api_copy_device():
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json() or {}
    mac_from = data.get("macFrom")
    mac_to = data.get("macTo")

    if not mac_from or not mac_to:
        return jsonify({"success": False, "error": "macFrom and macTo are required"}), 400

    return copy_device(mac_from, mac_to)

@app.route("/device/<mac>/update-column", methods=["POST"])
def api_update_device_column(mac):
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json() or {}
    column_name = data.get("columnName")
    column_value = data.get("columnValue")

    if not column_name or not column_value:
        return jsonify({"success": False, "error": "columnName and columnValue are required"}), 400

    return update_device_column(mac, column_name, column_value)

# --------------------------
# Devices Collections
# --------------------------

@app.route("/devices", methods=["GET"])
def api_get_devices():
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403
    return get_all_devices()

@app.route("/devices", methods=["DELETE"])
def api_delete_devices():
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403
    
    macs = request.json.get("macs") if request.is_json else None

    return delete_devices(macs)

@app.route("/devices/empty-macs", methods=["DELETE"])
def api_delete_all_empty_macs():
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403
    return delete_all_with_empty_macs()

@app.route("/devices/unknown", methods=["DELETE"])
def api_delete_unknown_devices():
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403
    return delete_unknown_devices()


@app.route("/devices/export", methods=["GET"])
@app.route("/devices/export/<format>", methods=["GET"])
def api_export_devices(format=None):
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403

    export_format = (format or request.args.get("format", "csv")).lower()
    return export_devices(export_format)

@app.route("/devices/import", methods=["POST"])
def api_import_csv():
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403
    return import_csv(request.files.get("file"))

@app.route("/devices/totals", methods=["GET"])
def api_devices_totals():
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403
    return devices_totals()

@app.route("/devices/by-status", methods=["GET"])
def api_devices_by_status():
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403

    status = request.args.get("status", "") if request.args else None

    return devices_by_status(status)

# --------------------------
# Net tools
# --------------------------
@app.route("/nettools/wakeonlan", methods=["POST"])
def api_wakeonlan():
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403

    mac = request.json.get("devMac")
    return wakeonlan(mac)

@app.route("/nettools/traceroute", methods=["POST"])
def api_traceroute():
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403
    ip = request.json.get("devLastIP")
    return traceroute(ip)

@app.route("/nettools/speedtest", methods=["GET"])
def api_speedtest():
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403
    return speedtest()

@app.route("/nettools/nslookup", methods=["POST"])
def api_nslookup():
    """
    API endpoint to handle nslookup requests.
    Expects JSON with 'devLastIP'.
    """
    if not is_authorized():
        return jsonify({"success": False, "error": "Forbidden"}), 403

    data = request.get_json(silent=True)
    if not data or "devLastIP" not in data:
        return jsonify({"success": False, "error": "Missing 'devLastIP'"}), 400

    ip = data["devLastIP"]
    return nslookup(ip)

@app.route("/nettools/nmap", methods=["POST"])
def api_nmap():
    """
    API endpoint to handle nmap scan requests.
    Expects JSON with 'scan' (IP address) and 'mode' (scan mode).
    """
    if not is_authorized():
        return jsonify({"success": False, "error": "Forbidden"}), 403

    data = request.get_json(silent=True)
    if not data or "scan" not in data or "mode" not in data:
        return jsonify({"success": False, "error": "Missing 'scan' or 'mode'"}), 400

    ip = data["scan"]
    mode = data["mode"]
    return nmap_scan(ip, mode)
    

@app.route("/nettools/internetinfo", methods=["GET"])
def api_internet_info():
    if not is_authorized():
        return jsonify({"success": False, "error": "Forbidden"}), 403
    return internet_info()


# --------------------------
# DB query
# --------------------------

@app.route("/dbquery/read", methods=["POST"])
def dbquery_read():
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json() or {}
    raw_sql_b64 = data.get("rawSql")

    if not raw_sql_b64:
        return jsonify({"error": "rawSql is required"}), 400
    
    return read_query(raw_sql_b64)
    

@app.route("/dbquery/write", methods=["POST"])
def dbquery_write():
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json() or {}
    raw_sql_b64 = data.get("rawSql")
    if not raw_sql_b64:
        return jsonify({"error": "rawSql is required"}), 400

    return write_query(raw_sql_b64)


@app.route("/dbquery/update", methods=["POST"])
def dbquery_update():
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json() or {}
    required = ["columnName", "id", "dbtable", "columns", "values"]
    if not all(data.get(k) for k in required):
        return jsonify({"error": "Missing required parameters"}), 400

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
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json() or {}
    required = ["columnName", "id", "dbtable"]
    if not all(data.get(k) for k in required):
        return jsonify({"error": "Missing required parameters"}), 400

    return  delete_query(
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
        return jsonify({"error": "Forbidden"}), 403
    return delete_online_history()

# --------------------------
# Device Events
# --------------------------

@app.route("/events/create/<mac>", methods=["POST"])
def api_create_event(mac):
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403

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
        return jsonify({"error": "Forbidden"}), 403
    return delete_device_events(mac)

@app.route("/events", methods=["DELETE"])
def api_delete_all_events():
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403
    return delete_events()

@app.route("/events", methods=["GET"])
def api_get_events():
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403

    mac = request.args.get("mac")
    return get_events(mac)

@app.route("/events/<int:days>", methods=["DELETE"])
def api_delete_old_events(days: int):
    """
    Delete events older than <days> days.
    Example: DELETE /events/30
    """
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403
    
    return delete_events_older_than(days)

@app.route("/sessions/totals", methods=["GET"])
def api_get_events_totals():
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403

    period = get_date_from_period(request.args.get("period", "7 days"))
    return get_events_totals(period)

# --------------------------
# Sessions
# --------------------------

@app.route("/sessions/create", methods=["POST"])
def api_create_session():
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403

    data = request.json
    mac = data.get("mac")
    ip = data.get("ip")
    start_time = data.get("start_time")
    end_time = data.get("end_time")
    event_type_conn = data.get("event_type_conn", "Connected")
    event_type_disc = data.get("event_type_disc", "Disconnected")

    if not mac or not ip or not start_time:
        return jsonify({"success": False, "error": "Missing required parameters"}), 400

    return create_session(mac, ip, start_time, end_time, event_type_conn, event_type_disc)


@app.route("/sessions/delete", methods=["DELETE"])
def api_delete_session():
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403

    mac = request.json.get("mac") if request.is_json else None
    if not mac:
        return jsonify({"success": False, "error": "Missing MAC parameter"}), 400

    return delete_session(mac)


@app.route("/sessions/list", methods=["GET"])
def api_get_sessions():
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403

    mac = request.args.get("mac")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    return get_sessions(mac, start_date, end_date)

@app.route("/sessions/calendar", methods=["GET"])
def api_get_sessions_calendar():
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403

    # Query params: /sessions/calendar?start=2025-08-01&end=2025-08-21
    start_date = request.args.get("start")
    end_date = request.args.get("end")

    return get_sessions_calendar(start_date, end_date)

@app.route("/sessions/<mac>", methods=["GET"])
def api_device_sessions(mac):
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403

    period = request.args.get("period", "1 day")
    return get_device_sessions(mac, period)

@app.route("/sessions/session-events", methods=["GET"])
def api_get_session_events():
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403

    session_event_type = request.args.get("type", "all")
    period = get_date_from_period(request.args.get("period", "7 days"))
    return get_session_events(session_event_type, period)

# --------------------------
# Prometheus metrics endpoint
# --------------------------
@app.route("/metrics")
def metrics():
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403

    # Return Prometheus metrics as plain text
    return  Response(get_metric_stats(), mimetype="text/plain")
    
# --------------------------
# SYNC endpoint
# --------------------------
@app.route("/sync", methods=["GET", "POST"])
def sync_endpoint():
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403

    if request.method == "GET":
        return handle_sync_get()
    elif request.method == "POST":
        return handle_sync_post()
    else:
        msg = "[sync endpoint] Method Not Allowed"
        write_notification(msg, "alert")
        mylog("verbose", [msg])
        return jsonify({"error": "Method Not Allowed"}), 405

# --------------------------
# Background Server Start
# --------------------------
def is_authorized():
    token = request.headers.get("Authorization")
    is_authorized = token == f"Bearer {get_setting_value('API_TOKEN')}"

    if not is_authorized:
        msg = f"[api] Unauthorized access attempt - make sure your GRAPHQL_PORT and API_TOKEN settings are correct."
        write_notification(msg, "alert")
        mylog("verbose", [msg])

    return is_authorized


def start_server(graphql_port, app_state):
    """Start the GraphQL server in a background thread."""

    if app_state.graphQLServerStarted == 0:
                
        mylog('verbose', [f'[graphql endpoint] Starting on port: {graphql_port}'])

        # Start Flask app in a separate thread
        thread = threading.Thread(
            target=lambda: app.run(
                host="0.0.0.0",
                port=graphql_port,
                debug=True,
                use_reloader=False
            )
        )
        thread.start()

        # Update the state to indicate the server has started
        app_state = updateState("Process: Idle", None, None, None, 1)