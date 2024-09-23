import os
import sqlite3
import json
import subprocess
import datetime
import base64

from collections import namedtuple

# Register NetAlertX modules
import conf
from const import pluginsPath, logPath, applicationPath, reportTemplatesPath
from logger import mylog
from helper import timeNowTZ,  updateState, get_file_content, write_file, get_setting, get_setting_value
from api import update_api
from plugin_utils import logEventStatusCounts, get_plugin_string, get_plugin_setting_obj, print_plugin_info, list_to_csv, combine_plugin_objects, resolve_wildcards_arr, handle_empty, custom_plugin_decoder, decode_and_rename_files
from notification import Notification_obj, write_notification


#-------------------------------------------------------------------------------
class plugin_param:
    def __init__(self, param, plugin, db):

        mylog('debug', f'[Plugins] Resolving param: {param}')

        paramValuesCount = 1

        #  Get setting value
        if param["type"] == "setting":
            inputValue = get_setting(param["value"])

            if inputValue != None:
                setVal = inputValue["Value"] # setting value
                setTyp = inputValue["Type"]  # setting type

                setTypJSN = json.loads(setTyp.replace('"','\"').replace("'",'"'))

                mylog('debug', f'[Plugins] setTyp: {setTyp}')
                mylog('debug', f'[Plugins] setTypJSN: {setTypJSN}')

                dataType  = setTypJSN["dataType"]

                mylog('debug', f'[Plugins] dType: {dataType}')


                if dataType  == 'array':
                    # store number of returned values
                    paramValuesCount = len(setVal)

                if dataType in ['string','integer', 'boolean']:
                    resolved =  setVal
                
                elif dataType == 'array':
                    #  make them safely passable to a python or linux script
                    resolved =  list_to_csv(setVal)

                else:
                    mylog('none', ['[Plugins] ⚠ ERROR: Parameter probably not converted.'])  
                    return json.dumps(setVal)

        #  Get SQL result
        if param["type"] == "sql":
            inputValue = db.get_sql_array(param["value"])

            # store number of returned values
            paramValuesCount = len(inputValue)

            #  make them safely passable to a python or linux script
            resolved = list_to_csv(inputValue)

        
        mylog('debug', f'[Plugins] Resolved value: {resolved}')

        #  Handle timeout multiplier if script executes multiple time
        multiplyTimeout = False
        if 'timeoutMultiplier' in param and param['timeoutMultiplier']:
            multiplyTimeout = True

        #  Handle base64 encoding
        encodeToBase64 = False
        if 'base64' in param and param['base64']:
            encodeToBase64 = True


        mylog('debug', f'[Plugins] Convert to Base64: {encodeToBase64}')
        if encodeToBase64:
            resolved = str(base64.b64encode(resolved.encode('ascii')))
            mylog('debug', f'[Plugins] base64 value: {resolved}')


        self.resolved   = resolved        
        self.inputValue = inputValue        
        self.base64     = encodeToBase64                
        self.name       = param["name"]
        self.type       = param["type"]
        self.value      = param["value"]
        self.paramValuesCount       = paramValuesCount    
        self.multiplyTimeout        = multiplyTimeout    

#-------------------------------------------------------------------------------
class plugins_state:
    def __init__(self, processScan = False):
        self.processScan        = processScan

#-------------------------------------------------------------------------------
def run_plugin_scripts(db, all_plugins, runType, pluginsState = plugins_state()):

    # Header
    updateState("Run: Plugins")

    mylog('debug', ['[Plugins] Check if any plugins need to be executed on run type: ', runType])

    for plugin in all_plugins:

        shouldRun = False        
        prefix = plugin["unique_prefix"]

        set = get_plugin_setting_obj(plugin, "RUN")
        if set != None and set['value'] == runType:
            if runType != "schedule":
                shouldRun = True
            elif  runType == "schedule":
                # run if overdue scheduled time   
                # check schedules if any contains a unique plugin prefix matching the current plugin
                for schd in conf.mySchedules:
                    if schd.service == prefix:          
                        # Check if schedule overdue
                        shouldRun = schd.runScheduleCheck()  

        if shouldRun:            
            # Header
            updateState(f"Plugins: {prefix}")
                        
            print_plugin_info(plugin, ['display_name'])
            mylog('debug', ['[Plugins] CMD: ', get_plugin_setting_obj(plugin, "CMD")["value"]])
            pluginsState = execute_plugin(db, all_plugins, plugin, pluginsState) 
            #  update last run time
            if runType == "schedule":
                for schd in conf.mySchedules:
                    if schd.service == prefix:          
                        # note the last time the scheduled plugin run was executed
                        schd.last_run = timeNowTZ()

    return pluginsState




