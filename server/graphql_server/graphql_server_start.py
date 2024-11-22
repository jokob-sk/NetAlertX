import threading
from flask import Flask, request, jsonify
from .graphql_schema import devicesSchema
from graphene import Schema
import sys

# Register NetAlertX directories
INSTALL_PATH = "/app"
sys.path.extend([f"{INSTALL_PATH}/server"])

from logger import mylog
from helper import get_setting_value, timeNowTZ, updateState
from notification import write_notification

# Flask application
app = Flask(__name__)

# Retrieve API token and port
graphql_port_value = get_setting_value("GRAPHQL_PORT")

# Endpoint used when accessed via browser
@app.route("/graphql", methods=["GET"])
def graphql_debug():
    # Handles GET requests
    return "NetAlertX GraphQL server running."

# Endpoint for GraphQL queries
@app.route("/graphql", methods=["POST"])
def graphql_endpoint():
    # Check for API token in headers
    incoming_header_token = request.headers.get("Authorization")            
    api_token_value = get_setting_value("API_TOKEN")

    if incoming_header_token != f"Bearer {api_token_value}":
        mylog('verbose', [f'[graphql_server] Unauthorized access attempt'])
        return jsonify({"error": "Unauthorized"}), 401

    # Retrieve and log request data
    data = request.get_json()
    mylog('verbose', [f'[graphql_server] data: {data}'])

    # Execute the GraphQL query
    result = devicesSchema.execute(data.get("query"), variables=data.get("variables"))

    # Return the result as JSON
    return jsonify(result.data)

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
        app_state = updateState("Process: Wait", None, None, None, 1)