import json


# Register NetAlertX modules 
import conf  
from const import (apiPath, sql_appevents, sql_devices_all, sql_events_pending_alert, sql_settings, sql_plugins_events, sql_plugins_history, sql_plugins_objects,sql_language_strings, sql_notifications_all, sql_online_history, sql_devices_tiles)
from logger import mylog
from helper import write_file, get_setting_value, updateState

# Import the start_server function
from graphql_server.graphql_server_start import start_server 

apiEndpoints = []

#===============================================================================
# API
#===============================================================================
def update_api(db, all_plugins, isNotification = False, updateOnlyDataSources = []):
    mylog('debug', ['[API] Update API starting'])

    # update app_state.json and retrieve app_state to chjeck if GraphQL server is running
    app_state = updateState("Update: API", None, None, None, None)
    
    folder = apiPath 

    # Save plugins    
    write_file(folder + 'plugins.json'  , json.dumps({"data" : all_plugins}))  

    #  prepare database tables we want to expose 
    dataSourcesSQLs = [
        ["appevents", sql_appevents],        
        ["devices", sql_devices_all],        
        ["events_pending_alert", sql_events_pending_alert],
        ["settings", sql_settings],
        ["plugins_events", sql_plugins_events],
        ["plugins_history", sql_plugins_history],
        ["plugins_objects", sql_plugins_objects],
        ["plugins_language_strings", sql_language_strings],
        ["notifications", sql_notifications_all],
        ["online_history", sql_online_history],
        ["devices_tiles", sql_devices_tiles],
        ["custom_endpoint", conf.API_CUSTOM_SQL],
    ]

    # Save selected database tables
    for dsSQL in dataSourcesSQLs:

        if updateOnlyDataSources == [] or dsSQL[0] in updateOnlyDataSources:

            api_endpoint_class(db, dsSQL[1], folder + 'table_' + dsSQL[0] + '.json')
            
    # Start the GraphQL server
    graphql_port_value = get_setting_value("GRAPHQL_PORT")
    api_token_value = get_setting_value("API_TOKEN")

    # start GraphQL server if not yet running
    if app_state.graphQLServerStarted == 0:
        # Validate if settings are available
        if graphql_port_value is not None and len(api_token_value) > 1:
            try:
                graphql_port_value = int(graphql_port_value)  # Ensure port is an integer
                start_server(graphql_port_value, app_state)  # Start the server
            except ValueError:
                mylog('none', [f"[API] Invalid GRAPHQL_PORT value, must be an integer: {graphql_port_value}"])
        else:
            mylog('none', [f"[API] GRAPHQL_PORT or API_TOKEN is not set, will try later."])


#-------------------------------------------------------------------------------


class api_endpoint_class:
    def __init__(self, db, query, path):        

        global apiEndpoints
        self.db = db
        self.query = query
        self.jsonData = db.get_table_as_json(self.query).json
        self.path = path
        self.fileName = path.split('/')[-1]
        self.hash = hash(json.dumps(self.jsonData))

        # check if the endpoint needs to be updated
        found = False
        changed = False
        changedIndex = -1
        index = 0
        
        # search previous endpoint states to check if API needs updating
        for endpoint in apiEndpoints:
            # match sql and API endpoint path 
            if endpoint.query == self.query and endpoint.path == self.path:
                found = True 
                if endpoint.hash != self.hash:                    
                    changed = True
                    changedIndex = index

            index = index + 1
        
        # check if API endpoints have changed or if it's a new one
        if not found or changed:

            mylog('verbose', [f'[API] Updating {self.fileName} file in /api'])

            write_file(self.path, json.dumps(self.jsonData)) 
            
            if not found:
                apiEndpoints.append(self)

            elif changed and changedIndex != -1 and changedIndex < len(apiEndpoints):
                # update hash
                apiEndpoints[changedIndex].hash = self.hash
            else:
                mylog('minimal', [f'[API] ⚠ ERROR Updating {self.fileName}'])
            
