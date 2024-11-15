import threading
from flask import Flask, request, jsonify
from .graphql_schema import devicesSchema
from graphene import Schema
import sys

# Global variable to track the server thread
server_thread = None

# Register NetAlertX directories
INSTALL_PATH="/app"
sys.path.extend([f"{INSTALL_PATH}/server"])

from logger import mylog
from helper import get_setting_value, timeNowTZ, updateState
from notification import write_notification

app = Flask(__name__)

GRAPHQL_PORT = get_setting_value("GRAPHQL_PORT")
API_TOKEN = get_setting_value("API_TOKEN")

@app.route("/graphql", methods=["POST"])
def graphql_endpoint():
    # Check for API token in headers
    token = request.headers.get("Authorization")
    if token != f"Bearer {API_TOKEN}":
        mylog('verbose', [f'[graphql_server] Unauthorized access attempt'])
       
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    mylog('verbose', [f'[graphql_server] data: {data}'])


    # Use the schema to execute the GraphQL query
    result = devicesSchema.execute(data.get("query"), variables=data.get("variables"))

    # Return the data from the query in JSON format
    return jsonify(result.data)

def start_server():
    """Function to start the GraphQL server in a background thread."""
    mylog('verbose', [f'[graphql_server] Starting on port: {GRAPHQL_PORT}'])

    state = updateState("GraphQL: Starting", None, None, None, None) 

    if state.graphQLServerStarted == 0:

        # Start the Flask app in a separate thread
        thread = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=GRAPHQL_PORT, debug=True, use_reloader=False))
        thread.start()

        # updateState(newState, settingsSaved = None (timestamp), settingsImported = None (timestamp), showSpinner = False (1/0), graphQLServerStarted = False (1/0))
        # update GraphQL = started
        state = updateState("Process: Wait", None, None, None, 1) 

