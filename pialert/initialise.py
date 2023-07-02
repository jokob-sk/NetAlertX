
import os
import time
from pytz import timezone
from cron_converter import Cron
from pathlib import Path
import datetime

import conf 
from const import fullConfPath
from helper import collect_lang_strings, updateSubnets, initOrSetParam
from logger import mylog
from api import update_api
from scheduler import schedule_class
from plugin import get_plugins_configs, print_plugin_info

#===============================================================================
# Initialise user defined values
#===============================================================================
# We need access to the DB to save new values so need to define DB access methods first
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Import user values
# Check config dictionary
def ccd(key, default, config_dir, name, inputtype, options, group, events=[], desc = "", regex = ""):
    result = default

    # use existing value if already supplied, otherwise default value is used
    if key in config_dir:
        result =  config_dir[key]

    if inputtype == 'text':
        result = result.replace('\'', "{s-quote}")

    conf.mySettingsSQLsafe.append((key, name, desc, inputtype, options, regex, str(result), group, str(events)))
    conf.mySettings.append((key, name, desc, inputtype, options, regex, result, group, str(events)))

    return result
#-------------------------------------------------------------------------------

def importConfigs (db): 

    sql = db.sql

    # get config file name
    config_file = Path(fullConfPath)

    # Only import file if the file was modifed since last import.
    # this avoids time zone issues as we just compare the previous timestamp to the current time stamp
    mylog('debug', ['[Import Config] checking config file '])
    mylog('debug', ['[Import Config] lastImportedConfFile     :', conf.lastImportedConfFile])
    mylog('debug', ['[Import Config] file modified time       :', os.path.getmtime(config_file)])
    

    if (os.path.getmtime(config_file) == conf.lastImportedConfFile) :
        mylog('debug', ['[Import Config] skipping config file import'])
        return

    conf.lastImportedConfFile = os.path.getmtime(config_file)  



    
    mylog('debug', ['[Import Config] importing config file'])
    conf.mySettings = [] # reset settings
    conf.mySettingsSQLsafe = [] # same as above but safe to be passed into a SQL query

    c_d = read_config_file(config_file)

    # Import setting if found in the dictionary
    # General
    conf.ENABLE_ARPSCAN = ccd('ENABLE_ARPSCAN', True , c_d, 'Enable arpscan', 'boolean', '', 'General', ['run']) 
    conf.SCAN_SUBNETS = ccd('SCAN_SUBNETS', ['192.168.1.0/24 --interface=eth1', '192.168.1.0/24 --interface=eth0'] , c_d, 'Subnets to scan', 'subnets', '', 'General')    
    conf.LOG_LEVEL = ccd('LOG_LEVEL', 'verbose' , c_d, 'Log verboseness', 'selecttext', "['none', 'minimal', 'verbose', 'debug']", 'General')
    conf.TIMEZONE = ccd('TIMEZONE', 'Europe/Berlin' , c_d, 'Time zone', 'text', '', 'General')
    conf.ENABLE_PLUGINS = ccd('ENABLE_PLUGINS', True , c_d, 'Enable plugins', 'boolean', '', 'General') 
    conf.PIALERT_WEB_PROTECTION = ccd('PIALERT_WEB_PROTECTION', False , c_d, 'Enable logon', 'boolean', '', 'General')
    conf.PIALERT_WEB_PASSWORD = ccd('PIALERT_WEB_PASSWORD', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92' , c_d, 'Logon password', 'readonly', '', 'General')
    conf.INCLUDED_SECTIONS = ccd('INCLUDED_SECTIONS', ['internet', 'new_devices', 'down_devices', 'events', 'ports']   , c_d, 'Notify on', 'multiselect', "['internet', 'new_devices', 'down_devices', 'events', 'ports', 'plugins']", 'General')
    conf.SCAN_CYCLE_MINUTES = ccd('SCAN_CYCLE_MINUTES', 5 , c_d, 'Scan cycle delay (m)', 'integer', '', 'General')
    conf.DAYS_TO_KEEP_EVENTS = ccd('DAYS_TO_KEEP_EVENTS', 90 , c_d, 'Delete events days', 'integer', '', 'General')
    conf.REPORT_DASHBOARD_URL = ccd('REPORT_DASHBOARD_URL', 'http://pi.alert/' , c_d, 'PiAlert URL', 'text', '', 'General')
    conf.DIG_GET_IP_ARG = ccd('DIG_GET_IP_ARG', '-4 myip.opendns.com @resolver1.opendns.com' , c_d, 'DIG arguments', 'text', '', 'General')
    conf.UI_LANG = ccd('UI_LANG', 'English' , c_d, 'Language Interface', 'selecttext', "['English', 'German', 'Spanish']", 'General')
    conf.UI_PRESENCE = ccd('UI_PRESENCE', ['online', 'offline', 'archived']   , c_d, 'Include in presence', 'multiselect', "['online', 'offline', 'archived']", 'General')    

    # New device defaults
    conf.NEWDEV_SCAN = ccd('NEWDEV_SCAN', 1 , c_d, 'Scan Device', 'selectinteger', "['0', '1']", 'NewDeviceDefaults')
    conf.NEWDEV_ALERT_ALL = ccd('NEWDEV_ALERT_ALL', 0 , c_d, 'Alert All Events', 'selectinteger', "['0', '1']",  'NewDeviceDefaults')
    conf.NEWDEV_ALERT_DWN = ccd('NEWDEV_ALERT_DWN', 0 , c_d, 'Alert Down', 'selectinteger', "['0', '1']",  'NewDeviceDefaults')
    conf.NEWDEV_NEWDEV = ccd('NEWDEV_NEWDEV', 1 , c_d, 'New Device', 'selectinteger', "['0', '1']",  'NewDeviceDefaults')
    conf.NEWDEV_ARCHIVED = ccd('NEWDEV_ARCHIVED', 0 , c_d, 'Archived', 'selectinteger', "['0', '1']", 'NewDeviceDefaults')
    conf.NEWDEV_SKIPNTF = ccd('NEWDEV_SKIPNTF', 0 , c_d, 'Skip repeated notifications for', 'selectinteger', "['0', '1', '8', '24', '168']", 'NewDeviceDefaults')

    # Email
    conf.REPORT_MAIL = ccd('REPORT_MAIL', False , c_d, 'Enable email', 'boolean', '', 'Email', ['test'])
    conf.SMTP_SERVER = ccd('SMTP_SERVER', '' , c_d,'SMTP server URL', 'text', '', 'Email')
    conf.SMTP_PORT = ccd('SMTP_PORT', 587 , c_d, 'SMTP port', 'integer', '', 'Email')
    conf.REPORT_TO = ccd('REPORT_TO', 'user@gmail.com' , c_d, 'Email to', 'text', '', 'Email')
    conf.REPORT_FROM = ccd('REPORT_FROM', 'Pi.Alert <user@gmail.com>' , c_d, 'Email Subject', 'text', '', 'Email')
    conf.SMTP_SKIP_LOGIN = ccd('SMTP_SKIP_LOGIN', False , c_d, 'SMTP skip login', 'boolean', '', 'Email')
    conf.SMTP_USER = ccd('SMTP_USER', '' , c_d, 'SMTP user', 'text', '', 'Email')
    conf.SMTP_PASS = ccd('SMTP_PASS', '' , c_d, 'SMTP password', 'password', '', 'Email')
    conf.SMTP_SKIP_TLS = ccd('SMTP_SKIP_TLS', False , c_d, 'SMTP skip TLS', 'boolean', '', 'Email')
    conf.SMTP_FORCE_SSL = ccd('SMTP_FORCE_SSL', False , c_d, 'Force SSL', 'boolean', '', 'Email')

    # Webhooks
    conf.REPORT_WEBHOOK = ccd('REPORT_WEBHOOK', False , c_d, 'Enable Webhooks', 'boolean', '', 'Webhooks', ['test'])
    conf.WEBHOOK_URL = ccd('WEBHOOK_URL', '' , c_d, 'Target URL', 'text', '', 'Webhooks')
    conf.WEBHOOK_PAYLOAD = ccd('WEBHOOK_PAYLOAD', 'json' , c_d, 'Payload type', 'selecttext', "['json', 'html', 'text']", 'Webhooks')
    conf.WEBHOOK_REQUEST_METHOD = ccd('WEBHOOK_REQUEST_METHOD', 'GET' , c_d, 'Req type', 'selecttext', "['GET', 'POST', 'PUT']", 'Webhooks')
    conf.WEBHOOK_SIZE = ccd('WEBHOOK_SIZE', 1024 , c_d, 'Payload size', 'integer', '', 'Webhooks')

    # Apprise
    conf.REPORT_APPRISE = ccd('REPORT_APPRISE', False , c_d, 'Enable Apprise', 'boolean', '', 'Apprise', ['test'])
    conf.APPRISE_HOST = ccd('APPRISE_HOST', '' , c_d, 'Apprise host URL', 'text', '', 'Apprise')
    conf.APPRISE_URL = ccd('APPRISE_URL', '' , c_d, 'Apprise notification URL', 'text', '', 'Apprise')
    conf.APPRISE_PAYLOAD = ccd('APPRISE_PAYLOAD', 'html' , c_d, 'Payload type', 'selecttext', "['html', 'text']", 'Apprise')

    # NTFY
    conf.REPORT_NTFY = ccd('REPORT_NTFY', False , c_d, 'Enable NTFY', 'boolean', '', 'NTFY', ['test'])
    conf.NTFY_HOST = ccd('NTFY_HOST', 'https://ntfy.sh' , c_d, 'NTFY host URL', 'text', '', 'NTFY')
    conf.NTFY_TOPIC = ccd('NTFY_TOPIC', '' , c_d, 'NTFY topic', 'text', '', 'NTFY')
    conf.NTFY_USER = ccd('NTFY_USER', '' , c_d, 'NTFY user', 'text', '', 'NTFY')
    conf.NTFY_PASSWORD = ccd('NTFY_PASSWORD', '' , c_d, 'NTFY password', 'password', '', 'NTFY')

    # PUSHSAFER
    conf.REPORT_PUSHSAFER = ccd('REPORT_PUSHSAFER', False , c_d, 'Enable PUSHSAFER', 'boolean', '', 'PUSHSAFER', ['test'])
    conf.PUSHSAFER_TOKEN = ccd('PUSHSAFER_TOKEN', 'ApiKey' , c_d, 'PUSHSAFER token', 'text', '', 'PUSHSAFER')

    # MQTT
    conf.REPORT_MQTT = ccd('REPORT_MQTT', False , c_d, 'Enable MQTT', 'boolean', '', 'MQTT')
    conf.MQTT_BROKER = ccd('MQTT_BROKER', '' , c_d, 'MQTT broker', 'text', '', 'MQTT')
    conf.MQTT_PORT = ccd('MQTT_PORT', 1883 , c_d, 'MQTT broker port', 'integer', '', 'MQTT')
    conf.MQTT_USER = ccd('MQTT_USER', '' , c_d, 'MQTT user', 'text', '', 'MQTT')
    conf.MQTT_PASSWORD = ccd('MQTT_PASSWORD', '' , c_d, 'MQTT password', 'password', '', 'MQTT')
    conf.MQTT_QOS = ccd('MQTT_QOS', 0 , c_d, 'MQTT Quality of Service', 'selectinteger', "['0', '1', '2']", 'MQTT')
    conf.MQTT_DELAY_SEC = ccd('MQTT_DELAY_SEC', 2 , c_d, 'MQTT delay', 'selectinteger', "['2', '3', '4', '5']", 'MQTT')

    # DynDNS
    conf.DDNS_ACTIVE = ccd('DDNS_ACTIVE', False , c_d, 'Enable DynDNS', 'boolean', '', 'DynDNS')
    conf.DDNS_DOMAIN = ccd('DDNS_DOMAIN', 'your_domain.freeddns.org' , c_d, 'DynDNS domain URL', 'text', '', 'DynDNS')
    conf.DDNS_USER = ccd('DDNS_USER', 'dynu_user' , c_d, 'DynDNS user', 'text', '', 'DynDNS')
    conf.DDNS_PASSWORD = ccd('DDNS_PASSWORD', 'A0000000B0000000C0000000D0000000' , c_d, 'DynDNS password', 'password', '', 'DynDNS')
    conf.DDNS_UPDATE_URL = ccd('DDNS_UPDATE_URL', 'https://api.dynu.com/nic/update?' , c_d, 'DynDNS update URL', 'text', '', 'DynDNS')

    # PiHole
    conf.PIHOLE_ACTIVE = ccd('PIHOLE_ACTIVE',  False, c_d, 'Enable PiHole mapping', 'boolean', '', 'PiHole')
    conf.DHCP_ACTIVE = ccd('DHCP_ACTIVE', False , c_d, 'Enable PiHole DHCP', 'boolean', '', 'PiHole')

    # PHOLUS
    conf.PHOLUS_ACTIVE = ccd('PHOLUS_ACTIVE', False , c_d, 'Enable Pholus scans', 'boolean', '', 'Pholus')
    conf.PHOLUS_TIMEOUT = ccd('PHOLUS_TIMEOUT', 20 , c_d, 'Pholus timeout', 'integer', '', 'Pholus')
    conf.PHOLUS_FORCE = ccd('PHOLUS_FORCE', False , c_d, 'Pholus force check', 'boolean', '', 'Pholus')
    conf.PHOLUS_RUN = ccd('PHOLUS_RUN', 'once' , c_d, 'Pholus enable schedule', 'selecttext', "['disabled', 'once', 'schedule']", 'Pholus')
    conf.PHOLUS_RUN_TIMEOUT = ccd('PHOLUS_RUN_TIMEOUT', 600 , c_d, 'Pholus timeout schedule', 'integer', '', 'Pholus')   
    conf.PHOLUS_RUN_SCHD = ccd('PHOLUS_RUN_SCHD', '0 4 * * *' , c_d, 'Pholus schedule', 'text', '', 'Pholus')
    conf.PHOLUS_DAYS_DATA = ccd('PHOLUS_DAYS_DATA', 0 , c_d, 'Pholus keep days', 'integer', '', 'Pholus')
    
    # Nmap
    conf.NMAP_ACTIVE = ccd('NMAP_ACTIVE', True , c_d, 'Enable Nmap scans', 'boolean', '', 'Nmap')
    conf.NMAP_TIMEOUT = ccd('NMAP_TIMEOUT', 150 , c_d, 'Nmap timeout', 'integer', '', 'Nmap')
    conf.NMAP_RUN = ccd('NMAP_RUN', 'disabled' , c_d, 'Nmap enable schedule', 'selecttext', "['disabled', 'once', 'schedule']", 'Nmap')
    conf.NMAP_RUN_SCHD = ccd('NMAP_RUN_SCHD', '0 2 * * *' , c_d, 'Nmap schedule', 'text', '', 'Nmap')
    conf.NMAP_ARGS = ccd('NMAP_ARGS', '-p -10000' , c_d, 'Nmap custom arguments', 'text', '', 'Nmap')

    # API     
    conf.API_CUSTOM_SQL = ccd('API_CUSTOM_SQL', 'SELECT * FROM Devices WHERE dev_PresentLastScan = 0' , c_d, 'Custom endpoint', 'text', '', 'API')

    #  Init timezone in case it changed
    conf.tz = timezone(conf.TIMEZONE) 
    
    # global mySchedules
    # reset schedules
    conf.mySchedules = [] 

    # init pholus schedule
    pholusSchedule = Cron(conf.PHOLUS_RUN_SCHD).schedule(start_date=datetime.datetime.now(conf.tz))    
    
    conf.mySchedules.append(schedule_class("pholus", pholusSchedule, pholusSchedule.next(), False))

    # init nmap schedule
    nmapSchedule = Cron(conf.NMAP_RUN_SCHD).schedule(start_date=datetime.datetime.now(conf.tz))
    conf.mySchedules.append(schedule_class("nmap", nmapSchedule, nmapSchedule.next(), False))

    # Format and prepare the list of subnets
    conf.userSubnets = updateSubnets(conf.SCAN_SUBNETS)

    # Plugins START
    # -----------------
    if conf.ENABLE_PLUGINS:
        conf.plugins = get_plugins_configs()

        mylog('none', ['[Config] Plugins: Number of dynamically loaded plugins: ', len(conf.plugins)])

        #  handle plugins
        for plugin in conf.plugins:
            pref = plugin["unique_prefix"]  
            print_plugin_info(plugin, ['display_name','description'])

            # if plugin["enabled"] == 'true': 
            
            # collect plugin level language strings
            collect_lang_strings(db, plugin, pref)
            
            for set in plugin["settings"]:
                setFunction = set["function"]
                # Setting code name / key  
                key = pref + "_" + setFunction 

                v = ccd(key, set["default_value"], c_d, set["name"][0]["string"], set["type"] , str(set["options"]), pref)

                # Save the user defined value into the object
                set["value"] = v

                # Setup schedules
                if setFunction == 'RUN_SCHD':
                    newSchedule = Cron(v).schedule(start_date=datetime.datetime.now(conf.tz))
                    conf.mySchedules.append(schedule_class(pref, newSchedule, newSchedule.next(), False))

                # Collect settings related language strings
                collect_lang_strings(db, set,  pref + "_" + set["function"])

        conf.plugins_once_run = False
    # -----------------
    # Plugins END

    
           
    

    # Insert settings into the DB    
    sql.execute ("DELETE FROM Settings")    
    sql.executemany ("""INSERT INTO Settings ("Code_Name", "Display_Name", "Description", "Type", "Options",
         "RegEx", "Value", "Group", "Events" ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", conf.mySettingsSQLsafe)

    # Used to determine the next import
    conf.lastTimeImported = time.time()

    # Is used to display a message in the UI when old (outdated) settings are loaded    
    initOrSetParam(db, "Back_Settings_Imported",(round(time.time() * 1000),) )    
    
    #commitDB(sql_connection)
    db.commitDB()

    #  update only the settings datasource
    update_api(db, False, ["settings"])  
    #TO DO this creates a circular reference between API and HELPER !

    mylog('info', '[Config] Imported new config')



#-------------------------------------------------------------------------------
def read_config_file(filename):
    """
    retuns dict on the config file key:value pairs
    """
    mylog('info', '[Config] reading config file')
    # load the variables from  pialert.conf
    code = compile(filename.read_text(), filename.name, "exec")
    confDict = {} # config dictionary
    exec(code, {"__builtins__": {}}, confDict)
    return confDict 