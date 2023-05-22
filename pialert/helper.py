""" Colection of generic functions to support Pi.Alert """

import datetime
import os
import re
import subprocess
from cron_converter import Cron
from pytz import timezone
from datetime import timedelta
import json
import time
from pathlib import Path
import requests




from const import *
from logger import mylog, logResult, print_log
from conf import tz
from files import write_file
# from api import update_api  # to avoid circular reference
from plugin import get_plugins_configs, get_setting, print_plugin_info


#-------------------------------------------------------------------------------
def timeNow():
    return datetime.datetime.now().replace(microsecond=0)

#-------------------------------------------------------------------------------
def updateSubnets(SCAN_SUBNETS):

    #  remove old list
    userSubnets = []  

    # multiple interfaces
    if type(SCAN_SUBNETS) is list:        
        for interface in SCAN_SUBNETS :            
            userSubnets.append(interface)
    # one interface only
    else:        
        userSubnets.append(SCAN_SUBNETS)    



#-------------------------------------------------------------------------------
# check RW access of DB and config file
def checkPermissionsOK():
    #global confR_access, confW_access, dbR_access, dbW_access
    
    confR_access = (os.access(fullConfPath, os.R_OK))
    confW_access = (os.access(fullConfPath, os.W_OK))
    dbR_access = (os.access(fullDbPath, os.R_OK))
    dbW_access = (os.access(fullDbPath, os.W_OK))


    mylog('none', ['\n Permissions check (All should be True)'])
    mylog('none', ['------------------------------------------------'])
    mylog('none', [ "  " , confPath ,     " | " , " READ  | " , confR_access])
    mylog('none', [ "  " , confPath ,     " | " , " WRITE | " , confW_access])
    mylog('none', [ "  " , dbPath , "       | " , " READ  | " , dbR_access])
    mylog('none', [ "  " , dbPath , "       | " , " WRITE | " , dbW_access])
    mylog('none', ['------------------------------------------------'])

    #return dbR_access and dbW_access and confR_access and confW_access 
    return (confR_access, dbR_access) 
