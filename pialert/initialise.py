
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
from const import fullConfPath
from helper import collect_lang_strings, updateSubnets, initOrSetParam, isJsonObject, updateState
from logger import mylog
from api import update_api
from scheduler import schedule_class
from plugin import print_plugin_info, run_plugin_scripts
from plugin_utils import get_plugins_configs

#===============================================================================
# Initialise user defined values
#===============================================================================

#-------------------------------------------------------------------------------
# Import user values
# Check config dictionary
def ccd(key, default, config_dir, name, inputtype, options, group, events=[], desc = "", regex = "", setJsonMetadata = {}, overrideTemplate = {}):

    # use default inintialization value    
    result = default

    if events is None:
        events = []

    # use existing value if already supplied, otherwise default value is used
    if key in config_dir:
        result =  config_dir[key]

    if inputtype == 'text':
        result = result.replace('\'', "{s-quote}")

    conf.mySettingsSQLsafe.append((key, name, desc, inputtype, options, regex, str(result), group, str(events)))
    conf.mySettings.append((key, name, desc, inputtype, options, regex, result, group, str(events)))

    # save metadata in dummy setting
    if '__metadata' not in key:
        tuple = (f'{key}__metadata', "metadata name", "metadata desc", 'json', "", "", json.dumps(setJsonMetadata), group, '[]')
        conf.mySettingsSQLsafe.append(tuple)
        conf.mySettings.append(tuple)
    
        

    return result
#-------------------------------------------------------------------------------

