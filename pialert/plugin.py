import os
import sqlite3
import json
import subprocess
import datetime
import base64
from collections import namedtuple

# pialert modules
import conf
from const import pluginsPath, logPath
from logger import mylog
from helper import timeNowTZ,  updateState, get_file_content, write_file, get_setting, get_setting_value
from api import update_api

#-------------------------------------------------------------------------------
def run_plugin_scripts(db, runType):

    # Header
    updateState(db,"Run: Plugins")

    mylog('debug', ['[Plugins] Check if any plugins need to be executed on run type: ', runType])

    for plugin in conf.plugins:

        shouldRun = False        
        prefix = plugin["unique_prefix"]

        set = get_plugin_setting(plugin, "RUN")
        if set != None and set['value'] == runType:
            if runType != "schedule":
                shouldRun = True
            elif  runType == "schedule":
                # run if overdue scheduled time   
                

                #  check schedules if any contains a unique plugin prefix matching the current plugin
                for schd in conf.mySchedules:
                    if schd.service == prefix:          
                        # Check if schedule overdue
                        shouldRun = schd.runScheduleCheck()  
                        if shouldRun:
                            # note the last time the scheduled plugin run was executed
                            schd.last_run = timeNowTZ()

        if shouldRun:            
            # Header
            updateState(db,f"Plugins: {prefix}")
                        
            print_plugin_info(plugin, ['display_name'])
            mylog('debug', ['[Plugins] CMD: ', get_plugin_setting(plugin, "CMD")["value"]])
            execute_plugin(db, plugin) 





#-------------------------------------------------------------------------------
def get_plugins_configs():
    
    pluginsList = []

    # only top level directories required. No need for the loop
    # for root, dirs, files in os.walk(pluginsPath):
    
    dirs = next(os.walk(pluginsPath))[1]
    for d in dirs:            # Loop over directories, not files    
        if not d.startswith( "__" ):        # ignore __pycache__ 
            pluginsList.append(json.loads(get_file_content(pluginsPath + "/" + d + '/config.json')))          

    return pluginsList



#-------------------------------------------------------------------------------
def print_plugin_info(plugin, elements = ['display_name']):

    mylog('verbose', ['[Plugins] ---------------------------------------------']) 

    for el in elements:
        res = get_plugin_string(plugin, el)
        mylog('verbose', ['[Plugins] ', el ,': ', res]) 


#-------------------------------------------------------------------------------
# Gets the whole setting object
def get_plugin_setting(plugin, function_key):
    
    result = None

    for set in plugin['settings']:
        if set["function"] == function_key:
          result =  set 

    if result == None:
        mylog('none', ['[Plugins] Setting with "function":"', function_key, '" is missing in plugin: ', get_plugin_string(plugin, 'display_name')])

    return result


        

#-------------------------------------------------------------------------------
# Get localized string value on the top JSON depth, not recursive
def get_plugin_string(props, el):

    result = ''

    if el in props['localized']:
        for val in props[el]:
            if val['language_code'] == 'en_us':
                result = val['string']
        
        if result == '':
            result = 'en_us string missing'

    else:
        result = props[el]
    
    return result


