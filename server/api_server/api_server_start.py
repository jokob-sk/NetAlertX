import threading
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from .graphql_endpoint import devicesSchema
from .device_endpoint import get_device_data, set_device_data, delete_device, delete_device_events, reset_device_props, copy_device, update_device_column
from .devices_endpoint import delete_unknown_devices, delete_all_with_empty_macs, delete_devices, export_devices, import_csv, devices_totals, devices_by_status
from .events_endpoint import delete_events, delete_events_30, get_events
from .history_endpoint import delete_online_history
from .prometheus_endpoint import getMetricStats
from .sync_endpoint import handle_sync_post, handle_sync_get
import sys

# Register NetAlertX directories
INSTALL_PATH = "/app"
sys.path.extend([f"{INSTALL_PATH}/server"])

from logger import mylog
from helper import get_setting_value, timeNowTZ
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

    # Return the result as JSON
    return jsonify(result.data)

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

    mac = request.json.get("mac") if request.is_json else None

    return get_events(mac)

@app.route("/events/30days", methods=["DELETE"])
def api_delete_old_events():
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403
    return delete_events_30()

# --------------------------
# Prometheus metrics endpoint
# --------------------------
@app.route("/metrics")
def metrics():

    # Check for API token in headers
    if not is_authorized():
        return jsonify({"error": "Forbidden"}), 403


    # Return Prometheus metrics as plain text
    return  Response(getMetricStats(), mimetype="text/plain")
    
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