def importConfigs (db): 

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
    

    if (fileModifiedTime == conf.lastImportedConfFile) :
        mylog('debug', ['[Import Config] skipping config file import'])
        return

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
    
    conf.LOG_LEVEL = ccd('LOG_LEVEL', 'verbose' , c_d, 'Log verboseness', 'text.select', "['none', 'minimal', 'verbose', 'debug']", 'General')
    conf.TIMEZONE = ccd('TIMEZONE', 'Europe/Berlin' , c_d, 'Time zone', 'text', '', 'General')    
    conf.PLUGINS_KEEP_HIST = ccd('PLUGINS_KEEP_HIST', 250 , c_d, 'Keep history entries', 'integer', '', 'General') 
    conf.PIALERT_WEB_PROTECTION = ccd('PIALERT_WEB_PROTECTION', False , c_d, 'Enable logon', 'boolean', '', 'General')
    conf.PIALERT_WEB_PASSWORD = ccd('PIALERT_WEB_PASSWORD', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92' , c_d, 'Logon password', 'readonly', '', 'General')
    conf.INCLUDED_SECTIONS = ccd('INCLUDED_SECTIONS', ['new_devices', 'down_devices', 'events']   , c_d, 'Notify on', 'text.multiselect', "['new_devices', 'down_devices', 'events', 'plugins']", 'General')    
    conf.REPORT_DASHBOARD_URL = ccd('REPORT_DASHBOARD_URL', 'http://pi.alert/' , c_d, 'PiAlert URL', 'text', '', 'General')
    conf.DIG_GET_IP_ARG = ccd('DIG_GET_IP_ARG', '-4 myip.opendns.com @resolver1.opendns.com' , c_d, 'DIG arguments', 'text', '', 'General')
    conf.UI_LANG = ccd('UI_LANG', 'English' , c_d, 'Language Interface', 'text.select', "['English', 'German', 'Spanish']", 'General')
    conf.UI_PRESENCE = ccd('UI_PRESENCE', ['online', 'offline', 'archived']   , c_d, 'Include in presence', 'text.multiselect', "['online', 'offline', 'archived']", 'General')    
    conf.DAYS_TO_KEEP_EVENTS = ccd('DAYS_TO_KEEP_EVENTS', 90 , c_d, 'Delete events days', 'integer', '', 'General')
    conf.HRS_TO_KEEP_NEWDEV = ccd('HRS_TO_KEEP_NEWDEV', 0 , c_d, 'Keep new devices for', 'integer', "0", 'General')    
    conf.DBCLNP_NOTIFI_HIST = ccd('DBCLNP_NOTIFI_HIST', 100 , c_d, 'Keep notification', 'integer', "0", 'General')    
    conf.API_CUSTOM_SQL = ccd('API_CUSTOM_SQL', 'SELECT * FROM Devices WHERE dev_PresentLastScan = 0' , c_d, 'Custom endpoint', 'text', '', 'General')
    conf.NETWORK_DEVICE_TYPES = ccd('NETWORK_DEVICE_TYPES', ['AP', 'Gateway', 'Firewall', 'Hypervisor', 'Powerline', 'Switch', 'WLAN', 'PLC', 'Router','USB LAN Adapter', 'USB WIFI Adapter', 'Internet'] , c_d, 'Network device types', 'list', '', 'General')

    # ARPSCAN (+ more settings are provided by the ARPSCAN plugin)    
    conf.SCAN_SUBNETS = ccd('SCAN_SUBNETS', ['192.168.1.0/24 --interface=eth1', '192.168.1.0/24 --interface=eth0'] , c_d, 'Subnets to scan', 'subnets', '', 'ARPSCAN')    

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
    conf.plugins = get_plugins_configs()

    mylog('none', ['[Config] Plugins: Number of dynamically loaded plugins: ', len(conf.plugins)])

    #  handle plugins
    index = 0
    for plugin in conf.plugins:
        # Header
        updateState(f"Import plugin {index} of {len(conf.plugins)}") 
        index +=1

        pref = plugin["unique_prefix"]  
        print_plugin_info(plugin, ['display_name','description'])

        # if plugin["enabled"] == 'true': 

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

        db.commitDB()



    conf.plugins_once_run = False
    # -----------------
    # Plugins END
  

    # Insert settings into the DB    
    sql.execute ("DELETE FROM Settings")    
    sql.executemany ("""INSERT INTO Settings ("Code_Name", "Display_Name", "Description", "Type", "Options",
         "RegEx", "Value", "Group", "Events" ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", conf.mySettingsSQLsafe)
    
    #commitDB(sql_connection)
    db.commitDB()

    #  update only the settings datasource
    update_api(db, False, ["settings"])  
    
    # run plugins that are modifying the config   
    run_plugin_scripts(db, 'before_config_save' )

    # Used to determine the next import
    conf.lastImportedConfFile = os.path.getmtime(config_file)   

    updateState("Config imported", conf.lastImportedConfFile, conf.lastImportedConfFile, False)   

    mylog('minimal', '[Config] Imported new config')



#-------------------------------------------------------------------------------
def read_config_file(filename):
    """
    retuns dict on the config file key:value pairs
    """
    mylog('minimal', '[Config] reading config file')
    # load the variables from  pialert.conf
    code = compile(filename.read_text(), filename.name, "exec")
    confDict = {} # config dictionary
    exec(code, {"__builtins__": {}}, confDict)
    return confDict 


#-------------------------------------------------------------------------------
# DEPERECATED soonest after 3/3/2024
replacements = {
    r'\bREPORT_TO\b': 'SMTP_REPORT_TO',
    r'\bREPORT_FROM\b': 'SMTP_REPORT_FROM',
    r'REPORT_MAIL=True': 'SMTP_RUN=\'on_notification\'',
    r'REPORT_APPRISE=True': 'APPRISE_RUN=\'on_notification\'',
    r'REPORT_NTFY=True': 'NTFY_RUN=\'on_notification\'',
    r'REPORT_WEBHOOK=True': 'WEBHOOK_RUN=\'on_notification\'',
    r'REPORT_PUSHSAFER=True': 'PUSHSAFER_RUN=\'on_notification\'',
    r'REPORT_MQTT=True': 'MQTT_RUN=\'on_notification\''
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

        

 