#-------------------------------------------------------------------------------
# Executes the plugin command specified in the setting with the function specified as CMD 
def execute_plugin(db, plugin):
    sql = db.sql  

    # ------- necessary settings check  --------
    set = get_plugin_setting(plugin, "CMD")

    #  handle missing "function":"CMD" setting
    if set == None:                
        return 

    set_CMD = set["value"]

    set = get_plugin_setting(plugin, "RUN_TIMEOUT")

    #  handle missing "function":"<unique_prefix>_TIMEOUT" setting
    if set == None:   
        set_RUN_TIMEOUT = 10
    else:     
        set_RUN_TIMEOUT = set["value"] 

    mylog('debug', ['[Plugins] Timeout: ', set_RUN_TIMEOUT])     

    #  Prepare custom params
    params = []

    if "params" in plugin:
        for param in plugin["params"]:            
            resolved = ""

            #  Get setting value
            if param["type"] == "setting":
                resolved = get_setting(param["value"])

                if resolved != None:
                    resolved = passable_string_from_setting(resolved)

            #  Get Sql result
            if param["type"] == "sql":
                resolved = flatten_array(db.get_sql_array(param["value"]))

            if resolved == None:
                mylog('none', [f'[Plugins] The parameter "name":"{param["name"]}" for "value": {param["value"]} was resolved as None'])

            else:
                params.append( [param["name"], resolved] )
    

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
            # try runnning a subprocess with a forced timeout in case the subprocess hangs
            output = subprocess.check_output (command, universal_newlines=True,  stderr=subprocess.STDOUT, timeout=(set_RUN_TIMEOUT))
        except subprocess.CalledProcessError as e:
            # An error occured, handle it
            mylog('none', [e.output])
            mylog('none', ['[Plugins] Error - enable LOG_LEVEL=debug and check logs'])            
        except subprocess.TimeoutExpired as timeErr:
            mylog('none', ['[Plugins] TIMEOUT - the process forcefully terminated as timeout reached']) 


        #  check the last run output
        # Initialize newLines
        newLines = []

        # Create the file path
        file_path = os.path.join(pluginsPath, plugin["code_name"], 'last_result.log')

        # Check if the file exists
        if os.path.exists(file_path):
            # File exists, open it and read its contents
            with open(file_path, 'r+') as f:
                newLines = f.read().split('\n')

            # if the script produced some outpout, clean it up to ensure it's the correct format        
            # cleanup - select only lines containing a separator to filter out unnecessary data
            newLines = list(filter(lambda x: '|' in x, newLines))  

            # # regular logging
            # for line in newLines:
            #     append_line_to_file (pluginsPath + '/plugin.log', line +'\n')         
            
            for line in newLines:
                columns = line.split("|")
                # There has to be always 9 columns
                if len(columns) == 9:
                    sqlParams.append((plugin["unique_prefix"], columns[0], columns[1], 'null', columns[2], columns[3], columns[4], columns[5], columns[6], 0, columns[7], 'null', columns[8]))
                else:
                    mylog('none', ['[Plugins] Skipped invalid line in the output: ', line])
        else:
            mylog('debug', [f'[Plugins] The file {file_path} does not exist'])             
    
    # pialert-db-query
    if plugin['data_source'] == 'pialert-db-query':
        # replace single quotes wildcards
        q = set_CMD.replace("{s-quote}", '\'')

        # Execute command
        mylog('verbose', ['[Plugins] Executing: ', q])

        # set_CMD should contain a SQL query        
        arr = db.get_sql_array (q) 

        for row in arr:
            # There has to be always 9 columns
            if len(row) == 9 and (row[0] in ['','null']) == False :
                sqlParams.append((plugin["unique_prefix"], row[0], handle_empty(row[1]), 'null', row[2], row[3], row[4], handle_empty(row[5]), handle_empty(row[6]), 0, row[7], 'null', row[8]))
            else:
                mylog('none', ['[Plugins] Skipped invalid sql result'])
    
    # pialert-db-query
    if plugin['data_source'] == 'sqlite-db-query':
        # replace single quotes wildcards
        # set_CMD should contain a SQL query    
        q = set_CMD.replace("{s-quote}", '\'')

        # Execute command
        mylog('verbose', ['[Plugins] Executing: ', q])
        
        fullSqlitePath = plugin['data_source_settings']['db_path']

        #  try attaching the sqlite DB
        try:
            sql.execute ("ATTACH DATABASE '"+ fullSqlitePath +"' AS EXTERNAL")
        except sqlite3.Error as e:
            mylog('none',[ '[Plugin] - ATTACH DATABASE failed with SQL ERROR: ', e])

        arr = db.get_sql_array (q) 

        for row in arr:
            # There has to be always 9 columns
            if len(row) == 9 and (row[0] in ['','null']) == False :
                sqlParams.append((plugin["unique_prefix"], row[0], handle_empty(row[1]), 'null', row[2], row[3], row[4], handle_empty(row[5]), handle_empty(row[6]), 0, row[7], 'null', row[8]))
            else:
                mylog('none', ['[Plugins] Skipped invalid sql result'])


    # check if the subprocess / SQL query failed / there was no valid output
    if len(sqlParams) == 0: 
        mylog('none', ['[Plugins] No output received from the plugin ', plugin["unique_prefix"], ' - enable LOG_LEVEL=debug and check logs'])
        return  
    else: 
        mylog('verbose', ['[Plugins] SUCCESS, received ', len(sqlParams), ' entries'])  

    # process results if any
    if len(sqlParams) > 0:                
        sql.executemany ("""INSERT INTO Plugins_Events ("Plugin", "Object_PrimaryID", "Object_SecondaryID", "DateTimeCreated", "DateTimeChanged", "Watched_Value1", "Watched_Value2", "Watched_Value3", "Watched_Value4", "Status" ,"Extra", "UserData", "ForeignKey") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", sqlParams) 
        db.commitDB()
        sql.executemany ("""INSERT INTO Plugins_History ("Plugin", "Object_PrimaryID", "Object_SecondaryID", "DateTimeCreated", "DateTimeChanged", "Watched_Value1", "Watched_Value2", "Watched_Value3", "Watched_Value4", "Status" ,"Extra", "UserData", "ForeignKey") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", sqlParams) 
        db.commitDB()

        process_plugin_events(db, plugin)

        # update API endpoints
        update_api(db, False, ["plugins_events","plugins_objects"])   

#-------------------------------------------------------------------------------
def custom_plugin_decoder(pluginDict):
    return namedtuple('X', pluginDict.keys())(*pluginDict.values())        

#-------------------------------------------------------------------------------
# Handle empty value 
def handle_empty(value):    
    if value == '' or value is None:
        value = 'null'

    return value    


#-------------------------------------------------------------------------------
# Flattens a setting to make it passable to a script
def passable_string_from_setting(globalSetting):

    setVal = globalSetting[6] # setting value
    setTyp = globalSetting[3] # setting type

    noConversion = ['text', 'string', 'integer', 'boolean', 'password', 'readonly', 'integer.select', 'text.select', 'integer.checkbox'  ]
    arrayConversion = ['text.multiselect', 'list'] 
    arrayConversionBase64 = ['subnets'] 
    jsonConversion = ['.template'] 

    mylog('debug', f'[Plugins] setTyp: {setTyp}')

    if setTyp in noConversion:
        return setVal

    if setTyp in arrayConversion:
        return flatten_array(setVal)

    if setTyp in arrayConversionBase64:
        
        return flatten_array(setVal, encodeBase64 = True)

    for item in jsonConversion:
        if setTyp.endswith(item):
            return json.dumps(setVal)

    mylog('none', ['[Plugins] ERROR: Parameter not converted.'])  



#-------------------------------------------------------------------------------
# Gets the setting value
def get_plugin_setting_value(plugin, function_key):
    
    resultObj = get_plugin_setting(plugin, function_key)

    if resultObj != None:
        return resultObj["value"]

    return None



#-------------------------------------------------------------------------------
def flatten_array(arr, encodeBase64=False):
    tmp = ''
    arrayItemStr = ''

    mylog('debug', '[Plugins] Flattening the below array')
    mylog('debug', f'[Plugins] Convert to Base64: {encodeBase64}')
    mylog('debug', arr)

    for arrayItem in arr:
        # only one column flattening is supported
        if isinstance(arrayItem, list):            
            arrayItemStr = str(arrayItem[0]).replace("'", '')  # removing single quotes - not allowed            
        else:
            # is string already
            arrayItemStr = arrayItem


        tmp += f'{arrayItemStr},'

    tmp = tmp[:-1]  # Remove last comma ','

    mylog('debug', f'[Plugins] Flattened array: {tmp}')

    if encodeBase64:
        tmp = str(base64.b64encode(tmp.encode('ascii')))
        mylog('debug', f'[Plugins] Flattened array (base64): {tmp}')


    return tmp



#-------------------------------------------------------------------------------
# Replace {wildcars} with parameters
def resolve_wildcards_arr(commandArr, params):

    mylog('debug', ['[Plugins] Pre-Resolved CMD: '] + commandArr)   

    for param in params:
        # mylog('debug', ['[Plugins] key     : {', param[0], '}'])
        # mylog('debug', ['[Plugins] resolved: ', param[1]])

        i = 0
        
        for comPart in commandArr:

            commandArr[i] = comPart.replace('{' + param[0] + '}', param[1]).replace('{s-quote}',"'")

            i += 1

    return commandArr    


#-------------------------------------------------------------------------------
# Combine plugin objects, keep user-defined values, created time, changed time if nothing changed and the index
def combine_plugin_objects(old, new):    
    
    new.userData = old.userData 
    new.index = old.index 
    new.created = old.created 

    # Keep changed time if nothing changed
    if new.status in ['watched-not-changed']:
        new.changed = old.changed

    #  return the new object, with some of the old values
    return new

#-------------------------------------------------------------------------------
# Check if watched values changed for the given plugin
def process_plugin_events(db, plugin):    
    sql = db.sql
    
    # capturing if we need to process scan results for devices
    conf.currentScanNeedsProcessing = False    

    pluginPref = plugin["unique_prefix"]

    mylog('debug', ['[Plugins] Processing        : ', pluginPref])

    plugObjectsArr = db.get_sql_array ("SELECT * FROM Plugins_Objects where Plugin = '" + str(pluginPref)+"'") 
    plugEventsArr  = db.get_sql_array ("SELECT * FROM Plugins_Events where Plugin = '" + str(pluginPref)+"'") 

    pluginObjects = []
    pluginEvents  = []

    for obj in plugObjectsArr: 
        pluginObjects.append(plugin_object_class(plugin, obj))

    existingPluginObjectsCount = len(pluginObjects)

    mylog('debug', ['[Plugins] Existing objects        : ', existingPluginObjectsCount])
    mylog('debug', ['[Plugins] New and existing events : ', len(plugEventsArr)])

    # set status as new - will be changed later if conditions are fulfilled, e.g. entry found
    for eve in plugEventsArr:
        tmpObject = plugin_object_class(plugin, eve)        
        tmpObject.status = "new"
        pluginEvents.append(tmpObject)

    
    #  Update the status to "exists"
    index = 0
    for tmpObjFromEvent in pluginEvents:        

        #  compare hash of the IDs for uniqueness
        if any(x.idsHash == tmpObject.idsHash for x in pluginObjects):
            mylog('debug', ['[Plugins] Found existing object'])
            pluginEvents[index].status = "exists"            
        index += 1

    # Loop thru events and update the one that exist to determine if watched columns changed
    index = 0
    for tmpObjFromEvent in pluginEvents:  

        if tmpObjFromEvent.status == "exists": 

            #  compare hash of the changed watched columns for uniqueness
            if any(x.watchedHash != tmpObject.watchedHash for x in pluginObjects):
                pluginEvents[index].status = "watched-changed"                            
            else:
                pluginEvents[index].status = "watched-not-changed"  
        index += 1

    # Merge existing plugin objects with newly discovered ones and update existing ones with new values
    for eveObj in pluginEvents:
        if eveObj.status == 'new':
            pluginObjects.append(eveObj)
        else:
            index = 0
            for plugObj in pluginObjects:
                # find corresponding object for the event and merge
                if plugObj.idsHash == eveObj.idsHash:               
                    pluginObjects[index] =  combine_plugin_objects(plugObj, eveObj)                    

                index += 1

    # Update the DB
    # ----------------------------
    # Update the Plugin_Objects    
    for plugObj in pluginObjects: 

        createdTime = plugObj.created

        if plugObj.status == 'new':
            
            createdTime = plugObj.changed

            sql.execute ("INSERT INTO Plugins_Objects (Plugin, Object_PrimaryID, Object_SecondaryID, DateTimeCreated, DateTimeChanged, Watched_Value1, Watched_Value2, Watched_Value3, Watched_Value4, Status, Extra, UserData, ForeignKey) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (plugObj.pluginPref, plugObj.primaryId , plugObj.secondaryId , createdTime, plugObj.changed , plugObj.watched1 , plugObj.watched2 , plugObj.watched3 , plugObj.watched4 , plugObj.status , plugObj.extra, plugObj.userData, plugObj.foreignKey ))    
        else:
            sql.execute (f"UPDATE Plugins_Objects set Plugin = '{plugObj.pluginPref}', DateTimeChanged = '{plugObj.changed}', Watched_Value1 = '{plugObj.watched1}', Watched_Value2 = '{plugObj.watched2}', Watched_Value3 = '{plugObj.watched3}', Watched_Value4 = '{plugObj.watched4}', Status = '{plugObj.status}', Extra = '{plugObj.extra}', ForeignKey = '{plugObj.foreignKey}' WHERE \"Index\" = {plugObj.index}")            

    # Update the Plugins_Events with the new statuses    
    sql.execute (f'DELETE FROM Plugins_Events where Plugin = "{pluginPref}"')

    for plugObj in pluginEvents: 

        createdTime = plugObj.created

        # use the same datetime for created and changed if a new entry
        if plugObj.status == 'new':
            createdTime = plugObj.changed  

        #  insert only events if they are to be reported on
        if plugObj.status in get_plugin_setting_value(plugin, "REPORT_ON"):  

            sql.execute ("INSERT INTO Plugins_Events (Plugin, Object_PrimaryID, Object_SecondaryID, DateTimeCreated, DateTimeChanged, Watched_Value1, Watched_Value2, Watched_Value3, Watched_Value4, Status,  Extra, UserData, ForeignKey) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (plugObj.pluginPref, plugObj.primaryId , plugObj.secondaryId , createdTime, plugObj.changed , plugObj.watched1 , plugObj.watched2 , plugObj.watched3 , plugObj.watched4 , plugObj.status , plugObj.extra, plugObj.userData, plugObj.foreignKey ))

    # Perform databse table mapping if enabled for the plugin   
    if len(pluginEvents) > 0 and  "mapped_to_table" in plugin:

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

            # Append the mapped values to the list 'sqlParams' as a tuple.
            sqlParams.append(tuple(tmpList))

        # Generate the SQL INSERT query using the collected information.
        q = f'INSERT into {dbTable} ({columnsStr}) VALUES ({valuesStr})'

        # Log a debug message showing the generated SQL query for mapping.
        mylog('debug', ['[Plugins] SQL query for mapping: ', q])

        # Execute the SQL query using 'sql.executemany()' and the 'sqlParams' list of tuples.
        # This will insert multiple rows into the database in one go.
        sql.executemany(q, sqlParams)

        db.commitDB()

        # perform scan if mapped to CurrentScan table
        if dbTable == 'CurrentScan':   
            conf.currentScanNeedsProcessing = True          

    db.commitDB()


#-------------------------------------------------------------------------------
class plugin_object_class:
    def __init__(self, plugin, objDbRow):
        self.index        = objDbRow[0]
        self.pluginPref   = objDbRow[1]
        self.primaryId    = objDbRow[2]
        self.secondaryId  = objDbRow[3]
        self.created      = objDbRow[4]
        self.changed      = objDbRow[5]
        self.watched1     = objDbRow[6]
        self.watched2     = objDbRow[7]
        self.watched3     = objDbRow[8]
        self.watched4     = objDbRow[9]
        self.status       = objDbRow[10]
        self.extra        = objDbRow[11]
        self.userData     = objDbRow[12]
        self.foreignKey   = objDbRow[13]

        # self.idsHash      = str(hash(str(self.primaryId) + str(self.secondaryId)))    
        self.idsHash      = str(self.primaryId) + str(self.secondaryId)

        self.watchedClmns = []
        self.watchedIndxs = []          

        setObj = get_plugin_setting(plugin, 'WATCH')

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

  

