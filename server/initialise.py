
import os
import time
from pytz import timezone
from cron_converter import Cron
from pathlib import Path
import datetime
import json
import shutil
import re


import conf 
from const import fullConfPath, applicationPath, fullConfFolder
from helper import collect_lang_strings, updateSubnets, initOrSetParam, isJsonObject, updateState, setting_value_to_python_type, timeNowTZ, get_setting_value
from logger import mylog
from api import update_api
from scheduler import schedule_class
from plugin import print_plugin_info, run_plugin_scripts
from plugin_utils import get_plugins_configs, get_plugin_setting_obj
from notification import write_notification

#===============================================================================
# Initialise user defined values
#===============================================================================

#-------------------------------------------------------------------------------
# Import user values
# Check config dictionary

#-------------------------------------------------------------------------------
# managing application settings, ensuring SQL safety for user input, and updating internal configuration lists
def ccd(key, default, config_dir, name, inputtype, options, group, events=None, desc="", regex="", setJsonMetadata=None, overrideTemplate=None, forceDefault=False, overriddenByEnv=0):
    if events is None:
        events = []
    if setJsonMetadata is None:
        setJsonMetadata = {}
    if overrideTemplate is None:
        overrideTemplate = {}

    # Use default initialization value    
    result = default

    # Use existing value if already supplied, otherwise default value is used
    if forceDefault == False and key in config_dir:
        result = config_dir[key]

    # Single quotes might break SQL queries, replacing them
    if inputtype == 'text':
        result = result.replace('\'', "{s-quote}")

    # Create the tuples
    sql_safe_tuple = (key, name, desc, str(inputtype), options, regex, str(result), group, str(events), overriddenByEnv)
    settings_tuple = (key, name, desc, inputtype, options, regex, result, group, str(events), overriddenByEnv)

    # Update or append the tuples in the lists
    conf.mySettingsSQLsafe = update_or_append(conf.mySettingsSQLsafe, sql_safe_tuple, key)
    conf.mySettings = update_or_append(conf.mySettings, settings_tuple, key)

    # Save metadata in dummy setting if not a metadata key
    if '__metadata' not in key:
        metadata_tuple = (f'{key}__metadata', "metadata name", "metadata desc", '{"dataType":"json", "elements": [{"elementType" : "textarea", "elementOptions" : [{"readonly": "true"}] ,"transformers": []}]}', '[]', "", json.dumps(setJsonMetadata), group, '[]', overriddenByEnv)
        conf.mySettingsSQLsafe = update_or_append(conf.mySettingsSQLsafe, metadata_tuple, f'{key}__metadata')
        conf.mySettings = update_or_append(conf.mySettings, metadata_tuple, f'{key}__metadata')

    return result

#-------------------------------------------------------------------------------
# Function to find and update the existing key in the list
def update_or_append(settings_list, item_tuple, key):
    if settings_list is None:
        settings_list = []

    for index, item in enumerate(settings_list):
        if item[0] == key:
            mylog('trace', ['[Import Config] OLD TUPLE  : ', item])
            # Keep values marked as "_KEEP_"
            updated_tuple = tuple(
                new_val if new_val != "_KEEP_" else old_val
                for old_val, new_val in zip(item, item_tuple)
            )
            mylog('trace', ['[Import Config] NEW TUPLE  : ', updated_tuple])
            settings_list[index] = updated_tuple
            mylog('trace', ['[Import Config] FOUND key : ', key])
            return settings_list     
    

    settings_list.append(item_tuple)
    return settings_list


    
#-------------------------------------------------------------------------------