#-------------------------------------------------------------------------------
# Executes the plugin command specified in the setting with the function specified as CMD 
def execute_plugin(db, all_plugins, plugin, pluginsState = plugins_state() ):
    sql = db.sql  


    if pluginsState is None:
        mylog('debug', ['[Plugins] pluginsState is None'])   
        pluginsState = plugins_state()

    # ------- necessary settings check  --------
    set = get_plugin_setting_obj(plugin, "CMD")

    #  handle missing "function":"CMD" setting
    if set == None:                
        return pluginsState

    set_CMD = set["value"]

    set = get_plugin_setting_obj(plugin, "RUN_TIMEOUT")

    #  handle missing "function":"<unique_prefix>_TIMEOUT" setting
    if set == None:   
        set_RUN_TIMEOUT = 10
    else:     
        set_RUN_TIMEOUT = set["value"]         

    #  Prepare custom params    
    params = []

    if "params" in plugin:
        for param in plugin["params"]:     

            tempParam = plugin_param(param, plugin, db)

            if tempParam.resolved == None:
                mylog('none', [f'[Plugins] The parameter "name":"{tempParam.name}" for "value": {tempParam.value} was resolved as None'])

            else:
                # params.append( [param["name"], resolved] )
                params.append( [tempParam.name, tempParam.resolved] )

                if tempParam.multiplyTimeout:
                    
                    set_RUN_TIMEOUT = set_RUN_TIMEOUT*tempParam.paramValuesCount

                    mylog('debug', [f'[Plugins] The parameter "name":"{param["name"]}" will multiply the timeout {tempParam.paramValuesCount} times. Total timeout: {set_RUN_TIMEOUT}s'])
    
    mylog('debug', ['[Plugins] Timeout: ', set_RUN_TIMEOUT]) 
    
    # build SQL query parameters to insert into the DB
    sqlParams = []

    # script 
    if plugin['data_source'] == 'script':
        # ------- prepare params --------
        # prepare command from plugin settings, custom parameters  
        command = resolve_wildcards_arr(set_CMD.split(), params)        

        # Execute command
        mylog('verbose', ['[Plugins] Executing: ', set_CMD])
        mylog('debug',   ['[Plugins] Resolved : ', command])        

        try:
            # try running a subprocess with a forced timeout in case the subprocess hangs
            output = subprocess.check_output(command, universal_newlines=True, stderr=subprocess.STDOUT, timeout=(set_RUN_TIMEOUT))
        except subprocess.CalledProcessError as e:
            # An error occurred, handle it
            mylog('none', [e.output])
            mylog('none', ['[Plugins] ⚠ ERROR - enable LOG_LEVEL=debug and check logs'])            
        except subprocess.TimeoutExpired as timeErr:
            mylog('none', [f'[Plugins] ⚠ ERROR - TIMEOUT - the plugin {plugin["unique_prefix"]} forcefully terminated as timeout reached. Increase TIMEOUT setting and scan interval.']) 

        # Initialize newLines
        newLines = []

        # Create the file path
        file_dir = os.path.join(pluginsPath, plugin["code_name"])
        file_prefix = 'last_result'

        # Decode files, rename them, and get the list of files
        files_to_process = decode_and_rename_files(file_dir, file_prefix)

        for filename in files_to_process:

            full_path = os.path.join(file_dir, filename)

            # Open the decrypted file and process its contents
            with open(full_path, 'r') as f:
                newLines = f.read().split('\n')

                # if the script produced some output, clean it up to ensure it's the correct format        
                # cleanup - select only lines containing a separator to filter out unnecessary data
                newLines = list(filter(lambda x: '|' in x, newLines))    

                # Store e.g. Node_1 from last_result.encoded.Node_1.1.log
                tmp_SyncHubNodeName = ''
                if len(filename.split('.')) > 3:
                    tmp_SyncHubNodeName = filename.split('.')[2]   
            
                for line in newLines:
                    columns = line.split("|")
                    # There have to be 9 or 13 columns 
                    if len(columns) not in [9, 13]:
                        mylog('none', [f'[Plugins] Wrong number of input values, must be 9 or 13, got {len(columns)} from: {line}'])
                        continue  # Skip lines with incorrect number of columns
                    
                    # Common part of the SQL parameters
                    base_params = [
                        0,                          # "Index" placeholder
                        plugin["unique_prefix"],    # "Plugin" column value from the plugin dictionary
                        columns[0],                 # "Object_PrimaryID" value from columns list
                        columns[1],                 # "Object_SecondaryID" value from columns list
                        'null',                     # Placeholder for "DateTimeCreated" column
                        columns[2],                 # "DateTimeChanged" value from columns list
                        columns[3],                 # "Watched_Value1" value from columns list
                        columns[4],                 # "Watched_Value2" value from columns list
                        columns[5],                 # "Watched_Value3" value from columns list
                        columns[6],                 # "Watched_Value4" value from columns list
                        'not-processed',            # "Status" column (placeholder)
                        columns[7],                 # "Extra" value from columns list
                        'null',                     # Placeholder for "UserData" column
                        columns[8],                 # "ForeignKey" value from columns list
                        tmp_SyncHubNodeName         # Sync Hub Node name
                    ]
                    
                    # Extend the common part with the additional values if there are 13 columns
                    if len(columns) == 13:
                        base_params.extend([
                            columns[9],                 # "HelpVal1" value from columns list
                            columns[10],                # "HelpVal2" value from columns list
                            columns[11],                # "HelpVal3" value from columns list
                            columns[12]                 # "HelpVal4" value from columns list
                        ])
                    elif len(columns) == 9:                                        
                        # add padding
                        base_params.extend([
                            'null',   # "HelpVal1"
                            'null',   # "HelpVal2"
                            'null',   # "HelpVal3"
                            'null'    # "HelpVal4"
                        ])
                        
                    # Create a tuple containing values to be inserted into the database.
                    # Each value corresponds to a column in the table in the order of the columns.
                    # must match the Plugins_Objects and Plugins_Events database tables and can be used as input for the plugin_object_class.
                    
                    # Append the final parameters to sqlParams
                    sqlParams.append(tuple(base_params))     
            
            # keep current instance log file, delete all from other nodes
            if filename != 'last_result.log' and os.path.exists(full_path):
                os.remove(full_path)
                mylog('verbose', [f'[Plugins] Processed and deleted file: {full_path} '])   

    
    # app-db-query
    if plugin['data_source'] == 'app-db-query':
        # replace single quotes wildcards
        q = set_CMD.replace("{s-quote}", '\'')

        # Execute command
        mylog('verbose', ['[Plugins] Executing: ', q])

        # set_CMD should contain a SQL query        
        arr = db.get_sql_array (q) 

        for row in arr:
            # There has to be always 9 or 13 columns
            if len(row) in [9, 13] and row[0] not in ['', 'null']:
                # Create a base tuple containing values to be inserted into the database.
                # Each value corresponds to a column in the table in the order of the columns.
                # Must match the Plugins_Objects and Plugins_Events database tables and can be used as input for the plugin_object_class.
                base_params = [
                    0,                          # "Index" placeholder
                    plugin["unique_prefix"],    # "Plugin" plugin dictionary
                    row[0],                     # "Object_PrimaryID" row
                    handle_empty(row[1]),       # "Object_SecondaryID" column after handling empty values
                    'null',                     # Placeholder "DateTimeCreated" column
                    row[2],                     # "DateTimeChanged" row
                    row[3],                     # "Watched_Value1" row
                    row[4],                     # "Watched_Value2" row
                    handle_empty(row[5]),       # "Watched_Value3" column after handling empty values
                    handle_empty(row[6]),       # "Watched_Value4" column after handling empty values
                    'not-processed',            # "Status" column (placeholder)
                    row[7],                     # "Extra" row
                    'null',                     # Placeholder "UserData" column
                    row[8],                     # "ForeignKey" row
                    'null'                      # Sync Hub Node name - Only supported with scripts
                ]

                # Extend the base tuple with additional values if there are 13 columns
                if len(row) == 13:
                    base_params.extend([
                        row[9],   # "HelpVal1" row
                        row[10],  # "HelpVal2" row
                        row[11],  # "HelpVal3" row
                        row[12]   # "HelpVal4" row
                    ])
                else:
                    # add padding
                    base_params.extend([
                        'null',   # "HelpVal1"
                        'null',   # "HelpVal2"
                        'null',   # "HelpVal3"
                        'null'    # "HelpVal4"
                    ])

                # Append the final parameters to sqlParams
                sqlParams.append(tuple(base_params))
            else:
                mylog('none', ['[Plugins] Skipped invalid sql result'])
    
    # app-db-query
    if plugin['data_source'] == 'sqlite-db-query':
        # replace single quotes wildcards
        # set_CMD should contain a SQL query    
        q = set_CMD.replace("{s-quote}", '\'')

        # Execute command
        mylog('verbose', ['[Plugins] Executing: ', q])

        # ------- necessary settings check  --------
        set = get_plugin_setting_obj(plugin, "DB_PATH")

        #  handle missing "function":"DB_PATH" setting
        if set == None:                
            mylog('none', ['[Plugins] ⚠ ERROR: DB_PATH setting for plugin type sqlite-db-query missing.'])
            return pluginsState
        
        fullSqlitePath = set["value"]


        #  try attaching the sqlite DB
        try:
            sql.execute ("ATTACH DATABASE '"+ fullSqlitePath +"' AS EXTERNAL_"+plugin["unique_prefix"])
            arr = db.get_sql_array (q) 
            sql.execute ("DETACH DATABASE EXTERNAL_"+plugin["unique_prefix"])
             
        except sqlite3.Error as e:            
            mylog('none',[f'[Plugins] ⚠ ERROR: DB_PATH setting ({fullSqlitePath}) for plugin {plugin["unique_prefix"]}. Did you mount it correctly?'])
            mylog('none',[f'[Plugins] ⚠ ERROR: ATTACH DATABASE failed with SQL ERROR: ', e])
            return pluginsState            

        for row in arr:
            # There has to be always 9 or 13 columns
            if len(row) in [9, 13] and row[0] not in ['', 'null']:
                # Create a base tuple containing values to be inserted into the database.
                # Each value corresponds to a column in the table in the order of the columns.
                # Must match the Plugins_Objects and Plugins_Events database tables and can be used as input for the plugin_object_class.
                base_params = [
                    0,                            # "Index" placeholder
                    plugin["unique_prefix"],      # "Plugin" 
                    row[0],                       # "Object_PrimaryID" 
                    handle_empty(row[1]),         # "Object_SecondaryID" 
                    'null',                       # "DateTimeCreated" column (null placeholder)
                    row[2],                       # "DateTimeChanged" 
                    row[3],                       # "Watched_Value1" 
                    row[4],                       # "Watched_Value2" 
                    handle_empty(row[5]),         # "Watched_Value3" 
                    handle_empty(row[6]),         # "Watched_Value4" 
                    'not-processed',              # "Status" column (placeholder)
                    row[7],                       # "Extra" 
                    'null',                       # "UserData" column (null placeholder)
                    row[8],                       # "ForeignKey" 
                    'null'                        # Sync Hub Node name - Only supported with scripts
                ]

                # Extend the base tuple with additional values if there are 13 columns
                if len(row) == 13:
                    base_params.extend([
                        row[9],    # "HelpVal1"
                        row[10],   # "HelpVal2"
                        row[11],   # "HelpVal3"
                        row[12]    # "HelpVal4"
                    ])
                else:
                    # add padding
                    base_params.extend([
                        'null',   # "HelpVal1"
                        'null',   # "HelpVal2"
                        'null',   # "HelpVal3"
                        'null'    # "HelpVal4"
                    ])

                # Append the final parameters to sqlParams
                sqlParams.append(tuple(base_params))
            else:
                mylog('none', ['[Plugins] Skipped invalid sql result'])

    
    # check if the subprocess / SQL query failed / there was no valid output
    if len(sqlParams) == 0: 
        mylog('none', ['[Plugins] No output received from the plugin ', plugin["unique_prefix"], ' - enable LOG_LEVEL=debug and check logs'])
        return pluginsState 
    else: 
        mylog('verbose', ['[Plugins] SUCCESS, received ', len(sqlParams), ' entries'])  
        mylog('debug',   ['[Plugins] sqlParam entries: ', sqlParams])

    # process results if any
    if len(sqlParams) > 0:               

        # create objects
        pluginsState = process_plugin_events(db, plugin, pluginsState, sqlParams)

        # update API endpoints
        update_api(db, all_plugins, False, ["plugins_events","plugins_objects", "plugins_history", "appevents"])  
    
    return pluginsState


