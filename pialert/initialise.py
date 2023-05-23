
import os
import time
from pytz import timezone
from cron_converter import Cron
from pathlib import Path
import datetime

from conf import *
from const import *
from helper import collect_lang_strings, schedule_class, timeNow, updateSubnets, initOrSetParam
from logger import mylog
from plugin import get_plugins_configs, print_plugin_info

#===============================================================================
# Initialise user defined values
#===============================================================================
# We need access to the DB to save new values so need to define DB access methods first
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Import user values
# Check config dictionary
def ccd(key, default, config, name, inputtype, options, group, events=[], desc = "", regex = ""):
    result = default

    # use existing value if already supplied, otherwise default value is used
    if key in config:
        result =  config[key]

    if inputtype == 'text':
        result = result.replace('\'', "{s-quote}")

    mySettingsSQLsafe.append((key, name, desc, inputtype, options, regex, str(result), group, str(events)))
    mySettings.append((key, name, desc, inputtype, options, regex, result, group, str(events)))

    return result
#-------------------------------------------------------------------------------

def importConfigs (db): 

    sql = db.sql

    # Specify globals so they can be overwritten with the new config
    global lastTimeImported, mySettings, mySettingsSQLsafe, plugins, plugins_once_run
    lastTimeImported = 0
    # General
    global ENABLE_ARPSCAN, SCAN_SUBNETS, LOG_LEVEL, TIMEZONE, ENABLE_PLUGINS, PIALERT_WEB_PROTECTION, PIALERT_WEB_PASSWORD, INCLUDED_SECTIONS, SCAN_CYCLE_MINUTES, DAYS_TO_KEEP_EVENTS, REPORT_DASHBOARD_URL, DIG_GET_IP_ARG, UI_LANG
    # Email
    global REPORT_MAIL, SMTP_SERVER, SMTP_PORT, REPORT_TO, REPORT_FROM, SMTP_SKIP_LOGIN, SMTP_USER, SMTP_PASS, SMTP_SKIP_TLS, SMTP_FORCE_SSL
    # Webhooks
    global REPORT_WEBHOOK, WEBHOOK_URL, WEBHOOK_PAYLOAD, WEBHOOK_REQUEST_METHOD
    # Apprise
    global REPORT_APPRISE, APPRISE_HOST, APPRISE_URL, APPRISE_PAYLOAD
    # NTFY
    global REPORT_NTFY, NTFY_HOST, NTFY_TOPIC, NTFY_USER, NTFY_PASSWORD
    # PUSHSAFER
    global REPORT_PUSHSAFER, PUSHSAFER_TOKEN
    # MQTT
    global REPORT_MQTT,  MQTT_BROKER, MQTT_PORT, MQTT_USER, MQTT_PASSWORD, MQTT_QOS, MQTT_DELAY_SEC
    # DynDNS
    global DDNS_ACTIVE, DDNS_DOMAIN, DDNS_USER, DDNS_PASSWORD, DDNS_UPDATE_URL
    # PiHole
    global PIHOLE_ACTIVE, DHCP_ACTIVE
    # Pholus
    global PHOLUS_ACTIVE, PHOLUS_TIMEOUT, PHOLUS_FORCE, PHOLUS_DAYS_DATA, PHOLUS_RUN, PHOLUS_RUN_SCHD, PHOLUS_RUN_TIMEOUT
    # Nmap
    global NMAP_ACTIVE, NMAP_TIMEOUT, NMAP_RUN, NMAP_RUN_SCHD, NMAP_ARGS 
    # API
    global API_CUSTOM_SQL

    # get config file
    config_file = Path(fullConfPath)

    # Skip import if last time of import is NEWER than file age 
    if (os.path.getmtime(config_file) < lastTimeImported) :
        return
        
    mySettings = [] # reset settings
    mySettingsSQLsafe = [] # same as above but safe to be passed into a SQL query
    
    # load the variables from  pialert.conf
    code = compile(config_file.read_text(), config_file.name, "exec")
    c_d = {} # config dictionary
    exec(code, {"__builtins__": {}}, c_d)

    # Import setting if found in the dictionary
    # General
    ENABLE_ARPSCAN = ccd('ENABLE_ARPSCAN', True , c_d, 'Enable arpscan', 'boolean', '', 'General', ['run']) 
    SCAN_SUBNETS = ccd('SCAN_SUBNETS', ['192.168.1.0/24 --interface=eth1', '192.168.1.0/24 --interface=eth0'] , c_d, 'Subnets to scan', 'subnets', '', 'General')    
    LOG_LEVEL = ccd('LOG_LEVEL', 'verbose' , c_d, 'Log verboseness', 'selecttext', "['none', 'minimal', 'verbose', 'debug']", 'General')
    TIMEZONE = ccd('TIMEZONE', 'Europe/Berlin' , c_d, 'Time zone', 'text', '', 'General')
    ENABLE_PLUGINS = ccd('ENABLE_PLUGINS', True , c_d, 'Enable plugins', 'boolean', '', 'General') 
    PIALERT_WEB_PROTECTION = ccd('PIALERT_WEB_PROTECTION', False , c_d, 'Enable logon', 'boolean', '', 'General')
    PIALERT_WEB_PASSWORD = ccd('PIALERT_WEB_PASSWORD', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92' , c_d, 'Logon password', 'readonly', '', 'General')
    INCLUDED_SECTIONS = ccd('INCLUDED_SECTIONS', ['internet', 'new_devices', 'down_devices', 'events', 'ports']   , c_d, 'Notify on', 'multiselect', "['internet', 'new_devices', 'down_devices', 'events', 'ports', 'plugins']", 'General')
    SCAN_CYCLE_MINUTES = ccd('SCAN_CYCLE_MINUTES', 5 , c_d, 'Scan cycle delay (m)', 'integer', '', 'General')
    DAYS_TO_KEEP_EVENTS = ccd('DAYS_TO_KEEP_EVENTS', 90 , c_d, 'Delete events days', 'integer', '', 'General')
    REPORT_DASHBOARD_URL = ccd('REPORT_DASHBOARD_URL', 'http://pi.alert/' , c_d, 'PiAlert URL', 'text', '', 'General')
    DIG_GET_IP_ARG = ccd('DIG_GET_IP_ARG', '-4 myip.opendns.com @resolver1.opendns.com' , c_d, 'DIG arguments', 'text', '', 'General')
    UI_LANG = ccd('UI_LANG', 'English' , c_d, 'Language Interface', 'selecttext', "['English', 'German', 'Spanish']", 'General')
    UI_PRESENCE = ccd('UI_PRESENCE', ['online', 'offline', 'archived']   , c_d, 'Include in presence', 'multiselect', "['online', 'offline', 'archived']", 'General')    

    # Email
    REPORT_MAIL = ccd('REPORT_MAIL', False , c_d, 'Enable email', 'boolean', '', 'Email', ['test'])
    SMTP_SERVER = ccd('SMTP_SERVER', '' , c_d,'SMTP server URL', 'text', '', 'Email')
    SMTP_PORT = ccd('SMTP_PORT', 587 , c_d, 'SMTP port', 'integer', '', 'Email')
    REPORT_TO = ccd('REPORT_TO', 'user@gmail.com' , c_d, 'Email to', 'text', '', 'Email')
    REPORT_FROM = ccd('REPORT_FROM', 'Pi.Alert <user@gmail.com>' , c_d, 'Email Subject', 'text', '', 'Email')
    SMTP_SKIP_LOGIN = ccd('SMTP_SKIP_LOGIN', False , c_d, 'SMTP skip login', 'boolean', '', 'Email')
    SMTP_USER = ccd('SMTP_USER', '' , c_d, 'SMTP user', 'text', '', 'Email')
    SMTP_PASS = ccd('SMTP_PASS', '' , c_d, 'SMTP password', 'password', '', 'Email')
    SMTP_SKIP_TLS = ccd('SMTP_SKIP_TLS', False , c_d, 'SMTP skip TLS', 'boolean', '', 'Email')
    SMTP_FORCE_SSL = ccd('SMTP_FORCE_SSL', False , c_d, 'Force SSL', 'boolean', '', 'Email')

    # Webhooks
    REPORT_WEBHOOK = ccd('REPORT_WEBHOOK', False , c_d, 'Enable Webhooks', 'boolean', '', 'Webhooks', ['test'])
    WEBHOOK_URL = ccd('WEBHOOK_URL', '' , c_d, 'Target URL', 'text', '', 'Webhooks')
    WEBHOOK_PAYLOAD = ccd('WEBHOOK_PAYLOAD', 'json' , c_d, 'Payload type', 'selecttext', "['json', 'html', 'text']", 'Webhooks')
    WEBHOOK_REQUEST_METHOD = ccd('WEBHOOK_REQUEST_METHOD', 'GET' , c_d, 'Req type', 'selecttext', "['GET', 'POST', 'PUT']", 'Webhooks')

    # Apprise
    REPORT_APPRISE = ccd('REPORT_APPRISE', False , c_d, 'Enable Apprise', 'boolean', '', 'Apprise', ['test'])
    APPRISE_HOST = ccd('APPRISE_HOST', '' , c_d, 'Apprise host URL', 'text', '', 'Apprise')
    APPRISE_URL = ccd('APPRISE_URL', '' , c_d, 'Apprise notification URL', 'text', '', 'Apprise')
    APPRISE_PAYLOAD = ccd('APPRISE_PAYLOAD', 'html' , c_d, 'Payload type', 'selecttext', "['html', 'text']", 'Apprise')

    # NTFY
    REPORT_NTFY = ccd('REPORT_NTFY', False , c_d, 'Enable NTFY', 'boolean', '', 'NTFY', ['test'])
    NTFY_HOST = ccd('NTFY_HOST', 'https://ntfy.sh' , c_d, 'NTFY host URL', 'text', '', 'NTFY')
    NTFY_TOPIC = ccd('NTFY_TOPIC', '' , c_d, 'NTFY topic', 'text', '', 'NTFY')
    NTFY_USER = ccd('NTFY_USER', '' , c_d, 'NTFY user', 'text', '', 'NTFY')
    NTFY_PASSWORD = ccd('NTFY_PASSWORD', '' , c_d, 'NTFY password', 'password', '', 'NTFY')

    # PUSHSAFER
    REPORT_PUSHSAFER = ccd('REPORT_PUSHSAFER', False , c_d, 'Enable PUSHSAFER', 'boolean', '', 'PUSHSAFER', ['test'])
    PUSHSAFER_TOKEN = ccd('PUSHSAFER_TOKEN', 'ApiKey' , c_d, 'PUSHSAFER token', 'text', '', 'PUSHSAFER')

    # MQTT
    REPORT_MQTT = ccd('REPORT_MQTT', False , c_d, 'Enable MQTT', 'boolean', '', 'MQTT')
    MQTT_BROKER = ccd('MQTT_BROKER', '' , c_d, 'MQTT broker', 'text', '', 'MQTT')
    MQTT_PORT = ccd('MQTT_PORT', 1883 , c_d, 'MQTT broker port', 'integer', '', 'MQTT')
    MQTT_USER = ccd('MQTT_USER', '' , c_d, 'MQTT user', 'text', '', 'MQTT')
    MQTT_PASSWORD = ccd('MQTT_PASSWORD', '' , c_d, 'MQTT password', 'password', '', 'MQTT')
    MQTT_QOS = ccd('MQTT_QOS', 0 , c_d, 'MQTT Quality of Service', 'selectinteger', "['0', '1', '2']", 'MQTT')
    MQTT_DELAY_SEC = ccd('MQTT_DELAY_SEC', 2 , c_d, 'MQTT delay', 'selectinteger', "['2', '3', '4', '5']", 'MQTT')

    # DynDNS
    DDNS_ACTIVE = ccd('DDNS_ACTIVE', False , c_d, 'Enable DynDNS', 'boolean', '', 'DynDNS')
    DDNS_DOMAIN = ccd('DDNS_DOMAIN', 'your_domain.freeddns.org' , c_d, 'DynDNS domain URL', 'text', '', 'DynDNS')
    DDNS_USER = ccd('DDNS_USER', 'dynu_user' , c_d, 'DynDNS user', 'text', '', 'DynDNS')
    DDNS_PASSWORD = ccd('DDNS_PASSWORD', 'A0000000B0000000C0000000D0000000' , c_d, 'DynDNS password', 'password', '', 'DynDNS')
    DDNS_UPDATE_URL = ccd('DDNS_UPDATE_URL', 'https://api.dynu.com/nic/update?' , c_d, 'DynDNS update URL', 'text', '', 'DynDNS')

    # PiHole
    PIHOLE_ACTIVE = ccd('PIHOLE_ACTIVE',  False, c_d, 'Enable PiHole mapping', 'boolean', '', 'PiHole')
    DHCP_ACTIVE = ccd('DHCP_ACTIVE', False , c_d, 'Enable PiHole DHCP', 'boolean', '', 'PiHole')

    # PHOLUS
    PHOLUS_ACTIVE = ccd('PHOLUS_ACTIVE', False , c_d, 'Enable Pholus scans', 'boolean', '', 'Pholus')
    PHOLUS_TIMEOUT = ccd('PHOLUS_TIMEOUT', 20 , c_d, 'Pholus timeout', 'integer', '', 'Pholus')
    PHOLUS_FORCE = ccd('PHOLUS_FORCE', False , c_d, 'Pholus force check', 'boolean', '', 'Pholus')
    PHOLUS_RUN = ccd('PHOLUS_RUN', 'once' , c_d, 'Pholus enable schedule', 'selecttext', "['none', 'once', 'schedule']", 'Pholus')
    PHOLUS_RUN_TIMEOUT = ccd('PHOLUS_RUN_TIMEOUT', 600 , c_d, 'Pholus timeout schedule', 'integer', '', 'Pholus')   
    PHOLUS_RUN_SCHD = ccd('PHOLUS_RUN_SCHD', '0 4 * * *' , c_d, 'Pholus schedule', 'text', '', 'Pholus')
    PHOLUS_DAYS_DATA = ccd('PHOLUS_DAYS_DATA', 0 , c_d, 'Pholus keep days', 'integer', '', 'Pholus')
    
    # Nmap
    NMAP_ACTIVE = ccd('NMAP_ACTIVE', True , c_d, 'Enable Nmap scans', 'boolean', '', 'Nmap')
    NMAP_TIMEOUT = ccd('NMAP_TIMEOUT', 150 , c_d, 'Nmap timeout', 'integer', '', 'Nmap')
    NMAP_RUN = ccd('NMAP_RUN', 'none' , c_d, 'Nmap enable schedule', 'selecttext', "['none', 'once', 'schedule']", 'Nmap')
    NMAP_RUN_SCHD = ccd('NMAP_RUN_SCHD', '0 2 * * *' , c_d, 'Nmap schedule', 'text', '', 'Nmap')
    NMAP_ARGS = ccd('NMAP_ARGS', '-p -10000' , c_d, 'Nmap custom arguments', 'text', '', 'Nmap')

    # API     
    API_CUSTOM_SQL = ccd('API_CUSTOM_SQL', 'SELECT * FROM Devices WHERE dev_PresentLastScan = 0' , c_d, 'Custom endpoint', 'text', '', 'API')

    # Prepare scheduler
    global tz, mySchedules, plugins

    #  Init timezone in case it changed
    tz = timezone(TIMEZONE) 

    # reset schedules
    mySchedules = [] 

    # init pholus schedule
    pholusSchedule = Cron(PHOLUS_RUN_SCHD).schedule(start_date=datetime.datetime.now(tz))    
    mySchedules.append(schedule_class("pholus", pholusSchedule, pholusSchedule.next(), False))

    # init nmap schedule
    nmapSchedule = Cron(NMAP_RUN_SCHD).schedule(start_date=datetime.datetime.now(tz))
    mySchedules.append(schedule_class("nmap", nmapSchedule, nmapSchedule.next(), False))

    # Format and prepare the list of subnets
    userSubnets = updateSubnets(SCAN_SUBNETS)



    # Plugins START
    # -----------------
    if ENABLE_PLUGINS:
        plugins = get_plugins_configs()

        mylog('none', ['[', timeNow(), '] Plugins: Number of dynamically loaded plugins: ', len(plugins)])

        #  handle plugins
        for plugin in plugins:
            print_plugin_info(plugin, ['display_name','description'])
            
            pref = plugin["unique_prefix"]   

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
                    newSchedule = Cron(v).schedule(start_date=datetime.datetime.now(tz))
                    mySchedules.append(schedule_class(pref, newSchedule, newSchedule.next(), False))

                # Collect settings related language strings
                collect_lang_strings(db, set,  pref + "_" + set["function"])

        plugins_once_run = False
    # -----------------
    # Plugins END

    
           
    

    # Insert settings into the DB    
    sql.execute ("DELETE FROM Settings")    
    sql.executemany ("""INSERT INTO Settings ("Code_Name", "Display_Name", "Description", "Type", "Options",
         "RegEx", "Value", "Group", "Events" ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", mySettingsSQLsafe)

    # Used to determine the next import
    lastTimeImported = time.time()

    # Is used to display a message in the UI when old (outdated) settings are loaded    
    initOrSetParam(db, "Back_Settings_Imported",(round(time.time() * 1000),) )    
    
    #commitDB(sql_connection)
    db.commitDB()

    #  update only the settings datasource
    # update_api(False, ["settings"])  
    # TO DO this creates a circular reference between API and HELPER !

    mylog('info', ['[', timeNow(), '] Config: Imported new config'])  