def importConfigs (db, all_plugins): 

    sql = db.sql

    # get config file name
    config_file = Path(fullConfPath)

    # Only import file if the file was modifed since last import.
    # this avoids time zone issues as we just compare the previous timestamp to the current time stamp

    # rename settings that have changed names due to code cleanup and migration to plugins
    renameSettings(config_file)

    fileModifiedTime = os.path.getmtime(config_file)

    mylog('debug', ['[Import Config] checking config file '])
    mylog('debug', ['[Import Config] lastImportedConfFile     :', conf.lastImportedConfFile])
    mylog('debug', ['[Import Config] fileModifiedTime         :', fileModifiedTime])
    

    if (fileModifiedTime == conf.lastImportedConfFile) and all_plugins is not None:
        mylog('debug', ['[Import Config] skipping config file import'])
        return all_plugins

    # Header
    updateState("Import config", showSpinner = True)  

    # remove all plugin langauge strings
    sql.execute("DELETE FROM Plugins_Language_Strings;")
    db.commitDB()
    
    mylog('debug', ['[Import Config] importing config file'])
    conf.mySettings = [] # reset settings
    conf.mySettingsSQLsafe = [] # same as above but safe to be passed into a SQL query

    # User values loaded from now
    c_d = read_config_file(config_file)

   
    # Import setting if found in the dictionary
    
    # General    
    # ----------------------------------------
    # ccd(key, default, config_dir, name, inputtype, options, group, events=[], desc = "", regex = "", setJsonMetadata = {}, overrideTemplate = {})
    
    conf.LOADED_PLUGINS = ccd('LOADED_PLUGINS', [] , c_d, 'Loaded plugins', '{"dataType":"array", "elements": [{"elementType" : "select", "elementOptions" : [{"multiple":"true"}] ,"transformers": []}]}', '[]', 'General')
    conf.SCAN_SUBNETS = ccd('SCAN_SUBNETS', ['192.168.1.0/24 --interface=eth1', '192.168.1.0/24 --interface=eth0'] , c_d, 'Subnets to scan', '{"dataType": "array","elements": [{"elementType": "input","elementOptions": [{"placeholder": "192.168.1.0/24 --interface=eth1"},{"suffix": "_in"},{"cssClasses": "col-sm-10"},{"prefillValue": "null"}],"transformers": []},{"elementType": "button","elementOptions": [{"sourceSuffixes": ["_in"]},{"separator": ""},{"cssClasses": "col-xs-12"},{"onClick": "addList(this, false)"},{"getStringKey": "Gen_Add"}],"transformers": []},{"elementType": "select","elementHasInputValue": 1,"elementOptions": [{"multiple": "true"},{"readonly": "true"},{"editable": "true"}],"transformers": []},{"elementType": "button","elementOptions": [{"sourceSuffixes": []},{"separator": ""},{"cssClasses": "col-xs-6"},{"onClick": "removeAllOptions(this)"},{"getStringKey": "Gen_Remove_All"}],"transformers": []},{"elementType": "button","elementOptions": [{"sourceSuffixes": []},{"separator": ""},{"cssClasses": "col-xs-6"},{"onClick": "removeFromList(this)"},{"getStringKey": "Gen_Remove_Last"}],"transformers": []}]}', '[]', 'General')    
    conf.LOG_LEVEL = ccd('LOG_LEVEL', 'verbose' , c_d, 'Log verboseness', '{"dataType":"string", "elements": [{"elementType" : "select", "elementOptions" : [] ,"transformers": []}]}', "['none', 'minimal', 'verbose', 'debug', 'trace']", 'General')
    conf.TIMEZONE = ccd('TIMEZONE', 'Europe/Berlin' , c_d, 'Time zone', '{"dataType":"string", "elements": [{"elementType" : "input", "elementOptions" : [] ,"transformers": []}]}', '[]', 'General')    
    conf.PLUGINS_KEEP_HIST = ccd('PLUGINS_KEEP_HIST', 250 , c_d, 'Keep history entries', '{"dataType":"integer", "elements": [{"elementType" : "input", "elementOptions" : [{"type": "number"}] ,"transformers": []}]}', '[]', 'General') 
    conf.REPORT_DASHBOARD_URL = ccd('REPORT_DASHBOARD_URL', 'http://netalertx/' , c_d, 'NetAlertX URL', '{"dataType":"string", "elements": [{"elementType" : "input", "elementOptions" : [] ,"transformers": []}]}', '[]', 'General')
    conf.DAYS_TO_KEEP_EVENTS = ccd('DAYS_TO_KEEP_EVENTS', 90 , c_d, 'Delete events days', '{"dataType":"integer", "elements": [{"elementType" : "input", "elementOptions" : [{"type": "number"}] ,"transformers": []}]}', '[]', 'General')
    conf.HRS_TO_KEEP_NEWDEV = ccd('HRS_TO_KEEP_NEWDEV', 0 , c_d, 'Keep new devices for', '{"dataType":"integer", "elements": [{"elementType" : "input", "elementOptions" : [{"type": "number"}] ,"transformers": []}]}', "[]", 'General')        
    conf.CLEAR_NEW_FLAG = ccd('CLEAR_NEW_FLAG', 0 , c_d, 'Clear new flag', '{"dataType":"integer", "elements": [{"elementType" : "input", "elementOptions" : [{"type": "number"}] ,"transformers": []}]}', "[]", 'General')        
    conf.API_CUSTOM_SQL = ccd('API_CUSTOM_SQL', 'SELECT * FROM Devices WHERE dev_PresentLastScan = 0' , c_d, 'Custom endpoint', '{"dataType":"string", "elements": [{"elementType" : "input", "elementOptions" : [] ,"transformers": []}]}', '[]', 'General')
    conf.VERSION = ccd('VERSION', '' , c_d, 'Version', '{"dataType":"string", "elements": [{"elementType" : "input", "elementOptions" : [{ "readonly": "true" }] ,"transformers": []}]}', '', 'General')
    conf.NETWORK_DEVICE_TYPES = ccd('NETWORK_DEVICE_TYPES', ['AP', 'Gateway', 'Firewall', 'Hypervisor', 'Powerline', 'Switch', 'WLAN', 'PLC', 'Router','USB LAN Adapter', 'USB WIFI Adapter', 'Internet'] , c_d, 'Network device types', '{"dataType":"array","elements":[{"elementType":"input","elementOptions":[{"placeholder":"Enter value"},{"suffix":"_in"},{"cssClasses":"col-sm-10"},{"prefillValue":"null"}],"transformers":[]},{"elementType":"button","elementOptions":[{"sourceSuffixes":["_in"]},{"separator":""},{"cssClasses":"col-xs-12"},{"onClick":"addList(this,false)"},{"getStringKey":"Gen_Add"}],"transformers":[]},{"elementType":"select",	"elementHasInputValue":1,"elementOptions":[{"multiple":"true"},{"readonly":"true"},{"editable":"true"}],"transformers":[]},{"elementType":"button","elementOptions":[{"sourceSuffixes":[]},{"separator":""},{"cssClasses":"col-xs-6"},{"onClick":"removeAllOptions(this)"},{"getStringKey":"Gen_Remove_All"}],"transformers":[]},{"elementType":"button","elementOptions":[{"sourceSuffixes":[]},{"separator":""},{"cssClasses":"col-xs-6"},{"onClick":"removeFromList(this)"},{"getStringKey":"Gen_Remove_Last"}],"transformers":[]}]}', '[]', 'General')
          
    # UI
    conf.UI_LANG = ccd('UI_LANG', 'English' , c_d, 'Language Interface', '{"dataType":"string", "elements": [{"elementType" : "select", "elementOptions" : [] ,"transformers": []}]}', "['English', 'French', 'German', 'Norwegian', 'Russian', 'Spanish', 'Italian (it_it)', 'Portuguese (pt_br)', 'Polish (pl_pl)', 'Turkish (tr_tr)', 'Chinese (zh_cn)', 'Czech (cs_cz)' ]", 'UI') 
    
    #  Init timezone in case it changed
    conf.tz = timezone(conf.TIMEZONE) 

    # TODO cleanup later ----------------------------------------------------------------------------------
    # init all time values as we have timezone - all this shoudl be moved into plugin/plugin settings
    conf.time_started = datetime.datetime.now(conf.tz)    
    conf.plugins_once_run = False

    # timestamps of last execution times
    conf.startTime  = conf.time_started
    now_minus_24h   = conf.time_started - datetime.timedelta(hours = 24)

    # set these times to the past to force the first run         
    conf.last_scan_run          = now_minus_24h        
    conf.last_version_check     = now_minus_24h  

    # TODO cleanup later ----------------------------------------------------------------------------------
    
    # reset schedules
    conf.mySchedules = [] 

    # Format and prepare the list of subnets
    conf.userSubnets = updateSubnets(conf.SCAN_SUBNETS)

    # Plugins START
    # -----------------
    all_plugins = get_plugins_configs()

    mylog('none', ['[Config] Plugins: Number of all plugins (including not loaded): ', len(all_plugins)])

    plugin_indexes_to_remove = []
    all_plugins_prefixes     = [] # to init the LOADED_PLUGINS setting with correct options
    loaded_plugins_prefixes  = [] # to init the LOADED_PLUGINS setting with correct initially seelcted values

    #  handle plugins
    index = 0
    for plugin in all_plugins:

        # Header on the frontend and the app_state.json
        updateState(f"Check plugin {index} of {len(all_plugins)}") 

        index +=1

        pref = plugin["unique_prefix"]  
        print_plugin_info(plugin, ['display_name','description'])

        all_plugins_prefixes.append(pref)

        # The below lines are used to determine if the plugin should be loaded, or skipped based on user settings (conf.LOADED_PLUGINS)
        # ...or based on if is already enabled, or if the default configuration loads the plugin (RUN function != disabled )   

        # get default plugin run value
        plugin_run = ''
        setting_obj = get_plugin_setting_obj(plugin, "RUN")

        if setting_obj is not None:
            set_type = setting_obj.get('type')              # lower case "type" - default json value vs uppper-case "Type" (= from user defined settings)
            set_value = setting_obj.get('default_value')

            plugin_run = setting_value_to_python_type(set_type, set_value)

        #  get user-defined run value if available
        if pref + "_RUN" in c_d:
            plugin_run =  c_d[pref + "_RUN" ]

        # only include loaded plugins, and the ones that are enabled        
        if pref in conf.LOADED_PLUGINS or plugin_run != 'disabled' or setting_obj is None or plugin_run is None:

            stringSqlParams = []
            
            # collect plugin level language strings
            stringSqlParams = collect_lang_strings(plugin, pref, stringSqlParams)
            
            for set in plugin["settings"]:
                setFunction = set["function"]
                # Setting code name / key  
                key = pref + "_" + setFunction 

                # set.get() - returns None if not found, set["options"] raises error
                #  ccd(key, default, config_dir, name, inputtype, options, group, events=[], desc = "", regex = "", setJsonMetadata = {}):
                v = ccd(key, 
                        set["default_value"], 
                        c_d, 
                        set["name"][0]["string"], 
                        set["type"] , 
                        str(set["options"]), 
                        group = pref, 
                        events = set.get("events"), 
                        desc = set["description"][0]["string"], 
                        regex = "", 
                        setJsonMetadata = set)                   

                # Save the user defined value into the object
                set["value"] = v

                # Setup schedules
                if setFunction == 'RUN_SCHD':
                    newSchedule = Cron(v).schedule(start_date=datetime.datetime.now(conf.tz))
                    conf.mySchedules.append(schedule_class(pref, newSchedule, newSchedule.next(), False))

                # Collect settings related language strings
                # Creates an entry with key, for example ARPSCAN_CMD_name
                stringSqlParams = collect_lang_strings(set,  pref + "_" + set["function"], stringSqlParams)

            # Collect column related language strings
            for clmn in plugin.get('database_column_definitions', []):
                # Creates an entry with key, for example ARPSCAN_Object_PrimaryID_name
                stringSqlParams = collect_lang_strings(clmn,  pref + "_" + clmn.get("column", ""), stringSqlParams)

            #  bulk-import language strings
            sql.executemany ("""INSERT INTO Plugins_Language_Strings ("Language_Code", "String_Key", "String_Value", "Extra") VALUES (?, ?, ?, ?)""", stringSqlParams )

        else:
            # log which plugins to remove 
            index_to_remove = 0
            for plugin in all_plugins:
                if plugin["unique_prefix"] == pref:
                    break
                index_to_remove +=1

            plugin_indexes_to_remove.append(index_to_remove)

    # remove plugin at index_to_remove from list
    # Sort the list of indexes in descending order to avoid index shifting issues
    plugin_indexes_to_remove.sort(reverse=True)
    for indx in plugin_indexes_to_remove:
        pref = all_plugins[indx]["unique_prefix"]  
        mylog('none', [f'[Config] ⛔ Unloading {pref}'])
        all_plugins.pop(indx)

    # all_plugins has now only initialized plugins, get all prefixes
    for plugin in all_plugins:
        pref = plugin["unique_prefix"]  
        loaded_plugins_prefixes.append(pref)
        
    # save the newly discovered plugins as options and default values
    conf.LOADED_PLUGINS = ccd('LOADED_PLUGINS', loaded_plugins_prefixes , c_d, 'Loaded plugins', '{"dataType":"array", "elements": [{"elementType" : "select", "elementOptions" : [{"multiple":"true"}] ,"transformers": []}]}', str(sorted(all_plugins_prefixes)), 'General')

    mylog('none', ['[Config] Number of Plugins to load: ', len(loaded_plugins_prefixes)])
    mylog('none', ['[Config] Plugins to load: ', loaded_plugins_prefixes])

    conf.plugins_once_run = False
    # -----------------
    # Plugins END
    
    # HANDLE APP_CONF_OVERRIDE via app_conf_override.json
    # Assuming fullConfFolder is defined elsewhere
    app_conf_override_path = fullConfFolder + '/app_conf_override.json'

    if os.path.exists(app_conf_override_path):
        with open(app_conf_override_path, 'r') as f:
            try:
                # Load settings_override from the JSON file
                settings_override = json.load(f)

                # Loop through settings_override dictionary
                for setting_name, value in settings_override.items():
                    # Ensure the value is treated as a string and passed directly
                    if isinstance(value, str):
                        # Log the value being passed
                        # ccd(key, default, config_dir, name, inputtype, options, group, events=None, desc="", regex="", setJsonMetadata=None, overrideTemplate=None, forceDefault=False)
                        mylog('debug', [f"[Config] Setting override {setting_name} with value: {value}"])
                        ccd(setting_name, value, c_d, '_KEEP_', '_KEEP_', '_KEEP_', '_KEEP_', None, "_KEEP_", "", None, None, True, 1)
                    else:
                        # Convert to string and log
                        # ccd(key, default, config_dir, name, inputtype, options, group, events=None, desc="", regex="", setJsonMetadata=None, overrideTemplate=None, forceDefault=False)
                        mylog('debug', [f"[Config] Setting override {setting_name} with value: {str(value)}"])
                        ccd(setting_name, str(value), c_d, '_KEEP_', '_KEEP_', '_KEEP_', '_KEEP_', None, "_KEEP_", "", None, None, True, 1)

            except json.JSONDecodeError:
                mylog('none', [f"[Config] [ERROR] Setting override decoding JSON from {app_conf_override_path}"])
    else:
        mylog('debug', [f"[Config] File {app_conf_override_path} does not exist."])
  
    # Check if app was upgraded
    with open(applicationPath + '/front/buildtimestamp.txt', 'r') as f:
        
        buildTimestamp = int(f.read().strip())
        cur_version = conf.VERSION 
        
        mylog('debug', [f"[Config] buildTimestamp: '{buildTimestamp}'"])
        mylog('debug', [f"[Config] conf.VERSION  : '{cur_version}'"])
        
        if str(cur_version) != str(buildTimestamp):
            
            mylog('none', ['[Config] App upgraded 🚀'])      
                 
            # ccd(key, default, config_dir, name, inputtype, options, group, events=None, desc="", regex="", setJsonMetadata=None, overrideTemplate=None, forceDefault=False)
            ccd('VERSION', buildTimestamp , c_d, '_KEEP_', '_KEEP_', '_KEEP_', '_KEEP_', None, "_KEEP_", "", None, None, True)
            
            write_notification(f'[Upgrade] : App upgraded 🚀 Please clear the cache: <ol> <li>Click OK below</li>  <li>Clear the browser cache (shift + browser refresh button)</li> <li> Clear app cache with the 🔄 (reload) button in the header</li><li>Go to Settings and click Save</li> </ol> Check out new features and what has changed in the <a href="https://github.com/jokob-sk/NetAlertX/releases" target="_blank">📓 release notes</a>.', 'interrupt', timeNowTZ())


    # Insert settings into the DB    
    sql.execute ("DELETE FROM Settings")    
    # mylog('debug', [f"[Config] conf.mySettingsSQLsafe  : '{conf.mySettingsSQLsafe}'"])
    sql.executemany ("""INSERT INTO Settings ("Code_Name", "Display_Name", "Description", "Type", "Options",
         "RegEx", "Value", "Group", "Events", "OverriddenByEnv" ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", conf.mySettingsSQLsafe)
    
    db.commitDB()

    #  update only the settings datasource
    update_api(db, all_plugins, False, ["settings"])  
    
    # run plugins that are modifying the config   
    run_plugin_scripts(db, all_plugins, 'before_config_save' )

    # Used to determine the next import
    conf.lastImportedConfFile = os.path.getmtime(config_file)   

    updateState("Config imported", conf.lastImportedConfFile, conf.lastImportedConfFile, False)   

    mylog('minimal', '[Config] Imported new config')

    return all_plugins



#-------------------------------------------------------------------------------
def read_config_file(filename):
    """
    retuns dict on the config file key:value pairs
    """
    mylog('minimal', '[Config] reading config file')
    # load the variables from .conf file
    code = compile(filename.read_text(), filename.name, "exec")
    confDict = {} # config dictionary
    exec(code, {"__builtins__": {}}, confDict)
    return confDict 


#-------------------------------------------------------------------------------
# DEPERECATED soonest after 10/10/2024
# 🤔Idea/TODO: Check and compare versions/timestamps amd only perform a replacement if config/version older than...
replacements = {
    r'\bREPORT_TO\b': 'SMTP_REPORT_TO',
    r'\bREPORT_FROM\b': 'SMTP_REPORT_FROM',
    r'\bPIALERT_WEB_PROTECTION\b': 'SETPWD_enable_password',
    r'\bPIALERT_WEB_PASSWORD\b': 'SETPWD_password',
    r'REPORT_MAIL=True': 'SMTP_RUN=\'on_notification\'',
    r'REPORT_APPRISE=True': 'APPRISE_RUN=\'on_notification\'',
    r'REPORT_NTFY=True': 'NTFY_RUN=\'on_notification\'',
    r'REPORT_WEBHOOK=True': 'WEBHOOK_RUN=\'on_notification\'',
    r'REPORT_PUSHSAFER=True': 'PUSHSAFER_RUN=\'on_notification\'',
    r'REPORT_MQTT=True': 'MQTT_RUN=\'on_notification\'',
    r'PIHOLE_CMD=': 'PIHOLE_CMD_OLD=',
    r'\bINCLUDED_SECTIONS\b': 'NTFPRCS_INCLUDED_SECTIONS',
    r'\bDIG_GET_IP_ARG\b': 'INTRNT_DIG_GET_IP_ARG',
    r'\/home/pi/pialert\b': '/app'
}

def renameSettings(config_file):
    # Check if the file contains any of the old setting code names
    contains_old_settings = False

    # Open the original config_file for reading
    with open(str(config_file), 'r') as original_file:  # Convert config_file to a string
        for line in original_file:
            # Use regular expressions with word boundaries to check for the old setting code names
            if any(re.search(key, line) for key in replacements.keys()):
                contains_old_settings = True
                break  # Exit the loop if any old setting is found

    # If the file contains old settings, proceed with renaming and backup
    if contains_old_settings:
        # Create a backup file with the suffix "_old_setting_names" and timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        backup_file = f"{config_file}_old_setting_names_{timestamp}.bak"

        mylog('debug', f'[Config] Old setting names will be replaced and a backup ({backup_file}) of the config created.')

        shutil.copy(str(config_file), backup_file)  # Convert config_file to a string

        # Open the original config_file for reading and create a temporary file for writing
        with open(str(config_file), 'r') as original_file, open(str(config_file) + "_temp", 'w') as temp_file:  # Convert config_file to a string
            for line in original_file:
                # Use regular expressions with word boundaries for replacements
                for key, value in replacements.items():
                    line = re.sub(key, value, line)

                # Write the modified line to the temporary file
                temp_file.write(line)

        # Close both files
        original_file.close()
        temp_file.close()

        # Replace the original config_file with the temporary file
        shutil.move(str(config_file) + "_temp", str(config_file))  # Convert config_file to a string
    else:
        mylog('debug', '[Config] No old setting names found in the file. No changes made.')

        

 