#-------------------------------------------------------------------------------
def fixPermissions():
    # Try fixing access rights if needed
    chmodCommands = []
    
    chmodCommands.append(['sudo', 'chmod', 'a+rw', '-R', fullDbPath])    
    chmodCommands.append(['sudo', 'chmod', 'a+rw', '-R', fullConfPath])

    for com in chmodCommands:
        # Execute command
        mylog('none', ["[Setup] Attempting to fix permissions."])
        try:
            # try runnning a subprocess
            result = subprocess.check_output (com, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            # An error occured, handle it
            mylog('none', ["[Setup] Fix Failed. Execute this command manually inside of the container: ", ' '.join(com)]) 
            mylog('none', [e.output])


#-------------------------------------------------------------------------------
def initialiseFile(pathToCheck, defaultFile):
    # if file not readable (missing?) try to copy over the backed-up (default) one
    if str(os.access(pathToCheck, os.R_OK)) == "False":
        mylog('none', ["[Setup] ("+ pathToCheck +") file is not readable or missing. Trying to copy over the default one."])
        try:
            # try runnning a subprocess
            p = subprocess.Popen(["cp", defaultFile , pathToCheck], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            stdout, stderr = p.communicate()

            if str(os.access(pathToCheck, os.R_OK)) == "False":
                mylog('none', ["[Setup] Error copying ("+defaultFile+") to ("+pathToCheck+"). Make sure the app has Read & Write access to the parent directory."])
            else:
                mylog('none', ["[Setup] ("+defaultFile+") copied over successfully to ("+pathToCheck+")."])

            # write stdout and stderr into .log files for debugging if needed
            logResult (stdout, stderr)  # TO-DO should be changed to mylog
            
        except subprocess.CalledProcessError as e:
            # An error occured, handle it
            mylog('none', ["[Setup] Error copying ("+defaultFile+"). Make sure the app has Read & Write access to " + pathToCheck])
            mylog('none', [e.output])


def filePermissions():
    # check and initialize pialert.conf
    (confR_access, dbR_access) = checkPermissionsOK() # Initial check

    if confR_access == False:
        initialiseFile(fullConfPath, "/home/pi/pialert/back/pialert.conf_bak" )

    # check and initialize pialert.db
    if dbR_access == False:
        initialiseFile(fullDbPath, "/home/pi/pialert/back/pialert.db_bak")

    # last attempt
    fixPermissions()            

#-------------------------------------------------------------------------------
class schedule_class:
    def __init__(self, service, scheduleObject, last_next_schedule, was_last_schedule_used, last_run = 0):
        self.service = service
        self.scheduleObject = scheduleObject
        self.last_next_schedule = last_next_schedule
        self.last_run = last_run
        self.was_last_schedule_used = was_last_schedule_used          
    def runScheduleCheck(self):

        result = False 

        # Initialize the last run time if never run before
        if self.last_run == 0:
            self.last_run =  (datetime.datetime.now(tz) - timedelta(days=365)).replace(microsecond=0)

        # get the current time with the currently specified timezone
        nowTime = datetime.datetime.now(tz).replace(microsecond=0)

        # Run the schedule if the current time is past the schedule time we saved last time and 
        #               (maybe the following check is unnecessary:)
        # if the last run is past the last time we run a scheduled Pholus scan
        if nowTime > self.last_next_schedule and self.last_run < self.last_next_schedule:
            print_log(f'Scheduler run for {self.service}: YES')
            self.was_last_schedule_used = True
            result = True
        else:
            print_log(f'Scheduler run for {self.service}: NO')
        
        if self.was_last_schedule_used:
            self.was_last_schedule_used = False
            self.last_next_schedule = self.scheduleObject.next()            

        return result
    
  


#-------------------------------------------------------------------------------

def bytes_to_string(value):
    # if value is of type bytes, convert to string
    if isinstance(value, bytes):
        value = value.decode('utf-8')
    return value        

#-------------------------------------------------------------------------------

def if_byte_then_to_str(input):
    if isinstance(input, bytes):
        input = input.decode('utf-8')
        input = bytes_to_string(re.sub('[^a-zA-Z0-9-_\s]', '', str(input)))
    return input

#-------------------------------------------------------------------------------
def collect_lang_strings(db, json, pref):

    for prop in json["localized"]:                   
        for language_string in json[prop]:
            import_language_string(db, language_string["language_code"], pref + "_" + prop, language_string["string"])       


#-------------------------------------------------------------------------------
def initOrSetParam(db, parID, parValue):    
    sql_connection = db.sql_connection
    sql = db.sql

    sql.execute ("INSERT INTO Parameters(par_ID, par_Value) VALUES('"+str(parID)+"', '"+str(parValue)+"') ON CONFLICT(par_ID) DO UPDATE SET par_Value='"+str(parValue)+"' where par_ID='"+str(parID)+"'")        

    db.commitDB()


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


#-------------------------------------------------------------------------------
class json_struc:
    def __init__(self, jsn, columnNames):        
        self.json = jsn
        self.columnNames = columnNames      

#-------------------------------------------------------------------------------
#  Creates a JSON object from a DB row
def row_to_json(names, row):  
    
    rowEntry = {}

    index = 0
    for name in names:
        rowEntry[name]= if_byte_then_to_str(row[name])
        index += 1

    return rowEntry

#-------------------------------------------------------------------------------
def import_language_string(db, code, key, value, extra = ""):

    db.sql.execute ("""INSERT INTO Plugins_Language_Strings ("Language_Code", "String_Key", "String_Value", "Extra") VALUES (?, ?, ?, ?)""", (str(code), str(key), str(value), str(extra))) 

    db.commitDB()



#-------------------------------------------------------------------------------
# Make a regular expression
# for validating an Ip-address
ipRegex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"

# Define a function to
# validate an Ip address
def checkIPV4(ip):
    # pass the regular expression
    # and the string in search() method
    if(re.search(ipRegex, ip)):
        return True
    else:
        return False


#-------------------------------------------------------------------------------
def isNewVersion(db):   
    global newVersionAvailable

    if newVersionAvailable == False:    

        f = open(pialertPath + '/front/buildtimestamp.txt', 'r') 
        buildTimestamp = int(f.read().strip())
        f.close() 

        data = ""

        try:
            url = requests.get("https://api.github.com/repos/jokob-sk/Pi.Alert/releases")
            text = url.text
            data = json.loads(text)
        except requests.exceptions.ConnectionError as e:
            mylog('info', ["    Couldn't check for new release."]) 
            data = ""
        
        # make sure we received a valid response and not an API rate limit exceeded message
        if data != "" and len(data) > 0 and isinstance(data, list) and "published_at" in data[0]:        

            dateTimeStr = data[0]["published_at"]            

            realeaseTimestamp = int(datetime.datetime.strptime(dateTimeStr, '%Y-%m-%dT%H:%M:%SZ').strftime('%s'))            

            if realeaseTimestamp > buildTimestamp + 600:        
                mylog('none', ["    New version of the container available!"])
                newVersionAvailable = True 
                # updateState(db, 'Back_New_Version_Available', str(newVersionAvailable))     ## TO DO add this back in but avoid circular ref with database

    return newVersionAvailable

#-------------------------------------------------------------------------------
def hide_email(email):
    m = email.split('@')

    if len(m) == 2:
        return f'{m[0][0]}{"*"*(len(m[0])-2)}{m[0][-1] if len(m[0]) > 1 else ""}@{m[1]}'

    return email    

#-------------------------------------------------------------------------------
def removeDuplicateNewLines(text):
    if "\n\n\n" in text:
        return removeDuplicateNewLines(text.replace("\n\n\n", "\n\n"))
    else:
        return text

#-------------------------------------------------------------------------------

def add_json_list (row, list):
    new_row = []
    for column in row :        
        column = bytes_to_string(column)

        new_row.append(column)

    list.append(new_row)    

    return list        

#-------------------------------------------------------------------------------

def sanitize_string(input):
    if isinstance(input, bytes):
        input = input.decode('utf-8')
    value = bytes_to_string(re.sub('[^a-zA-Z0-9-_\s]', '', str(input)))
    return value


#-------------------------------------------------------------------------------
def generate_mac_links (html, deviceUrl):

    p = re.compile(r'(?:[0-9a-fA-F]:?){12}')

    MACs = re.findall(p, html)

    for mac in MACs:        
        html = html.replace('<td>' + mac + '</td>','<td><a href="' + deviceUrl + mac + '">' + mac + '</a></td>')

    return html