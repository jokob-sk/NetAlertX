import json


# pialert modules
import conf  
from const import pialertPath
from logger import mylog
from files import write_file
from database import *

apiEndpoints = []

#===============================================================================
# API
#===============================================================================
def update_api(isNotification = False, updateOnlyDataSources = []):
    mylog('verbose', ['     [API] Update API not doing anything for now !'])
    return

    folder = pialertPath + '/front/api/'

    if isNotification:
        #  Update last notification alert in all formats
        mylog('verbose', ['     [API] Updating notification_* files in /front/api'])

        write_file(folder + 'notification_text.txt'  , mail_text)
        write_file(folder + 'notification_text.html'  , mail_html)
        write_file(folder + 'notification_json_final.json'  , json.dumps(json_final))  

    # Save plugins
    if conf.ENABLE_PLUGINS: 
        write_file(folder + 'plugins.json'  , json.dumps({"data" : plugins}))  

    #  prepare database tables we want to expose 
    dataSourcesSQLs = [
        ["devices", sql_devices_all],
        ["nmap_scan", sql_nmap_scan_all],
        ["pholus_scan", sql_pholus_scan_all],
        ["events_pending_alert", sql_events_pending_alert],
        ["settings", sql_settings],
        ["plugins_events", sql_plugins_events],
        ["plugins_history", sql_plugins_history],
        ["plugins_objects", sql_plugins_objects],
        ["language_strings", sql_language_strings],
        ["custom_endpoint", conf.API_CUSTOM_SQL],
    ]

    # Save selected database tables
    for dsSQL in dataSourcesSQLs:

        if updateOnlyDataSources == [] or dsSQL[0] in updateOnlyDataSources:

            api_endpoint_class(dsSQL[1], folder + 'table_' + dsSQL[0] + '.json')


#-------------------------------------------------------------------------------


class api_endpoint_class:
    def __init__(self, db, path):        

        global apiEndpoints
        self.db = db
        self.sql = db.sql
        self.jsonData = db.get_table_as_json( self.sql).json
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
            if endpoint.sql == self.sql and endpoint.path == self.path:
                found = True 
                if endpoint.hash != self.hash:                    
                    changed = True
                    changedIndex = index

            index = index + 1
        
        # cehck if API endpoints have changed or if it's a new one
        if not found or changed:

            mylog('verbose', [f'     [API] Updating {self.fileName} file in /front/api'])

            write_file(self.path, json.dumps(self.jsonData)) 
            
            if not found:
                apiEndpoints.append(self)

            elif changed and changedIndex != -1 and changedIndex < len(apiEndpoints):
                # update hash
                apiEndpoints[changedIndex].hash = self.hash
            else:
                mylog('info', [f'     [API] ERROR Updating {self.fileName}'])
            