#-------------------------------------------------------------------------------
# Check if watched values changed for the given plugin
def process_plugin_events(db, plugin, pluginsState, plugEventsArr):    
      
    sql = db.sql

    # Access the connection from the DB instance
    conn = db.sql_connection

    pluginPref = plugin["unique_prefix"]

    mylog('debug', ['[Plugins] Processing        : ', pluginPref])

    try:
        # Begin a transaction
        with conn:

            pluginObjects = []
            pluginEvents  = []

            #  Create plugin objects from existing database entries
            plugObjectsArr = db.get_sql_array ("SELECT * FROM Plugins_Objects where Plugin = '" + str(pluginPref)+"'") 

            for obj in plugObjectsArr: 
                pluginObjects.append(plugin_object_class(plugin, obj))

           
            # create plugin objects from events - will be processed to find existing objects 
            for eve in plugEventsArr:                                  
                pluginEvents.append(plugin_object_class(plugin, eve))


            mylog('debug', ['[Plugins] Existing objects from Plugins_Objects: ', len(pluginObjects)])
            mylog('debug', ['[Plugins] Logged events from the plugin run    : ', len(pluginEvents)])

            
            #  Loop thru all current events and update the status to "exists" if the event matches an existing object
            index = 0
            for tmpObjFromEvent in pluginEvents:        

                #  compare hash of the IDs for uniqueness
                if any(x.idsHash == tmpObjFromEvent.idsHash for x in pluginObjects):                    
            
                    pluginEvents[index].status = "exists"            
                index += 1


            # Loop thru events and check if the ones that exist have changed in the watched columns
            # if yes update status accordingly
            index = 0
            for tmpObjFromEvent in pluginEvents:  

                if tmpObjFromEvent.status == "exists": 

                    #  compare hash of the changed watched columns for uniqueness
                    if any(x.watchedHash != tmpObjFromEvent.watchedHash for x in pluginObjects):
                        pluginEvents[index].status = "watched-changed"                            
                    else:
                        pluginEvents[index].status = "watched-not-changed"  
                index += 1

            # Loop thru events and check if previously available objects are missing
            for tmpObj in pluginObjects:
                
                isMissing = True

                for tmpObjFromEvent in pluginEvents:
                    if tmpObj.idsHash == tmpObjFromEvent.idsHash:
                        isMissing = False

                if isMissing:
                    # if wasn't missing before, mark as changed
                    if tmpObj.status != "missing-in-last-scan":
                        tmpObj.changed = timeNowTZ().strftime('%Y-%m-%d %H:%M:%S')
                        tmpObj.status = "missing-in-last-scan"                    
                    # mylog('debug', [f'[Plugins] Missing from last scan (PrimaryID | SecondaryID): {tmpObj.primaryId} | {tmpObj.secondaryId}'])


            # Merge existing plugin objects with newly discovered ones and update existing ones with new values
            for tmpObjFromEvent in pluginEvents:
                # set "new" status for new objects and append
                if tmpObjFromEvent.status == 'not-processed':
                    # This is a new object as it was not discovered as "exists" previously                    
                    tmpObjFromEvent.status = 'new'

                    pluginObjects.append(tmpObjFromEvent)
                # update data of existing objects
                else:
                    index = 0
                    for plugObj in pluginObjects:
                        # find corresponding object for the event and merge
                        if plugObj.idsHash == tmpObjFromEvent.idsHash:               
                            pluginObjects[index] =  combine_plugin_objects(plugObj, tmpObjFromEvent)                    

                        index += 1

            # Update the DB
            # ----------------------------
            # Update the Plugin_Objects    
            # Create lists to hold the data for bulk insertion
            objects_to_insert = []
            events_to_insert = []
            history_to_insert = []
            objects_to_update = []

            # only generate events that we want to be notified on (we only need to do this once as all plugObj have the same prefix)
            statuses_to_report_on = get_setting_value(pluginPref + "_REPORT_ON")  
            
            for plugObj in pluginObjects:
                #  keep old createdTime time if the plugObj already was created before
                createdTime = plugObj.changed if plugObj.status == 'new' else plugObj.created
                #  18 values without Index
                values = (
                    plugObj.pluginPref, plugObj.primaryId, plugObj.secondaryId, createdTime,
                    plugObj.changed, plugObj.watched1, plugObj.watched2, plugObj.watched3,
                    plugObj.watched4, plugObj.status, plugObj.extra, plugObj.userData,
                    plugObj.foreignKey, plugObj.syncHubNodeName,
                    plugObj.helpVal1, plugObj.helpVal2, plugObj.helpVal3, plugObj.helpVal4
                )

                if plugObj.status == 'new':
                    objects_to_insert.append(values)
                else:
                    objects_to_update.append(values + (plugObj.index,))  # Include index for UPDATE              
                
                if plugObj.status in statuses_to_report_on:
                    events_to_insert.append(values)

                # combine all DB insert and update events into one for history
                history_to_insert.append(values)

            
            mylog('debug', ['[Plugins] pluginEvents      count: ', len(pluginEvents)])
            mylog('debug', ['[Plugins] pluginObjects     count: ', len(pluginObjects)])

            mylog('debug', ['[Plugins] events_to_insert  count: ', len(events_to_insert)])
            mylog('debug', ['[Plugins] history_to_insert count: ', len(history_to_insert)])
            mylog('debug', ['[Plugins] objects_to_insert count: ', len(objects_to_insert)])
            mylog('debug', ['[Plugins] objects_to_update count: ', len(objects_to_update)])

            logEventStatusCounts('pluginEvents', pluginEvents)
            logEventStatusCounts('pluginObjects', pluginObjects)

            # Bulk insert objects
            if objects_to_insert:
                sql.executemany(
                    """
                    INSERT INTO Plugins_Objects 
                    ("Plugin", "Object_PrimaryID", "Object_SecondaryID", "DateTimeCreated", 
                    "DateTimeChanged", "Watched_Value1", "Watched_Value2", "Watched_Value3", 
                    "Watched_Value4", "Status", "Extra", "UserData", "ForeignKey", "SyncHubNodeName",
                    "HelpVal1", "HelpVal2", "HelpVal3", "HelpVal4") 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, objects_to_insert
                )

            # Bulk update objects
            if objects_to_update:
                sql.executemany(
                    """
                    UPDATE Plugins_Objects
                    SET "Plugin" = ?, "Object_PrimaryID" = ?, "Object_SecondaryID" = ?, "DateTimeCreated" = ?, 
                        "DateTimeChanged" = ?, "Watched_Value1" = ?, "Watched_Value2" = ?, "Watched_Value3" = ?, 
                        "Watched_Value4" = ?, "Status" = ?, "Extra" = ?, "UserData" = ?, "ForeignKey" = ?, "SyncHubNodeName" = ?, "HelpVal1" = ?, "HelpVal2" = ?, "HelpVal3" = ?, "HelpVal4" = ?
                    WHERE "Index" = ?
                    """, objects_to_update
                )

            # Bulk insert events
            if events_to_insert:

                sql.executemany(
                    """
                    INSERT INTO Plugins_Events 
                    ("Plugin", "Object_PrimaryID", "Object_SecondaryID", "DateTimeCreated", 
                    "DateTimeChanged", "Watched_Value1", "Watched_Value2", "Watched_Value3", 
                    "Watched_Value4", "Status", "Extra", "UserData", "ForeignKey", "SyncHubNodeName",
                    "HelpVal1", "HelpVal2", "HelpVal3", "HelpVal4")  
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, events_to_insert
                )

            # Bulk insert history entries
            if history_to_insert:

                sql.executemany(
                    """
                    INSERT INTO Plugins_History 
                    ("Plugin", "Object_PrimaryID", "Object_SecondaryID", "DateTimeCreated", 
                    "DateTimeChanged", "Watched_Value1", "Watched_Value2", "Watched_Value3", 
                    "Watched_Value4", "Status", "Extra", "UserData", "ForeignKey", "SyncHubNodeName",
                    "HelpVal1", "HelpVal2", "HelpVal3", "HelpVal4")  
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, history_to_insert
                )

            # Commit changes to the database
            db.commitDB()



    except Exception as e:
        # Rollback the transaction in case of an error
        conn.rollback()
        mylog('none', ['[Plugins] ⚠ ERROR: ', e])
        raise e   

    # Perform database table mapping if enabled for the plugin
    if len(pluginEvents) > 0 and "mapped_to_table" in plugin:

        # Initialize an empty list to store SQL parameters.
        sqlParams = []

        # Get the database table name from the 'mapped_to_table' key in the 'plugin' dictionary.
        dbTable = plugin['mapped_to_table']

        # Log a debug message indicating the mapping of objects to the database table.
        mylog('debug', ['[Plugins] Mapping objects to database table: ', dbTable])

        # Initialize lists to hold mapped column names, columnsStr, and valuesStr for SQL query.
        mappedCols = []
        columnsStr = ''
        valuesStr = ''

        # Loop through the 'database_column_definitions' in the 'plugin' dictionary to collect mapped columns.
        # Build the columnsStr and valuesStr for the SQL query.
        for clmn in plugin['database_column_definitions']:
            if 'mapped_to_column' in clmn:
                mappedCols.append(clmn)

                columnsStr = f'{columnsStr}, "{clmn["mapped_to_column"]}"'
                valuesStr = f'{valuesStr}, ?'

        # Remove the first ',' from columnsStr and valuesStr.
        if len(columnsStr) > 0:
            columnsStr = columnsStr[1:]
            valuesStr = valuesStr[1:]

        # Map the column names to plugin object event values and create a list of tuples 'sqlParams'.
        for plgEv in pluginEvents:
            tmpList = []

            for col in mappedCols:
                if col['column'] == 'Index':
                    tmpList.append(plgEv.index)
                elif col['column'] == 'Plugin':
                    tmpList.append(plgEv.pluginPref)
                elif col['column'] == 'Object_PrimaryID':
                    tmpList.append(plgEv.primaryId)
                elif col['column'] == 'Object_SecondaryID':
                    tmpList.append(plgEv.secondaryId)
                elif col['column'] == 'DateTimeCreated':
                    tmpList.append(plgEv.created)
                elif col['column'] == 'DateTimeChanged':
                    tmpList.append(plgEv.changed)
                elif col['column'] == 'Watched_Value1':
                    tmpList.append(plgEv.watched1)
                elif col['column'] == 'Watched_Value2':
                    tmpList.append(plgEv.watched2)
                elif col['column'] == 'Watched_Value3':
                    tmpList.append(plgEv.watched3)
                elif col['column'] == 'Watched_Value4':
                    tmpList.append(plgEv.watched4)
                elif col['column'] == 'UserData':
                    tmpList.append(plgEv.userData)
                elif col['column'] == 'Extra':
                    tmpList.append(plgEv.extra)
                elif col['column'] == 'Status':
                    tmpList.append(plgEv.status)
                elif col['column'] == 'SyncHubNodeName':
                    tmpList.append(plgEv.syncHubNodeName)
                elif col['column'] == 'HelpVal1':
                    tmpList.append(plgEv.helpVal1)
                elif col['column'] == 'HelpVal2':
                    tmpList.append(plgEv.helpVal2)
                elif col['column'] == 'HelpVal3':
                    tmpList.append(plgEv.helpVal3)
                elif col['column'] == 'HelpVal4':
                    tmpList.append(plgEv.helpVal4)

                # Check if there's a default value specified for this column in the JSON.
                if 'mapped_to_column_data' in col and 'value' in col['mapped_to_column_data']:
                    tmpList.append(col['mapped_to_column_data']['value'])
                
            # Append the mapped values to the list 'sqlParams' as a tuple.
            sqlParams.append(tuple(tmpList))

        # Generate the SQL INSERT query using the collected information.
        q = f'INSERT into {dbTable} ({columnsStr}) VALUES ({valuesStr})'

        # Log a debug message showing the generated SQL query for mapping.
        mylog('debug', ['[Plugins] SQL query for mapping: ', q])
        mylog('debug', ['[Plugins] SQL sqlParams for mapping: ', sqlParams])

        # Execute the SQL query using 'sql.executemany()' and the 'sqlParams' list of tuples.
        # This will insert multiple rows into the database in one go.
        sql.executemany(q, sqlParams)

        db.commitDB()

        # perform scan if mapped to CurrentScan table
        if dbTable == 'CurrentScan':
            pluginsState.processScan = True

    db.commitDB()


    return pluginsState


#-------------------------------------------------------------------------------
class plugin_object_class:
    def __init__(self, plugin, objDbRow):
        self.index             = objDbRow[0]
        self.pluginPref        = objDbRow[1]
        self.primaryId         = objDbRow[2]
        self.secondaryId       = objDbRow[3]
        self.created           = objDbRow[4] # can be null
        self.changed           = objDbRow[5] # never null (data coming from plugin)
        self.watched1          = objDbRow[6]
        self.watched2          = objDbRow[7]
        self.watched3          = objDbRow[8]
        self.watched4          = objDbRow[9]
        self.status            = objDbRow[10]
        self.extra             = objDbRow[11]
        self.userData          = objDbRow[12]
        self.foreignKey        = objDbRow[13]
        self.syncHubNodeName   = objDbRow[14]
        self.helpVal1          = objDbRow[15]
        self.helpVal2          = objDbRow[16]
        self.helpVal3          = objDbRow[17]
        self.helpVal4          = objDbRow[18]


        # Check if self.status is valid
        if self.status not in ["exists", "watched-changed", "watched-not-changed", "new", "not-processed", "missing-in-last-scan"]:
            raise ValueError("Invalid status value for plugin object:", self.status)

        self.idsHash      = str(hash(str(self.primaryId) + str(self.secondaryId)))    
        # self.idsHash      = str(self.primaryId) + str(self.secondaryId)

        self.watchedClmns = []
        self.watchedIndxs = []          

        setObj = get_plugin_setting_obj(plugin, 'WATCH')

        # hash for comapring watched value changes
        indexNameColumnMapping = [(6, 'Watched_Value1' ), (7, 'Watched_Value2' ), (8, 'Watched_Value3' ), (9, 'Watched_Value4' )]

        if setObj is not None:            
            
            self.watchedClmns = setObj["value"]

            for clmName in self.watchedClmns:
                for mapping in indexNameColumnMapping:
                    if clmName == indexNameColumnMapping[1]:
                        self.watchedIndxs.append(indexNameColumnMapping[0])

        tmp = ''
        for indx in self.watchedIndxs:
            tmp += str(objDbRow[indx])

        self.watchedHash  = str(hash(tmp))


#===============================================================================
# Handling of  user initialized front-end events
#===============================================================================
def check_and_run_user_event(db, all_plugins, pluginsState):
    # Check if the log file exists
    logFile = os.path.join(logPath, "execution_queue.log")

    # Track if not an API event and list of executed events
    show_events_completed = False
    executed_events = []

    if not os.path.exists(logFile):
        return pluginsState

    with open(logFile, "r") as file:
        lines = file.readlines()

    remaining_lines = []

    for line in lines:
        # Split the line by '|', and take the third and fourth columns (indices 2 and 3)
        columns = line.strip().split('|')[2:4]

        event, param = "", ""
        if len(columns) == 2:
            event, param = columns

        if event == 'test':
            show_events_completed = True
            pluginsState = handle_test(param, db, all_plugins, pluginsState)
            executed_events.append(f"test with param {param}")
        elif event == 'run':
            show_events_completed = True
            pluginsState = handle_run(param, db, all_plugins, pluginsState)
            executed_events.append(f"run with param {param}")
        elif event == 'update_api':
            # Update API endpoints
            update_api(db, all_plugins, False, param.split(','))
            executed_events.append(f"update_api with param {param}")
        else:
            remaining_lines.append(line)

    # Rewrite the log file with remaining lines
    with open(logFile, "w") as file:
        file.writelines(remaining_lines)

    # Only show pop-up if not an API event
    if show_events_completed:
        executed_events_message = ', '.join(executed_events)
        write_notification(f'[Ad-hoc events] Events executed: {executed_events_message}', 'interrupt', timeNowTZ())

    return pluginsState


#-------------------------------------------------------------------------------
def handle_run(runType, db, all_plugins, pluginsState):
    
    mylog('minimal', ['[', timeNowTZ(), '] START Run: ', runType])
    
    # run the plugin to run
    for plugin in all_plugins:
        if plugin["unique_prefix"] == runType:                
            pluginsState = execute_plugin(db, all_plugins, plugin, pluginsState) 

    mylog('minimal', ['[', timeNowTZ(), '] END Run: ', runType])
    return pluginsState



#-------------------------------------------------------------------------------
def handle_test(runType, db, all_plugins, pluginsState):

    mylog('minimal', ['[', timeNowTZ(), '] [Test] START Test: ', runType])
    
    # Prepare test samples
    sample_txt = get_file_content(reportTemplatesPath + 'report_sample.txt')    
    sample_html = get_file_content(reportTemplatesPath + 'report_sample.html')    
    sample_json = json.loads(get_file_content(reportTemplatesPath + 'webhook_json_sample.json'))[0]["body"]["attachments"][0]["text"]
    
    # Create fake notification
    notification    = Notification_obj(db)
    notificationObj = notification.create(sample_json, "")

    # Run test
    pluginsState = handle_run(runType, db, all_plugins, pluginsState)

    # Remove sample notification
    notificationObj.remove(notificationObj.GUID)    

    mylog('minimal', ['[Test] END Test: ', runType])

    return pluginsState

