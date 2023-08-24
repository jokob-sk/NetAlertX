import os
import base64
import json

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
        # Check if the directory name does not start with "__" and does not end with "__ignore"
        if not d.startswith("__") and not d.endswith("__ignore"):
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