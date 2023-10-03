import os
import json

import conf 
from logger import mylog
from const import pluginsPath, logPath
from helper import timeNowTZ,  updateState, get_file_content, write_file, get_setting, get_setting_value



#-------------------------------------------------------------------------------
def logEventStatusCounts(objName, pluginEvents):
    status_counts = {}  # Dictionary to store counts for each status

    for event in pluginEvents:
        status = event.status
        if status in status_counts:
            status_counts[status] += 1
        else:
            status_counts[status] = 1

    for status, count in status_counts.items():
        mylog('debug', [f'[Plugins] In {objName} there are {count} events with the status "{status}" '])


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
        mylog('debug', ['[Plugins] Setting with "function":"', function_key, '" is missing in plugin: ', get_plugin_string(plugin, 'display_name')])

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
def flatten_array(arr):
    tmp = ''
    arrayItemStr = ''

    mylog('debug', '[Plugins] Flattening the below array')
    
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

    return tmp



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
# Replace {wildcars} with parameters
def resolve_wildcards_arr(commandArr, params):

    mylog('debug', ['[Plugins] Pre-Resolved CMD: '] + commandArr)   

    for param in params:
        # mylog('debug', ['[Plugins] key     : {', param[0], '}'])
        # mylog('debug', ['[Plugins] resolved: ', param[1]])

        i = 0
        
        for comPart in commandArr:

            commandArr[i] = comPart.replace('{' + str(param[0]) + '}', str(param[1])).replace('{s-quote}',"'")

            i += 1

    return commandArr   



#-------------------------------------------------------------------------------
def get_plugins_configs():
    pluginsList = []  # Create an empty list to store plugin configurations
    
    # Get a list of top-level directories in the specified pluginsPath
    dirs = next(os.walk(pluginsPath))[1]
    
    # Loop through each directory (plugin folder) in dirs
    for d in dirs:
        # Check if the directory name does not start with "__" to skip python cache
        if not d.startswith("__"):
            # Check if the 'ignore_plugin' file exists in the plugin folder
            ignore_plugin_path = os.path.join(pluginsPath, d, "ignore_plugin")
            if not os.path.isfile(ignore_plugin_path):
                # Construct the path to the config.json file within the plugin folder
                config_path = os.path.join(pluginsPath, d, "config.json")
                
                # Load the contents of the config.json file as a JSON object and append it to pluginsList
                pluginsList.append(json.loads(get_file_content(config_path)))
    
    return pluginsList  # Return the list of plugin configurations


    
#-------------------------------------------------------------------------------
# Gets the setting value
def get_plugin_setting_value(plugin, function_key):
    
    resultObj = get_plugin_setting(plugin, function_key)

    if resultObj != None:
        return resultObj["value"]

    return None

#-------------------------------------------------------------------------------
def custom_plugin_decoder(pluginDict):
    return namedtuple('X', pluginDict.keys())(*pluginDict.values())        

#-------------------------------------------------------------------------------
# Handle empty value 
def handle_empty(value):    
    if value == '' or value is None:
        value = 'null'

    return value    


#===============================================================================
# Handling of  user initialized front-end events
#===============================================================================

#-------------------------------------------------------------------------------
def check_and_run_user_event(db, pluginsState):
    
    sql = db.sql # TO-DO
    sql.execute(""" select * from Parameters where par_ID = "Front_Event" """)
    rows = sql.fetchall()    

    event, param = ['','']
    if len(rows) > 0 and rows[0]['par_Value'] != 'finished':
        keyValue = rows[0]['par_Value'].split('|')

        if len(keyValue) == 2:
            event = keyValue[0]
            param = keyValue[1]
    else:
        return pluginsState

    if event == 'test':
        handle_test(param)
    if event == 'run':
        pluginsState = handle_run(param, db, pluginsState)

    # clear event execution flag
    sql.execute ("UPDATE Parameters SET par_Value='finished' WHERE par_ID='Front_Event'")

    # commit to DB
    db.commitDB()    

    return pluginsState

#-------------------------------------------------------------------------------
def handle_run(runType, db, pluginsState):
    
    mylog('minimal', ['[', timeNowTZ(), '] START Run: ', runType])
    
    # run the plugin to run
    for plugin in conf.plugins:
        if plugin["unique_prefix"] == runType:                
            pluginsState = execute_plugin(db, plugin, pluginsState) 

    mylog('minimal', ['[', timeNowTZ(), '] END Run: ', runType])
    return pluginsState



#-------------------------------------------------------------------------------
def handle_test(testType):

    mylog('minimal', ['[', timeNowTZ(), '] START Test: ', testType])

    # Open text sample
    sample_txt = get_file_content(pialertPath + '/back/report_sample.txt')

    # Open html sample
    sample_html = get_file_content(pialertPath + '/back/report_sample.html')

    # Open json sample and get only the payload part
    sample_json_payload = json.loads(get_file_content(pialertPath + '/back/webhook_json_sample.json'))[0]["body"]["attachments"][0]["text"]

    sample_msg = noti_struc(sample_json_payload, sample_txt, sample_html )
   

    if testType == 'Email':
        send_email(sample_msg)
    elif testType == 'Webhooks':
        send_webhook (sample_msg)
    elif testType == 'Apprise':
        send_apprise (sample_msg)
    elif testType == 'NTFY':
        send_ntfy (sample_msg)
    elif testType == 'PUSHSAFER':
        send_pushsafer (sample_msg)
    else:
        mylog('none', ['[Test Publishers] No test matches: ', testType])    

    mylog('minimal', ['[Test Publishers] END Test: ', testType])
