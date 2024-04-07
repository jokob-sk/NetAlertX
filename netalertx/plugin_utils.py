import os
import json

import conf 
from logger import mylog
from const import pluginsPath, logPath, apiPath
from helper import timeNowTZ,  updateState, get_file_content, write_file, get_setting, get_setting_value

module_name = 'Plugin utils'

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
        mylog('debug', [f'[{module_name}] In {objName} there are {count} events with the status "{status}" '])


#-------------------------------------------------------------------------------
def print_plugin_info(plugin, elements = ['display_name']):

    mylog('verbose', [f'[{module_name}] ---------------------------------------------']) 

    for el in elements:
        res = get_plugin_string(plugin, el)
        mylog('verbose', [f'[{module_name}] ', el ,': ', res]) 


#-------------------------------------------------------------------------------
# Gets the whole setting object
def get_plugin_setting(plugin, function_key):
    
    result = None

    for set in plugin['settings']:
        if set["function"] == function_key:
          result =  set 
          
    # if result == None:
    #     mylog('debug', [f'[{module_name}] Setting with "function":"', function_key, '" is missing in plugin: ', get_plugin_string(plugin, 'display_name')])

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
#  generates a comma separated list of values from a list (or a string representing a list)
def list_to_csv(arr):
    tmp = ''
    arrayItemStr = ''

    mylog('debug', f'[{module_name}] Flattening the below array')    
    mylog('debug', arr)    
    mylog('debug', f'[{module_name}] isinstance(arr, list) : {isinstance(arr, list)} | isinstance(arr, str) : {isinstance(arr, str)}')    

    if isinstance(arr, str):
        tmpStr =  arr.replace('[','').replace(']','').replace("'", '')  # removing brackets and single quotes (not allowed)    
        
        if ',' in tmpStr:            
            # Split the string into a list and trim whitespace
            cleanedStr = [tmpSubStr.strip() for tmpSubStr in tmpStr.split(',')]

            # Join the list elements using a comma
            result_string = ",".join(cleanedStr)   
        else:
            result_string = tmpStr

        return result_string

    elif isinstance(arr, list):
        for arrayItem in arr:
            # only one column flattening is supported
            if isinstance(arrayItem, list):  
                arrayItemStr = str(arrayItem[0]).replace("'", '').strip()  # removing single quotes - not allowed            
            else:
                # is string already
                arrayItemStr = arrayItem


            tmp += f'{arrayItemStr},'

        tmp = tmp[:-1]  # Remove last comma ','

        mylog('debug', f'[{module_name}] Flattened array: {tmp}')    

        return tmp

    else:
        mylog('none', f'[{module_name}] ⚠ ERROR Could not convert array: {arr}')    




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

    mylog('debug', [f'[{module_name}] Pre-Resolved CMD: '] + commandArr)   

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
def custom_plugin_decoder(pluginDict):
    return namedtuple('X', pluginDict.keys())(*pluginDict.values())        

#-------------------------------------------------------------------------------
# Handle empty value 
def handle_empty(value):    
    if value == '' or value is None:
        value = 'null'

    return value    

#-------------------------------------------------------------------------------
# Get and return a plugin object based on key-value pairs
# keyValues example: getPluginObject({"Plugin":"MQTT", "Watched_Value4":"someValue"})
def getPluginObject(keyValues):

    plugins_objects = apiPath + 'table_plugins_objects.json'

    try:
        with open(plugins_objects, 'r') as json_file:
            data = json.load(json_file)

            objectEntries = data.get("data", [])            

            for item in objectEntries:
                # Initialize a flag to check if all key-value pairs match
                all_match = True                

                for key, value in keyValues.items():
                    if item.get(key) != value:
                        all_match = False
                        break  # No need to continue checking if one pair doesn't match
                
                if all_match:
                    return item

            mylog('verbose', [f'[{module_name}] 💬 INFO - Object not found {json.dumps(keyValues)} '])  

            return {}

    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        # Handle the case when the file is not found, JSON decoding fails, or data is not in the expected format
        mylog('verbose', [f'[{module_name}] ⚠ ERROR - JSONDecodeError or FileNotFoundError for file {plugins_objects}'])                

        return {}


