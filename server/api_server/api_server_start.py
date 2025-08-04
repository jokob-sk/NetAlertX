import threading
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from .graphql_schema import devicesSchema
from .prometheus_metrics import getMetricStats
from graphene import Schema
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
CORS(app, resources={r"/metrics": {"origins": "*"}}, supports_credentials=True, allow_headers=["Authorization"])

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
# Prometheus /metrics Endpoint
# --------------------------

@app.route("/metrics")
def metrics():

    # Check for API token in headers
    if not is_authorized():
        msg = '[metrics] Unauthorized access attempt - make sure your GRAPHQL_PORT and API_TOKEN settings are correct.'
        mylog('verbose', [msg])
        return jsonify({"error": msg}), 401


    # Return Prometheus metrics as plain text
    return  Response(getMetricStats(), mimetype="text/plain")
    

# --------------------------
# Background Server Start
# --------------------------
def is_authorized():
    token = request.headers.get("Authorization")
    return token == f"Bearer {get_setting_value('API_TOKEN')}"


def start_server(graphql_port, app_state):
    """Start the GraphQL server in a background thread."""

    if app_state.graphQLServerStarted == 0:
                
        mylog('verbose', [f'[graphql_server] Starting on port: {graphql_port}'])

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