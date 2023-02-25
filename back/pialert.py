#!/usr/bin/env python
#
#-------------------------------------------------------------------------------
#  Pi.Alert  v2.70  /  2021-02-01
#  Open Source Network Guard / WIFI & LAN intrusion detector 
#
#  pialert.py - Back module. Network scanner
#-------------------------------------------------------------------------------
#  Puche 2021 / 2022+ jokob             jokob@duck.com                GNU GPLv3
#-------------------------------------------------------------------------------


#===============================================================================
# IMPORTS
#===============================================================================
from __future__ import print_function
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import sys
from collections import namedtuple
import subprocess
import os
import re
import time
import decimal
import datetime
from datetime import timedelta
import sqlite3
import socket
import io
import smtplib
import csv
import json
import requests
from base64 import b64encode
from paho.mqtt import client as mqtt_client
import threading
from pathlib import Path
from cron_converter import Cron
from pytz import timezone
from json2table import convert

#===============================================================================
# SQL queries
#===============================================================================

sql_devices_all = "select dev_MAC, dev_Name, dev_DeviceType, dev_Vendor, dev_Group, dev_FirstConnection, dev_LastConnection, dev_LastIP, dev_StaticIP, dev_PresentLastScan, dev_LastNotification, dev_NewDevice, dev_Network_Node_MAC_ADDR, dev_Network_Node_port,  dev_Icon from Devices"
sql_devices_stats =  "SELECT Online_Devices as online, Down_Devices as down, All_Devices as 'all', Archived_Devices as archived, (select count(*) from Devices a where dev_NewDevice = 1 ) as new, (select count(*) from Devices a where dev_Name = '(unknown)' or dev_Name = '(name not found)' ) as unknown from Online_History order by Scan_Date desc limit  1"
sql_nmap_scan_all = "SELECT  * FROM Nmap_Scan"
sql_pholus_scan_all = "SELECT  * FROM Pholus_Scan"
sql_events_pending_alert = "SELECT  * FROM Events where eve_PendingAlertEmail is not 0"
sql_settings = "SELECT  * FROM Settings"
sql_plugins_objects = "SELECT  * FROM Plugins_Objects"
sql_language_strings = "SELECT  * FROM Language_Strings"
sql_plugins_events = "SELECT  * FROM Plugins_Events"
sql_new_devices = """SELECT * FROM ( SELECT eve_IP as dev_LastIP, eve_MAC as dev_MAC FROM Events_Devices
                                                                WHERE eve_PendingAlertEmail = 1
                                                                AND eve_EventType = 'New Device'
                                    ORDER BY eve_DateTime ) t1
                                    LEFT JOIN 
                                    (
                                        SELECT dev_Name, dev_MAC as dev_MAC_t2 FROM Devices 
                                    ) t2 
                                    ON t1.dev_MAC = t2.dev_MAC_t2"""

#===============================================================================
# PATHS
#===============================================================================
pialertPath = '/home/pi/pialert'

confPath = "/config/pialert.conf"
dbPath = '/db/pialert.db'

pluginsPath  = pialertPath + '/front/plugins'
logPath      = pialertPath + '/front/log'
fullConfPath = pialertPath + confPath
fullDbPath   = pialertPath + dbPath

vendorsDB              = '/usr/share/arp-scan/ieee-oui.txt'
piholeDB               = '/etc/pihole/pihole-FTL.db'
piholeDhcpleases       = '/etc/pihole/dhcp.leases'

# Global variables

debug_force_notification = False

userSubnets = []
changedPorts_json_struc = None
time_started = datetime.datetime.now()
cron_instance = Cron()
log_timestamp = time_started
lastTimeImported = 0
sql_connection = None

#-------------------------------------------------------------------------------
def timeNow():
    return datetime.datetime.now().replace(microsecond=0)

#-------------------------------------------------------------------------------
debugLevels =   [
                    ('none', 0), ('minimal', 1), ('verbose', 2), ('debug', 3)
                ]
LOG_LEVEL = 'debug'

def mylog(requestedDebugLevel, n):

    setLvl = 0  
    reqLvl = 0  

    #  Get debug urgency/relative weight
    for lvl in debugLevels:
        if LOG_LEVEL == lvl[0]:
            setLvl = lvl[1]
        if requestedDebugLevel == lvl[0]:
            reqLvl = lvl[1]

    if reqLvl <= setLvl:
        file_print (*n)

#-------------------------------------------------------------------------------
def file_print (*args):

    result = ''
    
    file = open(logPath + "/pialert.log", "a")    
    for arg in args:                
        result += str(arg)
    print(result)
    file.write(result + '\n')
    file.close()


#-------------------------------------------------------------------------------
def append_file_binary (pPath, input):    
    file = open (pPath, 'ab') 
    file.write (input) 
    file.close() 

#-------------------------------------------------------------------------------
def logResult (stdout, stderr):
    if stderr != None:
        append_file_binary (logPath + '/stderr.log', stderr)
    if stdout != None:
        append_file_binary (logPath + '/stdout.log', stdout)  

#-------------------------------------------------------------------------------
def print_log (pText):
    global log_timestamp

    # Check LOG actived
    if not LOG_LEVEL == 'debug' :
        return

    # Current Time    
    log_timestamp2 = datetime.datetime.now().replace(microsecond=0)

    # Print line + time + elapsed time + text
    file_print ('[LOG_LEVEL=debug] ',
        # log_timestamp2, ' ',
        log_timestamp2.replace(microsecond=0) - log_timestamp.replace(microsecond=0), ' ',
        pText)

    # Save current time to calculate elapsed time until next log
    log_timestamp = log_timestamp2 

    return pText
    
#-------------------------------------------------------------------------------
# check RW access of DB and config file
def checkPermissionsOK():
    global confR_access, confW_access, dbR_access, dbW_access
    
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

    return dbR_access and dbW_access and confR_access and confW_access 
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


checkPermissionsOK() # Initial check

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
            logResult (stdout, stderr)
            
        except subprocess.CalledProcessError as e:
            # An error occured, handle it
            mylog('none', ["[Setup] Error copying ("+defaultFile+"). Make sure the app has Read & Write access to " + pathToCheck])
            mylog('none', [e.output])

#===============================================================================
# Basic checks and Setup
#===============================================================================

# check and initialize pialert.conf
if confR_access == False:
    initialiseFile(fullConfPath, "/home/pi/pialert/back/pialert.conf_bak" )

# check and initialize pialert.db
if dbR_access == False:
    initialiseFile(fullDbPath, "/home/pi/pialert/back/pialert.db_bak")

# last attempt
fixPermissions()

#===============================================================================
# Initialise user defined values
#===============================================================================
# We need access to the DB to save new values so need to define DB access methods first
#-------------------------------------------------------------------------------

def openDB ():
    global sql_connection
    global sql

    # Check if DB is open
    if sql_connection != None :
        return

    # Log    
    print_log ('Opening DB')

    # Open DB and Cursor
    sql_connection = sqlite3.connect (fullDbPath, isolation_level=None)
    sql_connection.execute('pragma journal_mode=wal') #
    sql_connection.text_factory = str
    sql_connection.row_factory = sqlite3.Row
    sql = sql_connection.cursor()

#-------------------------------------------------------------------------------
def commitDB ():
    global sql_connection
    global sql

    # Check if DB is open
    if sql_connection == None :
        return

    # Log    
    # print_log ('Commiting DB changes')

    # Commit changes to DB
    sql_connection.commit()

#-------------------------------------------------------------------------------
# Import user values
# Check config dictionary
def ccd(key, default, config, name, inputtype, options, group, events=[], desc = "", regex = ""):
    result = default

    # use existing value if already supplied, otehrwise default value is used
    if key in config:
        result =  config[key]

    global mySettings

    if inputtype == 'text':
        result = result.replace('\'', "{s-quote}")

    mySettingsSQLsafe.append((key, name, desc, inputtype, options, regex, str(result), group, str(events)))
    mySettings.append((key, name, desc, inputtype, options, regex, result, group, str(events)))

    return result

#-------------------------------------------------------------------------------

def importConfigs (): 

    # Specify globals so they can be overwritten with the new config
    global lastTimeImported, mySettings, mySettingsSQLsafe, plugins, plugins_once_run
    # General
    global ENABLE_ARPSCAN, SCAN_SUBNETS, LOG_LEVEL, TIMEZONE, PIALERT_WEB_PROTECTION, PIALERT_WEB_PASSWORD, INCLUDED_SECTIONS, SCAN_CYCLE_MINUTES, DAYS_TO_KEEP_EVENTS, REPORT_DASHBOARD_URL, DIG_GET_IP_ARG, UI_LANG
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
    mySettingsSQLsafe = [] # same as aboverr but safe to be passed into a SQL query
    
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
    PIALERT_WEB_PROTECTION = ccd('PIALERT_WEB_PROTECTION', False , c_d, 'Enable logon', 'boolean', '', 'General')
    PIALERT_WEB_PASSWORD = ccd('PIALERT_WEB_PASSWORD', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92' , c_d, 'Logon password', 'readonly', '', 'General')
    INCLUDED_SECTIONS = ccd('INCLUDED_SECTIONS', ['internet', 'new_devices', 'down_devices', 'events', 'ports']   , c_d, 'Notify on', 'multiselect', "['internet', 'new_devices', 'down_devices', 'events', 'ports', 'plugins']", 'General')
    SCAN_CYCLE_MINUTES = ccd('SCAN_CYCLE_MINUTES', 5 , c_d, 'Scan cycle delay (m)', 'integer', '', 'General')
    DAYS_TO_KEEP_EVENTS = ccd('DAYS_TO_KEEP_EVENTS', 90 , c_d, 'Delete events days', 'integer', '', 'General')
    REPORT_DASHBOARD_URL = ccd('REPORT_DASHBOARD_URL', 'http://pi.alert/' , c_d, 'PiAlert URL', 'text', '', 'General')
    DIG_GET_IP_ARG = ccd('DIG_GET_IP_ARG', '-4 myip.opendns.com @resolver1.opendns.com' , c_d, 'DIG arguments', 'text', '', 'General')
    UI_LANG = ccd('UI_LANG', 'English' , c_d, 'Language Interface', 'selecttext', "['English', 'German', 'Spanish']", 'General')

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
    updateSubnets()

    # Plugins START
    # -----------------
    plugins = get_plugins_configs()

    mylog('none', ['[', timeNow(), '] Plugins: Number of dynamically loaded plugins: ', len(plugins.dict)])

    #  handle plugins
    for plugin in plugins.list:
        print_plugin_info(plugin, ['display_name','description'])
        
        pref = plugin["unique_prefix"]    
        
        # collect plugin level language strings
        collect_lang_strings(plugin, pref)
        
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
            collect_lang_strings(set,  pref + "_" + set["function"])
    # -----------------
    # Plugins END

    
           
    plugins_once_run = False

    # Insert settings into the DB    
    sql.execute ("DELETE FROM Settings")    
    sql.executemany ("""INSERT INTO Settings ("Code_Name", "Display_Name", "Description", "Type", "Options",
         "RegEx", "Value", "Group", "Events" ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", mySettingsSQLsafe)

    # Used to determine the next import
    lastTimeImported = time.time()

    # Is used to display a message in the UI when old (outdated) settings are loaded    
    initOrSetParam("Back_Settings_Imported",(round(time.time() * 1000),) )    
    
    commitDB()

    #  update only the settings datasource
    update_api(False, ["settings"])

    mylog('info', ['[', timeNow(), '] Config: Imported new config'])  

#===============================================================================
# MAIN
#===============================================================================
cycle = ""
check_report = [1, "internet_IP", "update_vendors_silent"]
plugins_once_run = False

# timestamps of last execution times
startTime = time_started
now_minus_24h = time_started - datetime.timedelta(hours = 24)

last_network_scan = now_minus_24h
last_internet_IP_scan = now_minus_24h
last_run = now_minus_24h
last_cleanup = now_minus_24h
last_update_vendors = time_started - datetime.timedelta(days = 6) # update vendors 24h after first run and then once a week

# indicates, if a new version is available
newVersionAvailable = False

def main ():
    # Initialize global variables
    global time_started, cycle, last_network_scan, last_internet_IP_scan, last_run, last_cleanup, last_update_vendors
    # second set of global variables
    global startTime, log_timestamp, sql_connection, sql, plugins_once_run

    # DB
    sql_connection = None
    sql            = None

    # Open DB once and keep open
    # Opening / closing DB frequently actually casues more issues
    openDB() # main

    # Upgrade DB if needed
    upgradeDB()

    while True:

        # update time started
        time_started = datetime.datetime.now()

        # re-load user configuration and plugins
        importConfigs()       

        

        # Handle plugins executed ONCE
        if plugins_once_run == False:
            run_plugin_scripts('once')  
            plugins_once_run = True

        # check if there is a front end initiated event which needs to be executed
        check_and_run_event()

        # Update API endpoints              
        update_api()
        
        # proceed if 1 minute passed
        if last_run + datetime.timedelta(minutes=1) < time_started :

             # last time any scan or maintenance/Upkeep was run
            last_run = time_started

            # Header
            updateState("Process: Start")
            mylog('verbose', ['[', timeNow(), '] Process: Start'])                

            # Timestamp
            startTime = time_started
            startTime = startTime.replace (microsecond=0) 

            # Check if any plugins need to run on schedule
            run_plugin_scripts('schedule') 

            # determine run/scan type based on passed time
            # --------------------------------------------

            # check for changes in Internet IP
            if last_internet_IP_scan + datetime.timedelta(minutes=3) < time_started:
                cycle = 'internet_IP'                
                last_internet_IP_scan = time_started
                check_internet_IP()

            # Update vendors once a week
            if last_update_vendors + datetime.timedelta(days = 7) < time_started:
                last_update_vendors = time_started
                cycle = 'update_vendors'
                update_devices_MAC_vendors()

            # Execute scheduled or one-off Pholus scan if enabled and run conditions fulfilled
            if PHOLUS_RUN == "schedule" or PHOLUS_RUN == "once":

                pholusSchedule = [sch for sch in mySchedules if sch.service == "pholus"][0]
                run = False

                # run once after application starts
                if PHOLUS_RUN == "once" and pholusSchedule.last_run == 0:
                    run = True

                # run if overdue scheduled time
                if PHOLUS_RUN == "schedule":
                    run = pholusSchedule.runScheduleCheck()                    

                if run:
                    pholusSchedule.last_run = datetime.datetime.now(tz).replace(microsecond=0)
                    performPholusScan(PHOLUS_RUN_TIMEOUT)
            
            # Execute scheduled or one-off Nmap scan if enabled and run conditions fulfilled
            if NMAP_RUN == "schedule" or NMAP_RUN == "once":

                nmapSchedule = [sch for sch in mySchedules if sch.service == "nmap"][0]
                run = False

                # run once after application starts
                if NMAP_RUN == "once" and nmapSchedule.last_run == 0:
                    run = True

                # run if overdue scheduled time
                if NMAP_RUN == "schedule":
                    run = nmapSchedule.runScheduleCheck()                    

                if run:
                    nmapSchedule.last_run = datetime.datetime.now(tz).replace(microsecond=0)
                    performNmapScan(get_all_devices())
            
            # Perform a network scan via arp-scan or pihole
            if last_network_scan + datetime.timedelta(minutes=SCAN_CYCLE_MINUTES) < time_started:
                last_network_scan = time_started
                cycle = 1 # network scan
                scan_network() 
            
            # Reporting   
            if cycle in check_report:
                # Check if new devices found
                sql.execute (sql_new_devices)
                newDevices = sql.fetchall()
                commitDB()
                
                #  new devices were found
                if len(newDevices) > 0:
                    #  run all plugins registered to be run when new devices are found
                    run_plugin_scripts('on_new_device')

                    #  Scan newly found devices with Nmap if enabled
                    if NMAP_ACTIVE and len(newDevices) > 0:
                        performNmapScan(newDevices)

                # send all configured notifications
                send_notifications()

            # clean up the DB once a day
            if last_cleanup + datetime.timedelta(hours = 24) < time_started:
                last_cleanup = time_started
                cycle = 'cleanup'  
                cleanup_database()   

            # Commit SQL
            commitDB()            
            
            # Final message
            if cycle != "":
                action = str(cycle)
                if action == "1":
                    action = "network_scan"
                mylog('verbose', ['[', timeNow(), '] Last action: ', action])
                cycle = ""
            
            # Footer
            updateState("Process: Wait")
            mylog('verbose', ['[', timeNow(), '] Process: Wait'])            
        else:
            # do something
            cycle = ""           

        #loop     
        time.sleep(5) # wait for N seconds      

    
#===============================================================================
# INTERNET IP CHANGE
#===============================================================================
def check_internet_IP ():   

    # Header
    updateState("Scan: Internet IP")
    mylog('verbose', ['[', startTime, '] Check Internet IP:'])    

    # Get Internet IP
    mylog('verbose', ['    Retrieving Internet IP:'])
    internet_IP = get_internet_IP()
    # TESTING - Force IP
        # internet_IP = "1.2.3.4"

    # Check result = IP
    if internet_IP == "" :
        mylog('none', ['    Error retrieving Internet IP'])
        mylog('none', ['    Exiting...'])
        return False
    mylog('verbose', ['      ', internet_IP])

    # Get previous stored IP
    mylog('verbose', ['    Retrieving previous IP:'])    
    previous_IP = get_previous_internet_IP ()
    mylog('verbose', ['      ', previous_IP])

    # Check IP Change
    if internet_IP != previous_IP :
        mylog('info', ['    New internet IP: ', internet_IP])
        save_new_internet_IP (internet_IP)
        
    else :
        mylog('verbose', ['    No changes to perform'])    

    # Get Dynamic DNS IP
    if DDNS_ACTIVE :
        mylog('verbose', ['    Retrieving Dynamic DNS IP'])
        dns_IP = get_dynamic_DNS_IP()

        # Check Dynamic DNS IP
        if dns_IP == "" :
            mylog('info', ['    Error retrieving Dynamic DNS IP'])
            mylog('info', ['    Exiting...'])
        mylog('info', ['   ', dns_IP])

        # Check DNS Change
        if dns_IP != internet_IP :
            mylog('info', ['    Updating Dynamic DNS IP'])
            message = set_dynamic_DNS_IP ()
            mylog('info', ['       ', message])            
        else :
            mylog('verbose', ['    No changes to perform'])
    else :
        mylog('verbose', ['    Skipping Dynamic DNS update'])



#-------------------------------------------------------------------------------
def get_internet_IP ():
    # BUGFIX #46 - curl http://ipv4.icanhazip.com repeatedly is very slow
    # Using 'dig'
    dig_args = ['dig', '+short'] + DIG_GET_IP_ARG.strip().split()
    try:
        cmd_output = subprocess.check_output (dig_args, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        mylog('none', [e.output])
        cmd_output = '' # no internet

    # Check result is an IP
    IP = check_IP_format (cmd_output)
    return IP

#-------------------------------------------------------------------------------
def get_dynamic_DNS_IP ():
    # Using OpenDNS server
        # dig_args = ['dig', '+short', DDNS_DOMAIN, '@resolver1.opendns.com']

    # Using default DNS server
    dig_args = ['dig', '+short', DDNS_DOMAIN]

    try:
        # try runnning a subprocess
        dig_output = subprocess.check_output (dig_args, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        mylog('none', [e.output])
        dig_output = '' # probably no internet

    # Check result is an IP
    IP = check_IP_format (dig_output)
    return IP

#-------------------------------------------------------------------------------
def set_dynamic_DNS_IP ():
    try:
        # try runnning a subprocess
        # Update Dynamic IP
        curl_output = subprocess.check_output (['curl', '-s',
            DDNS_UPDATE_URL +
            'username='  + DDNS_USER +
            '&password=' + DDNS_PASSWORD +
            '&hostname=' + DDNS_DOMAIN],
            universal_newlines=True)
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        mylog('none', [e.output])
        curl_output = ""    
    
    return curl_output
    
#-------------------------------------------------------------------------------
def get_previous_internet_IP ():
    
    previous_IP = '0.0.0.0'

    # get previous internet IP stored in DB
    sql.execute ("SELECT dev_LastIP FROM Devices WHERE dev_MAC = 'Internet' ")
    result = sql.fetchone()

    commitDB()

    if  result is not None and len(result) > 0 :
        previous_IP = result[0]

    # return previous IP
    return previous_IP

#-------------------------------------------------------------------------------
def save_new_internet_IP (pNewIP):
    # Log new IP into logfile
    append_line_to_file (logPath + '/IP_changes.log',
        '['+str(startTime) +']\t'+ pNewIP +'\n')

    prevIp = get_previous_internet_IP()     
    # Save event
    sql.execute ("""INSERT INTO Events (eve_MAC, eve_IP, eve_DateTime,
                        eve_EventType, eve_AdditionalInfo,
                        eve_PendingAlertEmail)
                    VALUES ('Internet', ?, ?, 'Internet IP Changed',
                        'Previous Internet IP: '|| ?, 1) """,
                    (pNewIP, startTime, prevIp) )

    # Save new IP
    sql.execute ("""UPDATE Devices SET dev_LastIP = ?
                    WHERE dev_MAC = 'Internet' """,
                    (pNewIP,) )

    # commit changes    
    commitDB()
    
#-------------------------------------------------------------------------------
def check_IP_format (pIP):
    # Check IP format
    IPv4SEG  = r'(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])'
    IPv4ADDR = r'(?:(?:' + IPv4SEG + r'\.){3,3}' + IPv4SEG + r')'
    IP = re.search(IPv4ADDR, pIP)

    # Return error if not IP
    if IP is None :
        return ""

    # Return IP
    return IP.group(0)


#===============================================================================
# Cleanup Online History chart
#===============================================================================
def cleanup_database ():
    # Header    
    updateState("Upkeep: Clean DB") 
    mylog('verbose', ['[', startTime, '] Upkeep Database:' ])

    # Cleanup Online History
    mylog('verbose', ['    Online_History: Delete all older than 3 days'])
    sql.execute ("DELETE FROM Online_History WHERE Scan_Date <= date('now', '-3 day')")
    mylog('verbose', ['    Optimize Database'])

    # Cleanup Events
    mylog('verbose', ['    Events: Delete all older than '+str(DAYS_TO_KEEP_EVENTS)+' days'])
    sql.execute ("DELETE FROM Events WHERE eve_DateTime <= date('now', '-"+str(DAYS_TO_KEEP_EVENTS)+" day')")

    # Cleanup Pholus_Scan
    if PHOLUS_DAYS_DATA != 0:
        mylog('verbose', ['    Pholus_Scan: Delete all older than ' + str(PHOLUS_DAYS_DATA) + ' days'])
        sql.execute ("DELETE FROM Pholus_Scan WHERE Time <= date('now', '-"+ str(PHOLUS_DAYS_DATA) +" day')") # improvement possibility: keep at least N per mac
    
    # De-Dupe (de-duplicate - remove duplicate entries) from the Pholus_Scan table    
    mylog('verbose', ['    Pholus_Scan: Delete all duplicates'])
    sql.execute ("""DELETE  FROM Pholus_Scan
                    WHERE rowid > (
                    SELECT MIN(rowid) FROM Pholus_Scan p2  
                    WHERE Pholus_Scan.MAC = p2.MAC
                    AND Pholus_Scan.Value = p2.Value
                    AND Pholus_Scan.Record_Type = p2.Record_Type
                    );""") 

    # De-Dupe (de-duplicate - remove duplicate entries) from the Nmap_Scan table    
    mylog('verbose', ['    Nmap_Scan: Delete all duplicates'])
    sql.execute ("""DELETE  FROM Nmap_Scan
                    WHERE rowid > (
                    SELECT MIN(rowid) FROM Nmap_Scan p2  
                    WHERE Nmap_Scan.MAC = p2.MAC
                    AND Nmap_Scan.Port = p2.Port
                    AND Nmap_Scan.State = p2.State
                    AND Nmap_Scan.Service = p2.Service
                    );""") 
    
    # Shrink DB
    mylog('verbose', ['    Shrink Database'])
    sql.execute ("VACUUM;")

    commitDB()

#===============================================================================
# UPDATE DEVICE MAC VENDORS
#===============================================================================
def update_devices_MAC_vendors (pArg = ''):
    # Header    
    updateState("Upkeep: Vendors")
    mylog('verbose', ['[', startTime, '] Upkeep - Update HW Vendors:' ])

    # Update vendors DB (iab oui)
    mylog('verbose', ['    Updating vendors DB (iab & oui)'])    
    update_args = ['sh', pialertPath + '/update_vendors.sh', pArg]

    try:
        # try runnning a subprocess
        update_output = subprocess.check_output (update_args)
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        mylog('none', ['    FAILED: Updating vendors DB, set LOG_LEVEL=debug for more info'])  
        mylog('none', [e.output])        

    # Initialize variables
    recordsToUpdate = []
    ignored = 0
    notFound = 0

    # All devices loop
    mylog('verbose', ['    Searching devices vendor'])    
    for device in sql.execute ("SELECT * FROM Devices") :
        # Search vendor in HW Vendors DB
        vendor = query_MAC_vendor (device['dev_MAC'])
        if vendor == -1 :
            notFound += 1
        elif vendor == -2 :
            ignored += 1
        else :
            recordsToUpdate.append ([vendor, device['dev_MAC']])
            
    # Print log    
    mylog('verbose', ["    Devices Ignored:  ", ignored])
    mylog('verbose', ["    Vendors Not Found:", notFound])
    mylog('verbose', ["    Vendors updated:  ", len(recordsToUpdate) ])


    # update devices
    sql.executemany ("UPDATE Devices SET dev_Vendor = ? WHERE dev_MAC = ? ",
        recordsToUpdate )

    # Commit DB
    commitDB()

    if len(recordsToUpdate) > 0:
        return True
    else:
        return False

#-------------------------------------------------------------------------------
def query_MAC_vendor (pMAC):
    try :
        # BUGFIX #6 - Fix pMAC parameter as numbers
        pMACstr = str(pMAC)
        
        # Check MAC parameter
        mac = pMACstr.replace (':','')
        if len(pMACstr) != 17 or len(mac) != 12 :
            return -2

        # Search vendor in HW Vendors DB
        mac = mac[0:6]
        grep_args = ['grep', '-i', mac, vendorsDB]
        # Execute command
        try:
            # try runnning a subprocess
            grep_output = subprocess.check_output (grep_args)
        except subprocess.CalledProcessError as e:
            # An error occured, handle it
            mylog('none', [e.output])
            grep_output = "       There was an error, check logs for details"

        # Return Vendor
        vendor = grep_output[7:]
        vendor = vendor.rstrip()
        return vendor

    # not Found
    except subprocess.CalledProcessError :
        return -1
            
#===============================================================================
# SCAN NETWORK
#===============================================================================
def scan_network ():
    reporting = False

    # Header
    updateState("Scan: Network")
    mylog('verbose', ['[', startTime, '] Scan Devices:' ])       

    # # Query ScanCycle properties
    print_log ('Query ScanCycle confinguration')
    scanCycle_data = query_ScanCycle_Data (True)
    if scanCycle_data is None:
        mylog('none', ['\n*************** ERROR ***************'])
        mylog('none', ['ScanCycle %s not found' % cycle ])
        mylog('none', ['    Exiting...\n'])
        return False

    commitDB()

    # ScanCycle data        
    cycle_interval  = scanCycle_data['cic_EveryXmin']
    
    # arp-scan command
    arpscan_devices = []
    if ENABLE_ARPSCAN:    
        mylog('verbose', ['    arp-scan start'])    
        arpscan_devices = execute_arpscan ()
        print_log ('arp-scan ends')

    # Pi-hole method    
    if PIHOLE_ACTIVE :       
        mylog('verbose', ['    Pi-hole start'])        
        copy_pihole_network() 
        commitDB() 

    # DHCP Leases method    
    if DHCP_ACTIVE :        
        mylog('verbose', ['    DHCP Leases start'])        
        read_DHCP_leases () 
        commitDB()

    # Load current scan data
    mylog('verbose', ['  Processing scan results'])     
    save_scanned_devices (arpscan_devices, cycle_interval)    
    
    # Print stats
    print_log ('Print Stats')
    print_scan_stats()
    print_log ('Stats end')

    # Create Events
    mylog('verbose', ['  Updating DB Info'])
    mylog('verbose', ['    Sessions Events (connect / discconnect)'])
    insert_events()

    # Create New Devices
    # after create events -> avoid 'connection' event
    mylog('verbose', ['    Creating new devices'])
    create_new_devices ()

    # Update devices info
    mylog('verbose', ['    Updating Devices Info'])
    update_devices_data_from_scan ()

    # Resolve devices names
    print_log ('    Resolve devices names')
    update_devices_names()

    # Void false connection - disconnections
    mylog('verbose', ['    Voiding false (ghost) disconnections'])
    void_ghost_disconnections ()
  
    # Pair session events (Connection / Disconnection)
    mylog('verbose', ['    Pairing session events (connection / disconnection) '])
    pair_sessions_events()  
  
    # Sessions snapshot
    mylog('verbose', ['    Creating sessions snapshot'])
    create_sessions_snapshot ()

    # Sessions snapshot
    mylog('verbose', ['    Inserting scan results into Online_History'])
    insertOnlineHistory()
  
    # Skip repeated notifications
    mylog('verbose', ['    Skipping repeated notifications'])
    skip_repeated_notifications ()
  
    # Commit changes    
    commitDB()

    # Run splugin scripts which are set to run every timne after a scan finished
    run_plugin_scripts('always_after_scan')

    return reporting

#-------------------------------------------------------------------------------
def query_ScanCycle_Data (pOpenCloseDB = False, cycle = 1):
    # Query Data
    sql.execute ("""SELECT cic_arpscanCycles, cic_EveryXmin
                    FROM ScanCycles
                    WHERE cic_ID = ? """, (cycle,))
    sqlRow = sql.fetchone()

    # Return Row
    return sqlRow

#-------------------------------------------------------------------------------
def execute_arpscan ():

    # output of possible multiple interfaces
    arpscan_output = ""

    # scan each interface
    for interface in userSubnets :            
        arpscan_output += execute_arpscan_on_interface (interface)    
    
    # Search IP + MAC + Vendor as regular expresion
    re_ip = r'(?P<ip>((2[0-5]|1[0-9]|[0-9])?[0-9]\.){3}((2[0-5]|1[0-9]|[0-9])?[0-9]))'
    re_mac = r'(?P<mac>([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2}))'
    re_hw = r'(?P<hw>.*)'
    re_pattern = re.compile (re_ip + '\s+' + re_mac + '\s' + re_hw)

    # Create Userdict of devices
    devices_list = [device.groupdict()
        for device in re.finditer (re_pattern, arpscan_output)]
    
    # Delete duplicate MAC
    unique_mac = [] 
    unique_devices = [] 

    for device in devices_list :
        if device['mac'] not in unique_mac: 
            unique_mac.append(device['mac'])
            unique_devices.append(device)    

    # return list
    return unique_devices

#-------------------------------------------------------------------------------
def execute_arpscan_on_interface (interface):    
    # Prepare command arguments
    subnets = interface.strip().split()
    # Retry is 6 to avoid false offline devices
    arpscan_args = ['sudo', 'arp-scan', '--ignoredups', '--retry=6'] + subnets

    # Execute command
    try:
        # try runnning a subprocess
        result = subprocess.check_output (arpscan_args, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        mylog('none', [e.output])
        result = ""

    return result

#-------------------------------------------------------------------------------
def copy_pihole_network ():

    # Open Pi-hole DB
    sql.execute ("ATTACH DATABASE '"+ piholeDB +"' AS PH")

    # Copy Pi-hole Network table
    sql.execute ("DELETE FROM PiHole_Network")
    sql.execute ("""INSERT INTO PiHole_Network (PH_MAC, PH_Vendor, PH_LastQuery,
                        PH_Name, PH_IP)
                    SELECT hwaddr, macVendor, lastQuery,
                        (SELECT name FROM PH.network_addresses
                         WHERE network_id = id ORDER BY lastseen DESC, ip),
                        (SELECT ip FROM PH.network_addresses
                         WHERE network_id = id ORDER BY lastseen DESC, ip)
                    FROM PH.network
                    WHERE hwaddr NOT LIKE 'ip-%'
                      AND hwaddr <> '00:00:00:00:00:00' """)
    sql.execute ("""UPDATE PiHole_Network SET PH_Name = '(unknown)'
                    WHERE PH_Name IS NULL OR PH_Name = '' """)
    # Close Pi-hole DB
    sql.execute ("DETACH PH")

    return str(sql.rowcount) != "0"

#-------------------------------------------------------------------------------
def read_DHCP_leases ():
    reporting = False
            
    # Read DHCP Leases
    # Bugfix #1 - dhcp.leases: lines with different number of columns (5 col)
    data = []
    with open(piholeDhcpleases, 'r') as f:
        for line in f:
            reporting = True
            row = line.rstrip().split()
            if len(row) == 5 :
                data.append (row)

    # Insert into PiAlert table
    sql.execute ("DELETE FROM DHCP_Leases")
    sql.executemany ("""INSERT INTO DHCP_Leases (DHCP_DateTime, DHCP_MAC,
                            DHCP_IP, DHCP_Name, DHCP_MAC2)
                        VALUES (?, ?, ?, ?, ?)
                     """, data)

    return reporting

#-------------------------------------------------------------------------------
def save_scanned_devices (p_arpscan_devices, p_cycle_interval):
    cycle = 1 # always 1, only one cycle supported

    # Delete previous scan data
    sql.execute ("DELETE FROM CurrentScan WHERE cur_ScanCycle = ?",
                (cycle,))

    if len(p_arpscan_devices) > 0:
        # Insert new arp-scan devices
        sql.executemany ("INSERT INTO CurrentScan (cur_ScanCycle, cur_MAC, "+
                        "    cur_IP, cur_Vendor, cur_ScanMethod) "+
                        "VALUES ("+ str(cycle) + ", :mac, :ip, :hw, 'arp-scan')",
                        p_arpscan_devices) 

    # Insert Pi-hole devices
    sql.execute ("""INSERT INTO CurrentScan (cur_ScanCycle, cur_MAC, 
                        cur_IP, cur_Vendor, cur_ScanMethod)
                    SELECT ?, PH_MAC, PH_IP, PH_Vendor, 'Pi-hole'
                    FROM PiHole_Network
                    WHERE PH_LastQuery >= ?
                      AND NOT EXISTS (SELECT 'X' FROM CurrentScan
                                      WHERE cur_MAC = PH_MAC
                                        AND cur_ScanCycle = ? )""",
                    (cycle,
                     (int(startTime.strftime('%s')) - 60 * p_cycle_interval),
                     cycle) )

    # Check Internet connectivity
    internet_IP = get_internet_IP()
        # TESTING - Force IP
        # internet_IP = ""
    if internet_IP != "" :
        sql.execute ("""INSERT INTO CurrentScan (cur_ScanCycle, cur_MAC, cur_IP, cur_Vendor, cur_ScanMethod)
                        VALUES (?, 'Internet', ?, Null, 'queryDNS') """, (cycle, internet_IP) )

    # #76 Add Local MAC of default local interface
      # BUGFIX #106 - Device that pialert is running
        # local_mac_cmd = ["bash -lc ifconfig `ip route list default | awk {'print $5'}` | grep ether | awk '{print $2}'"]
          # local_mac_cmd = ["/sbin/ifconfig `ip route list default | sort -nk11 | head -1 | awk {'print $5'}` | grep ether | awk '{print $2}'"]
    local_mac_cmd = ["/sbin/ifconfig `ip -o route get 1 | sed 's/^.*dev \\([^ ]*\\).*$/\\1/;q'` | grep ether | awk '{print $2}'"]
    local_mac = subprocess.Popen (local_mac_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0].decode().strip()

    # local_dev_cmd = ["ip -o route get 1 | sed 's/^.*dev \\([^ ]*\\).*$/\\1/;q'"]
    # local_dev = subprocess.Popen (local_dev_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0].decode().strip()
    
    # local_ip_cmd = ["ip route list default | awk {'print $7'}"]
    local_ip_cmd = ["ip -o route get 1 | sed 's/^.*src \\([^ ]*\\).*$/\\1/;q'"]
    local_ip = subprocess.Popen (local_ip_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0].decode().strip()

    # Check if local mac has been detected with other methods
    sql.execute ("SELECT COUNT(*) FROM CurrentScan WHERE cur_ScanCycle = ? AND cur_MAC = ? ", (cycle, local_mac) )
    if sql.fetchone()[0] == 0 :
        sql.execute ("INSERT INTO CurrentScan (cur_ScanCycle, cur_MAC, cur_IP, cur_Vendor, cur_ScanMethod) "+
                     "VALUES ( ?, ?, ?, Null, 'local_MAC') ", (cycle, local_mac, local_ip) )

#-------------------------------------------------------------------------------
def print_scan_stats ():
    # Devices Detected
    sql.execute ("""SELECT COUNT(*) FROM CurrentScan
                    WHERE cur_ScanCycle = ? """,
                    (cycle,))
    mylog('verbose', ['    Devices Detected.......: ', str (sql.fetchone()[0]) ])

    # Devices arp-scan
    sql.execute ("""SELECT COUNT(*) FROM CurrentScan
                    WHERE cur_ScanMethod='arp-scan' AND cur_ScanCycle = ? """,
                    (cycle,))
    mylog('verbose', ['        arp-scan detected..: ', str (sql.fetchone()[0]) ])

    # Devices Pi-hole
    sql.execute ("""SELECT COUNT(*) FROM CurrentScan
                    WHERE cur_ScanMethod='PiHole' AND cur_ScanCycle = ? """,
                    (cycle,))
    mylog('verbose', ['        Pi-hole detected...: +' + str (sql.fetchone()[0]) ])

    # New Devices
    sql.execute ("""SELECT COUNT(*) FROM CurrentScan
                    WHERE cur_ScanCycle = ? 
                      AND NOT EXISTS (SELECT 1 FROM Devices
                                      WHERE dev_MAC = cur_MAC) """,
                    (cycle,))
    mylog('verbose', ['        New Devices........: ' + str (sql.fetchone()[0]) ])

    # Devices in this ScanCycle
    sql.execute ("""SELECT COUNT(*) FROM Devices, CurrentScan
                    WHERE dev_MAC = cur_MAC AND dev_ScanCycle = cur_ScanCycle
                      AND dev_ScanCycle = ? """,
                    (cycle,))
    
    mylog('verbose', ['    Devices in this cycle..: ' + str (sql.fetchone()[0]) ])

    # Down Alerts
    sql.execute ("""SELECT COUNT(*) FROM Devices
                    WHERE dev_AlertDeviceDown = 1
                      AND dev_ScanCycle = ?
                      AND NOT EXISTS (SELECT 1 FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC
                                        AND dev_ScanCycle = cur_ScanCycle) """,
                    (cycle,))
    mylog('verbose', ['        Down Alerts........: ' + str (sql.fetchone()[0]) ])

    # New Down Alerts
    sql.execute ("""SELECT COUNT(*) FROM Devices
                    WHERE dev_AlertDeviceDown = 1
                      AND dev_PresentLastScan = 1
                      AND dev_ScanCycle = ?
                      AND NOT EXISTS (SELECT 1 FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC
                                        AND dev_ScanCycle = cur_ScanCycle) """,
                    (cycle,))
    mylog('verbose', ['        New Down Alerts....: ' + str (sql.fetchone()[0]) ])

    # New Connections
    sql.execute ("""SELECT COUNT(*) FROM Devices, CurrentScan
                    WHERE dev_MAC = cur_MAC AND dev_ScanCycle = cur_ScanCycle
                      AND dev_PresentLastScan = 0
                      AND dev_ScanCycle = ? """,
                    (cycle,))
    mylog('verbose', ['        New Connections....: ' + str ( sql.fetchone()[0]) ])

    # Disconnections
    sql.execute ("""SELECT COUNT(*) FROM Devices
                    WHERE dev_PresentLastScan = 1
                      AND dev_ScanCycle = ?
                      AND NOT EXISTS (SELECT 1 FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC
                                        AND dev_ScanCycle = cur_ScanCycle) """,
                    (cycle,))
    mylog('verbose', ['        Disconnections.....: ' + str ( sql.fetchone()[0]) ])

    # IP Changes
    sql.execute ("""SELECT COUNT(*) FROM Devices, CurrentScan
                    WHERE dev_MAC = cur_MAC AND dev_ScanCycle = cur_ScanCycle
                      AND dev_ScanCycle = ?
                      AND dev_LastIP <> cur_IP """,
                    (cycle,))
    mylog('verbose', ['        IP Changes.........: ' + str ( sql.fetchone()[0]) ])

#-------------------------------------------------------------------------------
def insertOnlineHistory():
    # Add to History
    sql.execute("SELECT * FROM Devices")
    History_All = sql.fetchall()
    History_All_Devices  = len(History_All)

    sql.execute("SELECT * FROM Devices WHERE dev_Archived = 1")
    History_Archived = sql.fetchall()
    History_Archived_Devices  = len(History_Archived)

    sql.execute("""SELECT * FROM CurrentScan WHERE cur_ScanCycle = ? """, (cycle,))
    History_Online = sql.fetchall()
    History_Online_Devices  = len(History_Online)
    History_Offline_Devices = History_All_Devices - History_Archived_Devices - History_Online_Devices
    
    sql.execute ("INSERT INTO Online_History (Scan_Date, Online_Devices, Down_Devices, All_Devices, Archived_Devices) "+
                 "VALUES ( ?, ?, ?, ?, ?)", (startTime, History_Online_Devices, History_Offline_Devices, History_All_Devices, History_Archived_Devices ) )

#-------------------------------------------------------------------------------
def create_new_devices ():
    # arpscan - Insert events for new devices
    print_log ('New devices - 1 Events')
    sql.execute ("""INSERT INTO Events (eve_MAC, eve_IP, eve_DateTime,
                        eve_EventType, eve_AdditionalInfo,
                        eve_PendingAlertEmail)
                    SELECT cur_MAC, cur_IP, ?, 'New Device', cur_Vendor, 1
                    FROM CurrentScan
                    WHERE cur_ScanCycle = ? 
                      AND NOT EXISTS (SELECT 1 FROM Devices
                                      WHERE dev_MAC = cur_MAC) """,
                    (startTime, cycle) ) 

    print_log ('New devices - Insert Connection into session table')
    sql.execute ("""INSERT INTO Sessions (ses_MAC, ses_IP, ses_EventTypeConnection, ses_DateTimeConnection,
                        ses_EventTypeDisconnection, ses_DateTimeDisconnection, ses_StillConnected, ses_AdditionalInfo)
                    SELECT cur_MAC, cur_IP,'Connected',?, NULL , NULL ,1, cur_Vendor
                    FROM CurrentScan 
                    WHERE cur_ScanCycle = ? 
                      AND NOT EXISTS (SELECT 1 FROM Sessions
                                      WHERE ses_MAC = cur_MAC) """,
                    (startTime, cycle) ) 
                    
    # arpscan - Create new devices
    print_log ('New devices - 2 Create devices')
    sql.execute ("""INSERT INTO Devices (dev_MAC, dev_name, dev_Vendor,
                        dev_LastIP, dev_FirstConnection, dev_LastConnection,
                        dev_ScanCycle, dev_AlertEvents, dev_AlertDeviceDown,
                        dev_PresentLastScan)
                    SELECT cur_MAC, '(unknown)', cur_Vendor, cur_IP, ?, ?,
                        1, 1, 0, 1
                    FROM CurrentScan
                    WHERE cur_ScanCycle = ? 
                      AND NOT EXISTS (SELECT 1 FROM Devices
                                      WHERE dev_MAC = cur_MAC) """,
                    (startTime, startTime, cycle) ) 

    # Pi-hole - Insert events for new devices
    # NOT STRICYLY NECESARY (Devices can be created through Current_Scan)
    # Bugfix #2 - Pi-hole devices w/o IP
    print_log ('New devices - 3 Pi-hole Events')
    sql.execute ("""INSERT INTO Events (eve_MAC, eve_IP, eve_DateTime,
                        eve_EventType, eve_AdditionalInfo,
                        eve_PendingAlertEmail)
                    SELECT PH_MAC, IFNULL (PH_IP,'-'), ?, 'New Device',
                        '(Pi-Hole) ' || PH_Vendor, 1
                    FROM PiHole_Network
                    WHERE NOT EXISTS (SELECT 1 FROM Devices
                                      WHERE dev_MAC = PH_MAC) """,
                    (startTime, ) ) 

    # Pi-hole - Create New Devices
    # Bugfix #2 - Pi-hole devices w/o IP
    print_log ('New devices - 4 Pi-hole Create devices')
    sql.execute ("""INSERT INTO Devices (dev_MAC, dev_name, dev_Vendor,
                        dev_LastIP, dev_FirstConnection, dev_LastConnection,
                        dev_ScanCycle, dev_AlertEvents, dev_AlertDeviceDown,
                        dev_PresentLastScan)
                    SELECT PH_MAC, PH_Name, PH_Vendor, IFNULL (PH_IP,'-'),
                        ?, ?, 1, 1, 0, 1
                    FROM PiHole_Network
                    WHERE NOT EXISTS (SELECT 1 FROM Devices
                                      WHERE dev_MAC = PH_MAC) """,
                    (startTime, startTime) ) 

    # DHCP Leases - Insert events for new devices
    print_log ('New devices - 5 DHCP Leases Events')
    sql.execute ("""INSERT INTO Events (eve_MAC, eve_IP, eve_DateTime,
                        eve_EventType, eve_AdditionalInfo,
                        eve_PendingAlertEmail)
                    SELECT DHCP_MAC, DHCP_IP, ?, 'New Device', '(DHCP lease)',1
                    FROM DHCP_Leases
                    WHERE NOT EXISTS (SELECT 1 FROM Devices
                                      WHERE dev_MAC = DHCP_MAC) """,
                    (startTime, ) ) 

    # DHCP Leases - Create New Devices
    print_log ('New devices - 6 DHCP Leases Create devices')
    # BUGFIX #23 - Duplicated MAC in DHCP.Leases
    # TEST - Force Duplicated MAC
        # sql.execute ("""INSERT INTO DHCP_Leases VALUES
        #                 (1610700000, 'TEST1', '10.10.10.1', 'Test 1', '*')""")
        # sql.execute ("""INSERT INTO DHCP_Leases VALUES
        #                 (1610700000, 'TEST2', '10.10.10.2', 'Test 2', '*')""")
    sql.execute ("""INSERT INTO Devices (dev_MAC, dev_name, dev_LastIP, 
                        dev_Vendor, dev_FirstConnection, dev_LastConnection,
                        dev_ScanCycle, dev_AlertEvents, dev_AlertDeviceDown,
                        dev_PresentLastScan)
                    SELECT DISTINCT DHCP_MAC,
                        (SELECT DHCP_Name FROM DHCP_Leases AS D2
                         WHERE D2.DHCP_MAC = D1.DHCP_MAC
                         ORDER BY DHCP_DateTime DESC LIMIT 1),
                        (SELECT DHCP_IP FROM DHCP_Leases AS D2
                         WHERE D2.DHCP_MAC = D1.DHCP_MAC
                         ORDER BY DHCP_DateTime DESC LIMIT 1),
                        '(unknown)', ?, ?, 1, 1, 0, 1
                    FROM DHCP_Leases AS D1
                    WHERE NOT EXISTS (SELECT 1 FROM Devices
                                      WHERE dev_MAC = DHCP_MAC) """,
                    (startTime, startTime) ) 

    # sql.execute ("""INSERT INTO Devices (dev_MAC, dev_name, dev_Vendor,
    #                     dev_LastIP, dev_FirstConnection, dev_LastConnection,
    #                     dev_ScanCycle, dev_AlertEvents, dev_AlertDeviceDown,
    #                     dev_PresentLastScan)
    #                 SELECT DHCP_MAC, DHCP_Name, '(unknown)', DHCP_IP, ?, ?,
    #                     1, 1, 0, 1
    #                 FROM DHCP_Leases
    #                 WHERE NOT EXISTS (SELECT 1 FROM Devices
    #                                   WHERE dev_MAC = DHCP_MAC) """,
    #                 (startTime, startTime) ) 
    print_log ('New Devices end')

#-------------------------------------------------------------------------------
def insert_events ():
    # Check device down
    print_log ('Events 1 - Devices down')
    sql.execute ("""INSERT INTO Events (eve_MAC, eve_IP, eve_DateTime,
                        eve_EventType, eve_AdditionalInfo,
                        eve_PendingAlertEmail)
                    SELECT dev_MAC, dev_LastIP, ?, 'Device Down', '', 1
                    FROM Devices
                    WHERE dev_AlertDeviceDown = 1
                      AND dev_PresentLastScan = 1
                      AND dev_ScanCycle = ?
                      AND NOT EXISTS (SELECT 1 FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC
                                        AND dev_ScanCycle = cur_ScanCycle) """,
                    (startTime, cycle) )

    # Check new connections
    print_log ('Events 2 - New Connections')
    sql.execute ("""INSERT INTO Events (eve_MAC, eve_IP, eve_DateTime,
                        eve_EventType, eve_AdditionalInfo,
                        eve_PendingAlertEmail)
                    SELECT cur_MAC, cur_IP, ?, 'Connected', '', dev_AlertEvents
                    FROM Devices, CurrentScan
                    WHERE dev_MAC = cur_MAC AND dev_ScanCycle = cur_ScanCycle
                      AND dev_PresentLastScan = 0
                      AND dev_ScanCycle = ? """,
                    (startTime, cycle) )

    # Check disconnections
    print_log ('Events 3 - Disconnections')
    sql.execute ("""INSERT INTO Events (eve_MAC, eve_IP, eve_DateTime,
                        eve_EventType, eve_AdditionalInfo,
                        eve_PendingAlertEmail)
                    SELECT dev_MAC, dev_LastIP, ?, 'Disconnected', '',
                        dev_AlertEvents
                    FROM Devices
                    WHERE dev_AlertDeviceDown = 0
                      AND dev_PresentLastScan = 1
                      AND dev_ScanCycle = ?
                      AND NOT EXISTS (SELECT 1 FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC
                                        AND dev_ScanCycle = cur_ScanCycle) """,
                    (startTime, cycle) )

    # Check IP Changed
    print_log ('Events 4 - IP Changes')
    sql.execute ("""INSERT INTO Events (eve_MAC, eve_IP, eve_DateTime,
                        eve_EventType, eve_AdditionalInfo,
                        eve_PendingAlertEmail)
                    SELECT cur_MAC, cur_IP, ?, 'IP Changed',
                        'Previous IP: '|| dev_LastIP, dev_AlertEvents
                    FROM Devices, CurrentScan
                    WHERE dev_MAC = cur_MAC AND dev_ScanCycle = cur_ScanCycle
                      AND dev_ScanCycle = ?
                      AND dev_LastIP <> cur_IP """,
                    (startTime, cycle) )
    print_log ('Events end')

#-------------------------------------------------------------------------------
def update_devices_data_from_scan ():
    # Update Last Connection
    print_log ('Update devices - 1 Last Connection')
    sql.execute ("""UPDATE Devices SET dev_LastConnection = ?,
                        dev_PresentLastScan = 1
                    WHERE dev_ScanCycle = ?
                      AND dev_PresentLastScan = 0
                      AND EXISTS (SELECT 1 FROM CurrentScan 
                                  WHERE dev_MAC = cur_MAC
                                    AND dev_ScanCycle = cur_ScanCycle) """,
                    (startTime, cycle))

    # Clean no active devices
    print_log ('Update devices - 2 Clean no active devices')
    sql.execute ("""UPDATE Devices SET dev_PresentLastScan = 0
                    WHERE dev_ScanCycle = ?
                      AND NOT EXISTS (SELECT 1 FROM CurrentScan 
                                      WHERE dev_MAC = cur_MAC
                                        AND dev_ScanCycle = cur_ScanCycle) """,
                    (cycle,))

    # Update IP & Vendor
    print_log ('Update devices - 3 LastIP & Vendor')
    sql.execute ("""UPDATE Devices
                    SET dev_LastIP = (SELECT cur_IP FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC
                                        AND dev_ScanCycle = cur_ScanCycle),
                        dev_Vendor = (SELECT cur_Vendor FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC
                                        AND dev_ScanCycle = cur_ScanCycle)
                    WHERE dev_ScanCycle = ?
                      AND EXISTS (SELECT 1 FROM CurrentScan
                                  WHERE dev_MAC = cur_MAC
                                    AND dev_ScanCycle = cur_ScanCycle) """,
                    (cycle,)) 

    # Pi-hole Network - Update (unknown) Name
    print_log ('Update devices - 4 Unknown Name')
    sql.execute ("""UPDATE Devices
                    SET dev_NAME = (SELECT PH_Name FROM PiHole_Network
                                    WHERE PH_MAC = dev_MAC)
                    WHERE (dev_Name = "(unknown)"
                           OR dev_Name = ""
                           OR dev_Name IS NULL)
                      AND EXISTS (SELECT 1 FROM PiHole_Network
                                  WHERE PH_MAC = dev_MAC
                                    AND PH_NAME IS NOT NULL
                                    AND PH_NAME <> '') """)

    # DHCP Leases - Update (unknown) Name
    sql.execute ("""UPDATE Devices
                    SET dev_NAME = (SELECT DHCP_Name FROM DHCP_Leases
                                    WHERE DHCP_MAC = dev_MAC)
                    WHERE (dev_Name = "(unknown)"
                           OR dev_Name = ""
                           OR dev_Name IS NULL)
                      AND EXISTS (SELECT 1 FROM DHCP_Leases
                                  WHERE DHCP_MAC = dev_MAC)""")

    # DHCP Leases - Vendor
    print_log ('Update devices - 5 Vendor')

    recordsToUpdate = []
    query = """SELECT * FROM Devices
               WHERE dev_Vendor = '(unknown)' OR dev_Vendor =''
                  OR dev_Vendor IS NULL"""

    for device in sql.execute (query) :
        vendor = query_MAC_vendor (device['dev_MAC'])
        if vendor != -1 and vendor != -2 :
            recordsToUpdate.append ([vendor, device['dev_MAC']])

    sql.executemany ("UPDATE Devices SET dev_Vendor = ? WHERE dev_MAC = ? ",
        recordsToUpdate )

    print_log ('Update devices end')

#-------------------------------------------------------------------------------
def update_devices_names ():
    # Initialize variables
    recordsToUpdate = []
    recordsNotFound = []

    ignored = 0
    notFound = 0

    foundDig = 0
    foundPholus = 0

    # BUGFIX #97 - Updating name of Devices w/o IP    
    sql.execute ("SELECT * FROM Devices WHERE dev_Name IN ('(unknown)','', '(name not found)') AND dev_LastIP <> '-'")
    unknownDevices = sql.fetchall() 
    commitDB()

    # perform Pholus scan if (unknown) devices found
    if PHOLUS_ACTIVE and (len(unknownDevices) > 0 or PHOLUS_FORCE):        
        performPholusScan(PHOLUS_TIMEOUT)

    # skip checks if no unknown devices
    if len(unknownDevices) == 0 and PHOLUS_FORCE == False:
        return

    # Devices without name
    mylog('verbose', ['        Trying to resolve devices without name'])

    # get names from Pholus scan 
    sql.execute ('SELECT * FROM Pholus_Scan where "Record_Type"="Answer"')    
    pholusResults = list(sql.fetchall())        
    commitDB()

    # Number of entries from previous Pholus scans
    mylog('verbose', ["          Pholus entries from prev scans: ", len(pholusResults)])

    for device in unknownDevices:
        newName = -1
        
        # Resolve device name with DiG
        newName = resolve_device_name_dig (device['dev_MAC'], device['dev_LastIP'])
        
        # count
        if newName != -1:
            foundDig += 1

        # Resolve with Pholus 
        if newName == -1:
            newName =  resolve_device_name_pholus (device['dev_MAC'], device['dev_LastIP'], pholusResults)
            # count
            if newName != -1:
                foundPholus += 1
        
        # isf still not found update name so we can distinguish the devices where we tried already
        if newName == -1 :
            recordsNotFound.append (["(name not found)", device['dev_MAC']])          
        else:
            # name wa sfound with DiG or Pholus
            recordsToUpdate.append ([newName, device['dev_MAC']])

    # Print log            
    mylog('verbose', ["        Names Found (DiG/Pholus): ", len(recordsToUpdate), " (",foundDig,"/",foundPholus ,")" ])                 
    mylog('verbose', ["        Names Not Found         : ", len(recordsNotFound) ])    
     
    # update not found devices with (name not found) 
    sql.executemany ("UPDATE Devices SET dev_Name = ? WHERE dev_MAC = ? ", recordsNotFound )
    # update names of devices which we were bale to resolve
    sql.executemany ("UPDATE Devices SET dev_Name = ? WHERE dev_MAC = ? ", recordsToUpdate )
    commitDB()


#-------------------------------------------------------------------------------
def performNmapScan(devicesToScan):

    global changedPorts_json_struc     

    changedPortsTmp = []

    if len(devicesToScan) > 0:

        timeoutSec = NMAP_TIMEOUT

        devTotal = len(devicesToScan)

        updateState("Scan: Nmap")

        mylog('verbose', ['[', timeNow(), '] Scan: Nmap for max ', str(timeoutSec), 's ('+ str(round(int(timeoutSec) / 60, 1)) +'min) per device'])  

        mylog('verbose', ["        Estimated max delay: ", (devTotal * int(timeoutSec)), 's ', '(', round((devTotal * int(timeoutSec))/60,1) , 'min)' ])

        devIndex = 0
        for device in devicesToScan:
            # Execute command
            output = ""
            # prepare arguments from user supplied ones
            nmapArgs = ['nmap'] + NMAP_ARGS.split() + [device["dev_LastIP"]]

            progress = ' (' + str(devIndex+1) + '/' + str(devTotal) + ')'

            try:
                # try runnning a subprocess with a forced (timeout + 30 seconds)  in case the subprocess hangs
                output = subprocess.check_output (nmapArgs, universal_newlines=True,  stderr=subprocess.STDOUT, timeout=(timeoutSec + 30))
            except subprocess.CalledProcessError as e:
                # An error occured, handle it
                mylog('none', [e.output])
                mylog('none', ["        Error - Nmap Scan - check logs", progress])            
            except subprocess.TimeoutExpired as timeErr:
                mylog('verbose', ['        Nmap TIMEOUT - the process forcefully terminated as timeout reached for ', device["dev_LastIP"], progress]) 

            if output == "": # check if the subprocess failed                    
                mylog('info', ['[', timeNow(), '] Scan: Nmap FAIL for ', device["dev_LastIP"], progress ,' check logs for details']) 
            else: 
                mylog('verbose', ['[', timeNow(), '] Scan: Nmap SUCCESS for ', device["dev_LastIP"], progress])

            devIndex += 1
            
            #  check the last run output        
            newLines = output.split('\n')

            # regular logging
            for line in newLines:
                append_line_to_file (logPath + '/pialert_nmap.log', line +'\n')                
            
            # collect ports / new Nmap Entries
            newEntries = []

            index = 0
            startCollecting = False
            duration = "" 
            for line in newLines:            
                if 'Starting Nmap' in line:
                    if len(newLines) > index+1 and 'Note: Host seems down' in newLines[index+1]:
                        break # this entry is empty
                elif 'PORT' in line and 'STATE' in line and 'SERVICE' in line:
                    startCollecting = True
                elif 'PORT' in line and 'STATE' in line and 'SERVICE' in line:    
                    startCollecting = False # end reached
                elif startCollecting and len(line.split()) == 3:                                    
                    newEntries.append(nmap_entry(device["dev_MAC"], timeNow(), line.split()[0], line.split()[1], line.split()[2], device["dev_Name"]))
                elif 'Nmap done' in line:
                    duration = line.split('scanned in ')[1]            
            index += 1

            # previous Nmap Entries
            oldEntries = []
            
            if len(newEntries) > 0:   

                #  get all current NMAP ports from the DB
                sql.execute(sql_nmap_scan_all) 

                rows = sql.fetchall()

                for row in rows: 
                    oldEntries.append(nmap_entry(row["MAC"], row["Port"], row["State"], row["Service"], device["dev_Name"], row["Extra"], row["Index"]))

                indexesToRemove = []

                # Remove all entries already available in the database
                for newEntry in newEntries:
                    #  Check if available in oldEntries
                    if any(x.hash == newEntry.hash for x in oldEntries):
                        newEntries.pop(index)

                mylog('verbose', ['[', timeNow(), '] Scan: Nmap found ', len(newEntries), ' new or changed ports'])

                # collect new ports, find the corresponding old entry and return for notification purposes
                # also update the DB with the new values after deleting the old ones
                if len(newEntries) > 0:

                    params = []
                    indexesToDelete = ""

                    # Find old entry matching the new entry hash
                    for newEntry in newEntries:                   

                        foundEntry = None

                        for oldEntry in oldEntries:
                            if oldEntry.hash == newEntry.hash:

                                params.append(newEntry.mac, newEntry.time, newEntry.port, newEntry.state, newEntry.service, oldEntry.extra)

                                indexesToDelete = indexesToDelete + str(oldEntry.index) + ','

                                foundEntry = oldEntry

                        columnNames = ["Name", "MAC", "Port", "State", "Service", "Extra", "NewOrOld"  ]
                        if foundEntry is not None:
                            changedPortsTmp.append({       
                                                    "Name"      : foundEntry.name, 
                                                    "MAC"       : newEntry.mac, 
                                                    "Port"      : newEntry.port, 
                                                    "State"     : newEntry.state, 
                                                    "Service"   : newEntry.service, 
                                                    "Extra"     : foundEntry.extra,
                                                    "NewOrOld"  : "New values"
                                                })
                            changedPortsTmp.append({ 
                                                    "Name"      : foundEntry.name, 
                                                    "MAC"       : foundEntry.mac, 
                                                    "Port"      : foundEntry.port, 
                                                    "State"     : foundEntry.state, 
                                                    "Service"   : foundEntry.service, 
                                                    "Extra"     : foundEntry.extra,
                                                    "NewOrOld"  : "Old values"
                                                })                            
                        else:
                            changedPortsTmp.append({
                                                    "Name"      : "New device", 
                                                    "MAC"       : newEntry.mac, 
                                                    "Port"      : newEntry.port, 
                                                    "State"     : newEntry.state, 
                                                    "Service"   : newEntry.service, 
                                                    "Extra"     : "",
                                                    "NewOrOld"  : "New device"                                       
                                                })

                    changedPorts_json_struc = json_struc({ "data" : changedPortsTmp}, columnNames)

                    #  Delete old entries if available
                    if len(indexesToDelete) > 0:
                        sql.execute ("DELETE FROM Nmap_Scan where Index in (" + indexesToDelete[:-1] +")")
                        commitDB ()

                    # Insert new values into the DB 
                    sql.executemany ("""INSERT INTO Nmap_Scan ("MAC", "Time", "Port", "State", "Service", "Extra") VALUES (?, ?, ?, ?, ?, ?)""", params) 
                    commitDB ()

#-------------------------------------------------------------------------------
class nmap_entry:
    def __init__(self, mac, time, port, state, service, name = '', extra = '', index = 0):
        self.mac = mac
        self.time = time
        self.port = port
        self.state = state
        self.service = service
        self.name = name
        self.extra = extra
        self.index = index
        self.hash = str(hash(str(mac) + str(port)+ str(state)+ str(service)))

#-------------------------------------------------------------------------------
def performPholusScan (timeoutSec):

    # scan every interface
    for subnet in userSubnets:

        temp = subnet.split("--interface=")

        if len(temp) != 2:
            mylog('none', ["        Skip scan (need subnet in format '192.168.1.0/24 --inteface=eth0'), got: ", subnet])
            return

        mask = temp[0].strip()
        interface = temp[1].strip()

        # logging & updating app state        
        updateState("Scan: Pholus")        
        mylog('info', ['[', timeNow(), '] Scan: Pholus for ', str(timeoutSec), 's ('+ str(round(int(timeoutSec) / 60, 1)) +'min)'])  
        mylog('verbose', ["        Pholus scan on [interface] ", interface, " [mask] " , mask])
        
        # the scan always lasts 2x as long, so the desired user time from settings needs to be halved
        adjustedTimeout = str(round(int(timeoutSec) / 2, 0)) 

        #  python3 -m trace --trace /home/pi/pialert/pholus/pholus3.py eth1 -rdns_scanning  192.168.1.0/24 -stimeout 600
        pholus_args = ['python3', '/home/pi/pialert/pholus/pholus3.py', interface, "-rdns_scanning", mask, "-stimeout", adjustedTimeout]

        # Execute command
        output = ""

        try:
            # try runnning a subprocess with a forced (timeout + 30 seconds)  in case the subprocess hangs
            output = subprocess.check_output (pholus_args, universal_newlines=True,  stderr=subprocess.STDOUT, timeout=(timeoutSec + 30))
        except subprocess.CalledProcessError as e:
            # An error occured, handle it
            mylog('none', [e.output])
            mylog('none', ["        Error - Pholus Scan - check logs"])            
        except subprocess.TimeoutExpired as timeErr:
            mylog('none', ['        Pholus TIMEOUT - the process forcefully terminated as timeout reached']) 

        if output == "": # check if the subprocess failed                    
            mylog('none', ['[', timeNow(), '] Scan: Pholus FAIL - check logs']) 
        else: 
            mylog('verbose', ['[', timeNow(), '] Scan: Pholus SUCCESS'])
        
        #  check the last run output
        f = open(logPath + '/pialert_pholus_lastrun.log', 'r+')
        newLines = f.read().split('\n')
        f.close()        

        # cleanup - select only lines containing a separator to filter out unnecessary data
        newLines = list(filter(lambda x: '|' in x, newLines))        

        # regular logging
        for line in newLines:
            append_line_to_file (logPath + '/pialert_pholus.log', line +'\n')         
        
        # build SQL query parameters to insert into the DB
        params = []

        for line in newLines:
            columns = line.split("|")
            if len(columns) == 4:
                params.append(( interface + " " + mask, timeNow() , columns[0].replace(" ", ""), columns[1].replace(" ", ""), columns[2].replace(" ", ""), columns[3], ''))

        if len(params) > 0:                
            sql.executemany ("""INSERT INTO Pholus_Scan ("Info", "Time", "MAC", "IP_v4_or_v6", "Record_Type", "Value", "Extra") VALUES (?, ?, ?, ?, ?, ?, ?)""", params) 
            commitDB ()

#-------------------------------------------------------------------------------
def cleanResult(str):
    # alternative str.split('.')[0]
    str = str.replace("._airplay", "")
    str = str.replace("._tcp", "")
    str = str.replace(".local", "")
    str = str.replace("._esphomelib", "")
    str = str.replace("._googlecast", "")
    str = str.replace(".lan", "")
    str = str.replace(".home", "")
    str = re.sub(r'-[a-fA-F0-9]{32}', '', str)    # removing last part of e.g. Nest-Audio-ff77ff77ff77ff77ff77ff77ff77ff77
    # str = str.replace(".", "")

    return str


# Disclaimer - I'm interfacing with a script I didn't write (pholus3.py) so it's possible I'm missing types of answers
# it's also possible the pholus3.py script can be adjusted to provide a better output to interface with it
# Hit me with a PR if you know how! :)
def resolve_device_name_pholus (pMAC, pIP, allRes):
    
    pholusMatchesIndexes = []

    index = 0
    for result in allRes:
        #  limiting entries used for name resolution to the ones containing the current IP (v4 only)
        if result["MAC"] == pMAC and result["Record_Type"] == "Answer" and result["IP_v4_or_v6"] == pIP and '._googlezone' not in result["Value"]:
            # found entries with a matching MAC address, let's collect indexes             
            pholusMatchesIndexes.append(index)

        index += 1

    # return if nothing found
    if len(pholusMatchesIndexes) == 0:
        return -1

    # we have some entries let's try to select the most useful one

    # airplay matches contain a lot of information
    # Matches for example: 
    # Brand Tv (50)._airplay._tcp.local. TXT Class:32769 "acl=0 deviceid=66:66:66:66:66:66 features=0x77777,0x38BCB46 rsf=0x3 fv=p20.T-FFFFFF-03.1 flags=0x204 model=XXXX manufacturer=Brand serialNumber=XXXXXXXXXXX protovers=1.1 srcvers=777.77.77 pi=FF:FF:FF:FF:FF:FF psi=00000000-0000-0000-0000-FFFFFFFFFF gid=00000000-0000-0000-0000-FFFFFFFFFF gcgl=0 pk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    for i in pholusMatchesIndexes:
        if checkIPV4(allRes[i]['IP_v4_or_v6']) and '._airplay._tcp.local. TXT Class:32769' in str(allRes[i]["Value"]) :
            return allRes[i]["Value"].split('._airplay._tcp.local. TXT Class:32769')[0]
    
    # second best - contains airplay
    # Matches for example: 
    # _airplay._tcp.local. PTR Class:IN "Brand Tv (50)._airplay._tcp.local."
    for i in pholusMatchesIndexes:
        if checkIPV4(allRes[i]['IP_v4_or_v6']) and '_airplay._tcp.local. PTR Class:IN' in allRes[i]["Value"] and ('._googlecast') not in allRes[i]["Value"]:
            return cleanResult(allRes[i]["Value"].split('"')[1])    

    # Contains PTR Class:32769
    # Matches for example: 
    # 3.1.168.192.in-addr.arpa. PTR Class:32769 "MyPc.local."
    for i in pholusMatchesIndexes:
        if checkIPV4(allRes[i]['IP_v4_or_v6']) and 'PTR Class:32769' in allRes[i]["Value"]:
            return cleanResult(allRes[i]["Value"].split('"')[1])

    # Contains AAAA Class:IN
    # Matches for example: 
    # DESKTOP-SOMEID.local. AAAA Class:IN "fe80::fe80:fe80:fe80:fe80"
    for i in pholusMatchesIndexes:
        if checkIPV4(allRes[i]['IP_v4_or_v6']) and 'AAAA Class:IN' in allRes[i]["Value"]:
            return cleanResult(allRes[i]["Value"].split('.local.')[0])

    # Contains _googlecast._tcp.local. PTR Class:IN
    # Matches for example: 
    # _googlecast._tcp.local. PTR Class:IN "Nest-Audio-ff77ff77ff77ff77ff77ff77ff77ff77._googlecast._tcp.local."
    for i in pholusMatchesIndexes:
        if checkIPV4(allRes[i]['IP_v4_or_v6']) and '_googlecast._tcp.local. PTR Class:IN' in allRes[i]["Value"] and ('Google-Cast-Group') not in allRes[i]["Value"]:
            return cleanResult(allRes[i]["Value"].split('"')[1])

    # Contains A Class:32769
    # Matches for example: 
    # Android.local. A Class:32769 "192.168.1.6"
    for i in pholusMatchesIndexes:
        if checkIPV4(allRes[i]['IP_v4_or_v6']) and ' A Class:32769' in allRes[i]["Value"]:
            return cleanResult(allRes[i]["Value"].split(' A Class:32769')[0])

    # # Contains PTR Class:IN
    # Matches for example: 
    # _esphomelib._tcp.local. PTR Class:IN "ceiling-light-1._esphomelib._tcp.local."
    for i in pholusMatchesIndexes:
        if checkIPV4(allRes[i]['IP_v4_or_v6']) and 'PTR Class:IN' in allRes[i]["Value"]:
            return cleanResult(allRes[i]["Value"].split('"')[1])

    return -1
    
#-------------------------------------------------------------------------------

def resolve_device_name_dig (pMAC, pIP):
    
    newName = ""

    try :
        dig_args = ['dig', '+short', '-x', pIP]

        # Execute command
        try:
            # try runnning a subprocess
            newName = subprocess.check_output (dig_args, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            # An error occured, handle it
            mylog('none', [e.output])            
            # newName = "Error - check logs"
            return -1

        # Check returns
        newName = newName.strip()

        if len(newName) == 0 :
            return -1
            
        # Cleanup
        newName = cleanResult(newName)

        if newName == "" or  len(newName) == 0: 
            return -1

        # Return newName
        return newName

    # not Found
    except subprocess.CalledProcessError :
        return -1            

#-------------------------------------------------------------------------------
def void_ghost_disconnections ():
    # Void connect ghost events (disconnect event exists in last X min.) 
    print_log ('Void - 1 Connect ghost events')
    sql.execute ("""UPDATE Events SET eve_PairEventRowid = Null,
                        eve_EventType ='VOIDED - ' || eve_EventType
                    WHERE eve_MAC != 'Internet'
                      AND eve_EventType = 'Connected'
                      AND eve_DateTime = ?
                      AND eve_MAC IN (
                          SELECT Events.eve_MAC
                          FROM CurrentScan, Devices, ScanCycles, Events 
                          WHERE cur_ScanCycle = ?
                            AND dev_MAC = cur_MAC
                            AND dev_ScanCycle = cic_ID
                            AND cic_ID = cur_ScanCycle
                            AND eve_MAC = cur_MAC
                            AND eve_EventType = 'Disconnected'
                            AND eve_DateTime >=
                                DATETIME (?, '-' || cic_EveryXmin ||' minutes')
                          ) """,
                    (startTime, cycle, startTime)   )

    # Void connect paired events
    print_log ('Void - 2 Paired events')
    sql.execute ("""UPDATE Events SET eve_PairEventRowid = Null 
                    WHERE eve_MAC != 'Internet'
                      AND eve_PairEventRowid IN (
                          SELECT Events.RowID
                          FROM CurrentScan, Devices, ScanCycles, Events 
                          WHERE cur_ScanCycle = ?
                            AND dev_MAC = cur_MAC
                            AND dev_ScanCycle = cic_ID
                            AND cic_ID = cur_ScanCycle
                            AND eve_MAC = cur_MAC
                            AND eve_EventType = 'Disconnected'
                            AND eve_DateTime >=
                                DATETIME (?, '-' || cic_EveryXmin ||' minutes')
                          ) """,
                    (cycle, startTime)   )

    # Void disconnect ghost events 
    print_log ('Void - 3 Disconnect ghost events')
    sql.execute ("""UPDATE Events SET eve_PairEventRowid = Null, 
                        eve_EventType = 'VOIDED - '|| eve_EventType
                    WHERE eve_MAC != 'Internet'
                      AND ROWID IN (
                          SELECT Events.RowID
                          FROM CurrentScan, Devices, ScanCycles, Events 
                          WHERE cur_ScanCycle = ?
                            AND dev_MAC = cur_MAC
                            AND dev_ScanCycle = cic_ID
                            AND cic_ID = cur_ScanCycle
                            AND eve_MAC = cur_MAC
                            AND eve_EventType = 'Disconnected'
                            AND eve_DateTime >=
                                DATETIME (?, '-' || cic_EveryXmin ||' minutes')
                          ) """,
                    (cycle, startTime)   )
    print_log ('Void end')
    commitDB()

#-------------------------------------------------------------------------------
def pair_sessions_events ():
    # NOT NECESSARY FOR INCREMENTAL UPDATE
    # print_log ('Pair session - 1 Clean')
    # sql.execute ("""UPDATE Events
    #                 SET eve_PairEventRowid = NULL
    #                 WHERE eve_EventType IN ('New Device', 'Connected')
    #              """ )
    

    # Pair Connection / New Device events
    print_log ('Pair session - 1 Connections / New Devices')
    sql.execute ("""UPDATE Events
                    SET eve_PairEventRowid =
                       (SELECT ROWID
                        FROM Events AS EVE2
                        WHERE EVE2.eve_EventType IN ('New Device', 'Connected',
                            'Device Down', 'Disconnected')
                           AND EVE2.eve_MAC = Events.eve_MAC
                           AND EVE2.eve_Datetime > Events.eve_DateTime
                        ORDER BY EVE2.eve_DateTime ASC LIMIT 1)
                    WHERE eve_EventType IN ('New Device', 'Connected')
                    AND eve_PairEventRowid IS NULL
                 """ )

    # Pair Disconnection / Device Down
    print_log ('Pair session - 2 Disconnections')
    sql.execute ("""UPDATE Events
                    SET eve_PairEventRowid =
                        (SELECT ROWID
                         FROM Events AS EVE2
                         WHERE EVE2.eve_PairEventRowid = Events.ROWID)
                    WHERE eve_EventType IN ('Device Down', 'Disconnected')
                      AND eve_PairEventRowid IS NULL
                 """ )
    print_log ('Pair session end')

    commitDB()

#-------------------------------------------------------------------------------
def create_sessions_snapshot ():
    
    # Clean sessions snapshot
    print_log ('Sessions Snapshot - 1 Clean')
    sql.execute ("DELETE FROM SESSIONS" )

    # Insert sessions
    print_log ('Sessions Snapshot - 2 Insert')
    sql.execute ("""INSERT INTO Sessions
                    SELECT * FROM Convert_Events_to_Sessions""" )

    print_log ('Sessions end')
    commitDB()



#-------------------------------------------------------------------------------
def skip_repeated_notifications ():    

    # Skip repeated notifications
    # due strfime : Overflow --> use  "strftime / 60"
    print_log ('Skip Repeated')
    sql.execute ("""UPDATE Events SET eve_PendingAlertEmail = 0
                    WHERE eve_PendingAlertEmail = 1 AND eve_MAC IN
                        (
                        SELECT dev_MAC FROM Devices
                        WHERE dev_LastNotification IS NOT NULL
                          AND dev_LastNotification <>""
                          AND (strftime("%s", dev_LastNotification)/60 +
                                dev_SkipRepeated * 60) >
                              (strftime('%s','now','localtime')/60 )
                        )
                 """ )
    print_log ('Skip Repeated end')

    commitDB()


#===============================================================================
# REPORTING
#===============================================================================
# create a json for webhook and mqtt notifications to provide further integration options  
json_final = []

def send_notifications ():
    global mail_text, mail_html, json_final, changedPorts_json_struc, partial_html, partial_txt, partial_json

    deviceUrl              = REPORT_DASHBOARD_URL + '/deviceDetails.php?mac='

    # Reporting section
    mylog('verbose', ['  Check if something to report'])    

    # prepare variables for JSON construction
    json_internet = []
    json_new_devices = []
    json_down_devices = []
    json_events = []
    json_ports = []
    json_plugins = []

    # Disable reporting on events for devices where reporting is disabled based on the MAC address
    sql.execute ("""UPDATE Events SET eve_PendingAlertEmail = 0
                    WHERE eve_PendingAlertEmail = 1 AND eve_EventType != 'Device Down' AND eve_MAC IN
                        (
                            SELECT dev_MAC FROM Devices WHERE dev_AlertEvents = 0 
						)""")
    sql.execute ("""UPDATE Events SET eve_PendingAlertEmail = 0
                    WHERE eve_PendingAlertEmail = 1 AND eve_EventType = 'Device Down' AND eve_MAC IN
                        (
                            SELECT dev_MAC FROM Devices WHERE dev_AlertDeviceDown = 0 
						)""")

    # Open text Template
    template_file = open(pialertPath + '/back/report_template.txt', 'r') 
    mail_text = template_file.read() 
    template_file.close() 

    # Open html Template
    template_file = open(pialertPath + '/back/report_template.html', 'r') 
    if isNewVersion():
        template_file = open(pialertPath + '/back/report_template_new_version.html', 'r') 

    mail_html = template_file.read() 
    template_file.close() 

    # Report Header & footer
    timeFormated = startTime.strftime ('%Y-%m-%d %H:%M')
    mail_text = mail_text.replace ('<REPORT_DATE>', timeFormated)
    mail_html = mail_html.replace ('<REPORT_DATE>', timeFormated)

    mail_text = mail_text.replace ('<SERVER_NAME>', socket.gethostname() )
    mail_html = mail_html.replace ('<SERVER_NAME>', socket.gethostname() )

    if 'internet' in INCLUDED_SECTIONS:
        # Compose Internet Section
        sqlQuery = """SELECT eve_MAC as MAC,  eve_IP as IP, eve_DateTime as Datetime, eve_EventType as "Event Type", eve_AdditionalInfo as "More info" FROM Events
                        WHERE eve_PendingAlertEmail = 1 AND eve_MAC = 'Internet'
                        ORDER BY eve_DateTime"""

        notiStruc = construct_notifications(sqlQuery, "Internet IP change")

        # collect "internet" (IP changes) for the webhook json          
        json_internet = notiStruc.json["data"]

        mail_text = mail_text.replace ('<SECTION_INTERNET>', notiStruc.text + '\n')
        mail_html = mail_html.replace ('<INTERNET_TABLE>', notiStruc.html)

    if 'new_devices' in INCLUDED_SECTIONS:
        # Compose New Devices Section 
        sqlQuery = """SELECT eve_MAC as MAC, eve_DateTime as Datetime, dev_LastIP as IP, eve_EventType as "Event Type", dev_Name as "Device name", dev_Comments as Comments  FROM Events_Devices
                        WHERE eve_PendingAlertEmail = 1
                        AND eve_EventType = 'New Device'
                        ORDER BY eve_DateTime"""

        notiStruc = construct_notifications(sqlQuery, "New devices")

        # collect "new_devices" for the webhook json         
        json_new_devices = notiStruc.json["data"]

        mail_text = mail_text.replace ('<SECTION_NEW_DEVICES>', notiStruc.text + '\n')
        mail_html = mail_html.replace ('<NEW_DEVICES_TABLE>', notiStruc.html)

    if 'down_devices' in INCLUDED_SECTIONS:
        # Compose Devices Down Section   
        sqlQuery = """SELECT eve_MAC as MAC, eve_DateTime as Datetime, dev_LastIP as IP, eve_EventType as "Event Type", dev_Name as "Device name", dev_Comments as Comments  FROM Events_Devices
                        WHERE eve_PendingAlertEmail = 1
                        AND eve_EventType = 'Device Down'
                        ORDER BY eve_DateTime"""

        notiStruc = construct_notifications(sqlQuery, "Down devices")

        # collect "new_devices" for the webhook json         
        json_down_devices = notiStruc.json["data"]

        mail_text = mail_text.replace ('<SECTION_DEVICES_DOWN>', notiStruc.text + '\n')
        mail_html = mail_html.replace ('<DOWN_DEVICES_TABLE>', notiStruc.html)

    if 'events' in INCLUDED_SECTIONS:
        # Compose Events Section   
        sqlQuery = """SELECT eve_MAC as MAC, eve_DateTime as Datetime, dev_LastIP as IP, eve_EventType as "Event Type", dev_Name as "Device name", dev_Comments as Comments  FROM Events_Devices
                        WHERE eve_PendingAlertEmail = 1
                        AND eve_EventType IN ('Connected','Disconnected',
                            'IP Changed')
                        ORDER BY eve_DateTime"""

        notiStruc = construct_notifications(sqlQuery, "Events")

        # collect "events" for the webhook json         
        json_events = notiStruc.json["data"]

        mail_text = mail_text.replace ('<SECTION_EVENTS>', notiStruc.text + '\n')
        mail_html = mail_html.replace ('<EVENTS_TABLE>', notiStruc.html)
    
    if 'ports' in INCLUDED_SECTIONS:  
        # collect "ports" for the webhook json 
        if changedPorts_json_struc is not None:          
            json_ports =  changedPorts_json_struc.json["data"]       

        notiStruc = construct_notifications("", "Ports", True, changedPorts_json_struc)

        mail_html = mail_html.replace ('<PORTS_TABLE>', notiStruc.html)

        portsTxt = ""
        if changedPorts_json_struc is not None:
            portsTxt = "Ports \n---------\n Ports changed! Check PiAlert for details!\n"        

        mail_text = mail_text.replace ('<PORTS_TABLE>', portsTxt )

    if 'plugins' in INCLUDED_SECTIONS:  
        # Compose Plugins Section   
        sqlQuery = """SELECT Plugin, Object_PrimaryId, Object_SecondaryId, DateTimeChanged, Watched_Value1, Watched_Value2, Watched_Value3, Watched_Value4, Status from Plugins_Events"""

        notiStruc = construct_notifications(sqlQuery, "Plugins")

        # collect "plugins" for the webhook json 
        json_plugins = notiStruc.json["data"]

        mail_text = mail_text.replace ('<PLUGINS_TABLE>', notiStruc.text + '\n')
        mail_html = mail_html.replace ('<PLUGINS_TABLE>', notiStruc.html)

        # check if we need to report something
        plugins_report = plugin_check_smth_to_report(json_plugins)


    json_final = {
                    "internet": json_internet,                        
                    "new_devices": json_new_devices,
                    "down_devices": json_down_devices,                        
                    "events": json_events,
                    "ports": json_ports,
                    "plugins": json_plugins,
                    }    

    mail_text = removeDuplicateNewLines(mail_text)
    
    # Create clickable MAC links 
    mail_html = generate_mac_links (mail_html, deviceUrl)

    #  Write output emails for debug    
    write_file (logPath + '/report_output.json', json.dumps(json_final)) 
    write_file (logPath + '/report_output.txt', mail_text) 
    write_file (logPath + '/report_output.html', mail_html) 

    # Send Mail
    if json_internet != [] or json_new_devices != [] or json_down_devices != [] or json_events != [] or json_ports != [] or debug_force_notification or plugins_report:        

        update_api(True)

        mylog('none', ['    Changes detected, sending reports'])

        if REPORT_MAIL and check_config('email'):  
            updateState("Send: Email")
            mylog('info', ['      Sending report by Email'])
            send_email (mail_text, mail_html)
        else :
            mylog('verbose', ['      Skip email'])
        if REPORT_APPRISE and check_config('apprise'):
            updateState("Send: Apprise")
            mylog('info', ['      Sending report by Apprise'])
            send_apprise (mail_html, mail_text)
        else :
            mylog('verbose', ['      Skip Apprise'])
        if REPORT_WEBHOOK and check_config('webhook'):
            updateState("Send: Webhook")
            mylog('info', ['      Sending report by Webhook'])
            send_webhook (json_final, mail_text)
        else :
            mylog('verbose', ['      Skip webhook'])
        if REPORT_NTFY and check_config('ntfy'):
            updateState("Send: NTFY")
            mylog('info', ['      Sending report by NTFY'])
            send_ntfy (mail_text)
        else :
            mylog('verbose', ['      Skip NTFY'])
        if REPORT_PUSHSAFER and check_config('pushsafer'):
            updateState("Send: PUSHSAFER")
            mylog('info', ['      Sending report by PUSHSAFER'])
            send_pushsafer (mail_text)
        else :
            mylog('verbose', ['      Skip PUSHSAFER'])
        # Update MQTT entities
        if REPORT_MQTT and check_config('mqtt'):
            updateState("Send: MQTT")
            mylog('info', ['      Establishing MQTT thread'])                          
            mqtt_start()        
        else :
            mylog('verbose', ['      Skip MQTT'])
    else :
        mylog('verbose', ['    No changes to report'])

    # Clean Pending Alert Events
    sql.execute ("""UPDATE Devices SET dev_LastNotification = ?
                    WHERE dev_MAC IN (SELECT eve_MAC FROM Events
                                      WHERE eve_PendingAlertEmail = 1)
                 """, (datetime.datetime.now(),) )
    sql.execute ("""UPDATE Events SET eve_PendingAlertEmail = 0
                    WHERE eve_PendingAlertEmail = 1""")

    # clear plugin events
    sql.execute ("DELETE FROM Plugins_Events")
    
    changedPorts_json_struc = None

    # DEBUG - print number of rows updated    
    mylog('info', ['[', timeNow(), '] Notifications: ', sql.rowcount])

    # Commit changes    
    commitDB()

#-------------------------------------------------------------------------------
def construct_notifications(sqlQuery, tableTitle, skipText = False, suppliedJsonStruct = None):

    if suppliedJsonStruct is None and sqlQuery == "":
        return noti_struc("", "", "")

    table_attributes = {"style" : "border-collapse: collapse; font-size: 12px; color:#70707", "width" : "100%", "cellspacing" : 0, "cellpadding" : "3px", "bordercolor" : "#C0C0C0", "border":"1"}
    headerProps = "width='120px' style='color:blue; font-size: 16px;' bgcolor='#909090' "
    thProps = "width='120px' style='color:#F0F0F0' bgcolor='#909090' "

    build_direction = "TOP_TO_BOTTOM"
    text_line = '{}\t{}\n'

    if suppliedJsonStruct is None:
        json_struc = get_table_as_json(sqlQuery)
    else:
        json_struc = suppliedJsonStruct

    jsn  = json_struc.json
    html = ""    
    text = ""

    if len(jsn["data"]) > 0:
        text = tableTitle + "\n---------\n"

        html = convert(jsn, build_direction=build_direction, table_attributes=table_attributes)
        html = format_table(html, "data", headerProps, tableTitle).replace('<ul>','<ul style="list-style:none;padding-left:0">')

        headers = json_struc.columnNames

        # prepare text-only message
        if skipText == False:
            
            for device in jsn["data"]:
                for header in headers:
                    padding = ""
                    if len(header) < 4:
                        padding = "\t"
                    text += text_line.format ( header + ': ' + padding, device[header]) 
                text += '\n'

        #  Format HTML table headers
        for header in headers:
            html = format_table(html, header, thProps)

    return noti_struc(jsn, text, html)

#-------------------------------------------------------------------------------
class noti_struc:
    def __init__(self, json, text, html):
        self.json = json
        self.text = text
        self.html = html
       
#-------------------------------------------------------------------------------
def check_config(service):

    if service == 'email':
        if SMTP_PASS == '' or SMTP_SERVER == '' or SMTP_USER == '' or REPORT_FROM == '' or REPORT_TO == '':
            mylog('none', ['    Error: Email service not set up correctly. Check your pialert.conf SMTP_*, REPORT_FROM and REPORT_TO variables.'])
            return False
        else:
            return True   

    if service == 'apprise':
        if APPRISE_URL == '' or APPRISE_HOST == '':
            mylog('none', ['    Error: Apprise service not set up correctly. Check your pialert.conf APPRISE_* variables.'])
            return False
        else:
            return True  

    if service == 'webhook':
        if WEBHOOK_URL == '':
            mylog('none', ['    Error: Webhook service not set up correctly. Check your pialert.conf WEBHOOK_* variables.'])
            return False
        else:
            return True 

    if service == 'ntfy':
        if NTFY_HOST == '' or NTFY_TOPIC == '':
            mylog('none', ['    Error: NTFY service not set up correctly. Check your pialert.conf NTFY_* variables.'])
            return False
        else:
            return True 

    if service == 'pushsafer':
        if PUSHSAFER_TOKEN == 'ApiKey':
            mylog('none', ['    Error: Pushsafer service not set up correctly. Check your pialert.conf PUSHSAFER_TOKEN variable.'])
            return False
        else:
            return True 

    if service == 'mqtt':
        if MQTT_BROKER == '' or MQTT_PORT == '' or MQTT_USER == '' or MQTT_PASSWORD == '':
            mylog('none', ['    Error: MQTT service not set up correctly. Check your pialert.conf MQTT_* variables.'])
            return False
        else:
            return True 


   
#-------------------------------------------------------------------------------
def format_table (html, thValue, props, newThValue = ''):

    if newThValue == '':
        newThValue = thValue
        
    return html.replace("<th>"+thValue+"</th>", "<th "+props+" >"+newThValue+"</th>" )

#-------------------------------------------------------------------------------
def generate_mac_links (html, deviceUrl):

    p = re.compile(r'(?:[0-9a-fA-F]:?){12}')

    MACs = re.findall(p, html)

    for mac in MACs:        
        html = html.replace('<td>' + mac + '</td>','<td><a href="' + deviceUrl + mac + '">' + mac + '</a></td>')

    return html

#-------------------------------------------------------------------------------
def format_report_section (pActive, pSection, pTable, pText, pHTML):
    global mail_text
    global mail_html

    # Replace section text
    if pActive :
        mail_text = mail_text.replace ('<'+ pTable +'>', pText)
        mail_html = mail_html.replace ('<'+ pTable +'>', pHTML)       

        mail_text = remove_tag (mail_text, pSection)       
        mail_html = remove_tag (mail_html, pSection)
    else:
        mail_text = remove_section (mail_text, pSection)
        mail_html = remove_section (mail_html, pSection)

#-------------------------------------------------------------------------------
def remove_section (pText, pSection):
    # Search section into the text
    if pText.find ('<'+ pSection +'>') >=0 \
    and pText.find ('</'+ pSection +'>') >=0 : 
        # return text without the section
        return pText[:pText.find ('<'+ pSection+'>')] + \
               pText[pText.find ('</'+ pSection +'>') + len (pSection) +3:]
    else :
        # return all text
        return pText

#-------------------------------------------------------------------------------
def remove_tag (pText, pTag):
    # return text without the tag
    return pText.replace ('<'+ pTag +'>','').replace ('</'+ pTag +'>','')


#-------------------------------------------------------------------------------
# Reporting 
#-------------------------------------------------------------------------------
def send_email (pText, pHTML):

    # Print more info for debugging if LOG_LEVEL == 'debug' 
    if LOG_LEVEL == 'debug':
        print_log ('REPORT_TO: ' + hide_email(str(REPORT_TO)) + '  SMTP_USER: ' + hide_email(str(SMTP_USER))) 

    # Compose email
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Pi.Alert Report'
    msg['From'] = REPORT_FROM
    msg['To'] = REPORT_TO
    msg.attach (MIMEText (pText, 'plain'))
    msg.attach (MIMEText (pHTML, 'html'))

    failedAt = ''

    failedAt = print_log ('SMTP try')

    try:
        # Send mail
        failedAt = print_log('Trying to open connection to ' + str(SMTP_SERVER) + ':' + str(SMTP_PORT))

        if SMTP_FORCE_SSL:
            failedAt = print_log('SMTP_FORCE_SSL == True so using .SMTP_SSL()')
            if SMTP_PORT == 0:            
                failedAt = print_log('SMTP_PORT == 0 so sending .SMTP_SSL(SMTP_SERVER)')
                smtp_connection = smtplib.SMTP_SSL(SMTP_SERVER)
            else:
                failedAt = print_log('SMTP_PORT == 0 so sending .SMTP_SSL(SMTP_SERVER, SMTP_PORT)')
                smtp_connection = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
            
        else:
            failedAt = print_log('SMTP_FORCE_SSL == False so using .SMTP()')
            if SMTP_PORT == 0:
                failedAt = print_log('SMTP_PORT == 0 so sending .SMTP(SMTP_SERVER)')
                smtp_connection = smtplib.SMTP (SMTP_SERVER)
            else:
                failedAt = print_log('SMTP_PORT == 0 so sending .SMTP(SMTP_SERVER, SMTP_PORT)')
                smtp_connection = smtplib.SMTP (SMTP_SERVER, SMTP_PORT)

        failedAt = print_log('Setting SMTP debug level')

        # Log level set to debug of the communication between SMTP server and client
        if LOG_LEVEL == 'debug':
            smtp_connection.set_debuglevel(1) 
        
        failedAt = print_log( 'Sending .ehlo()')
        smtp_connection.ehlo()

        if not SMTP_SKIP_TLS:       
            failedAt = print_log('SMTP_SKIP_TLS == False so sending .starttls()')
            smtp_connection.starttls()
            failedAt = print_log('SMTP_SKIP_TLS == False so sending .ehlo()')
            smtp_connection.ehlo()
        if not SMTP_SKIP_LOGIN:
            failedAt = print_log('SMTP_SKIP_LOGIN == False so sending .login()')
            smtp_connection.login (SMTP_USER, SMTP_PASS)
            
        failedAt = print_log('Sending .sendmail()')
        smtp_connection.sendmail (REPORT_FROM, REPORT_TO, msg.as_string())
        smtp_connection.quit()
    except smtplib.SMTPAuthenticationError as e: 
        mylog('none', ['      ERROR: Failed at - ', failedAt])
        mylog('none', ['      ERROR: Couldn\'t connect to the SMTP server (SMTPAuthenticationError), skipping Email (enable LOG_LEVEL=debug for more logging)'])
    except smtplib.SMTPServerDisconnected as e: 
        mylog('none', ['      ERROR: Failed at - ', failedAt])
        mylog('none', ['      ERROR: Couldn\'t connect to the SMTP server (SMTPServerDisconnected), skipping Email (enable LOG_LEVEL=debug for more logging)'])

    print_log('      DEBUG: Last executed - ' + str(failedAt))

#-------------------------------------------------------------------------------
def send_ntfy (_Text):
    headers = {
        "Title": "Pi.Alert Notification",
        "Actions": "view, Open Dashboard, "+ REPORT_DASHBOARD_URL,
        "Priority": "urgent",
        "Tags": "warning"
    }
    # if username and password are set generate hash and update header
    if NTFY_USER != "" and NTFY_PASSWORD != "":
	# Generate hash for basic auth
        usernamepassword = "{}:{}".format(NTFY_USER,NTFY_PASSWORD)
        basichash = b64encode(bytes(NTFY_USER + ':' + NTFY_PASSWORD, "utf-8")).decode("ascii")

	# add authorization header with hash
        headers["Authorization"] = "Basic {}".format(basichash)

    requests.post("{}/{}".format( NTFY_HOST, NTFY_TOPIC),
    data=_Text,
    headers=headers)

def send_pushsafer (_Text):
    url = 'https://www.pushsafer.com/api'
    post_fields = {
        "t" : 'Pi.Alert Message',
        "m" : _Text,
        "s" : 11,
        "v" : 3,
        "i" : 148,
        "c" : '#ef7f7f',
        "d" : 'a',
        "u" : REPORT_DASHBOARD_URL,
        "ut" : 'Open Pi.Alert',
        "k" : PUSHSAFER_TOKEN,
        }
    requests.post(url, data=post_fields)

#-------------------------------------------------------------------------------
def send_webhook (_json, _html):

    # use data type based on specified payload type
    if WEBHOOK_PAYLOAD == 'json':
        payloadData = _json        
    if WEBHOOK_PAYLOAD == 'html':
        payloadData = _html
    if WEBHOOK_PAYLOAD == 'text':
        payloadData = to_text(_json)

    # Define slack-compatible payload
    _json_payload = { "text": payloadData } if WEBHOOK_PAYLOAD == 'text' else {
    "username": "Pi.Alert",
    "text": "There are new notifications",
    "attachments": [{
      "title": "Pi.Alert Notifications",
      "title_link": REPORT_DASHBOARD_URL,
      "text": payloadData
    }]
    } 

    # DEBUG - Write the json payload into a log file for debugging
    write_file (logPath + '/webhook_payload.json', json.dumps(_json_payload))    

    # Using the Slack-Compatible Webhook endpoint for Discord so that the same payload can be used for both
    if(WEBHOOK_URL.startswith('https://discord.com/api/webhooks/') and not WEBHOOK_URL.endswith("/slack")):
        _WEBHOOK_URL = f"{WEBHOOK_URL}/slack"
        curlParams = ["curl","-i","-H", "Content-Type:application/json" ,"-d", json.dumps(_json_payload), _WEBHOOK_URL]
    else:
        _WEBHOOK_URL = WEBHOOK_URL
        curlParams = ["curl","-i","-X", WEBHOOK_REQUEST_METHOD ,"-H", "Content-Type:application/json" ,"-d", json.dumps(_json_payload), _WEBHOOK_URL]

    # execute CURL call
    try:
        # try runnning a subprocess
        p = subprocess.Popen(curlParams, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        stdout, stderr = p.communicate()

        # write stdout and stderr into .log files for debugging if needed
        logResult (stdout, stderr)    
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        mylog('none', [e.output])

#-------------------------------------------------------------------------------
def send_apprise (html, text):
    #Define Apprise compatible payload (https://github.com/caronc/apprise-api#stateless-solution)
    payload = html

    if APPRISE_PAYLOAD == 'text':
        payload = text

    _json_payload={
    "urls": APPRISE_URL,
    "title": "Pi.Alert Notifications",    
    "format": APPRISE_PAYLOAD,
    "body": payload    
    }

    try:
        # try runnning a subprocess        
        p = subprocess.Popen(["curl","-i","-X", "POST" ,"-H", "Content-Type:application/json" ,"-d", json.dumps(_json_payload), APPRISE_HOST], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = p.communicate()
        # write stdout and stderr into .log files for debugging if needed
        logResult (stdout, stderr)      
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        mylog('none', [e.output])    

#-------------------------------------------------------------------------------
# MQTT
#-------------------------------------------------------------------------------
mqtt_connected_to_broker = False
mqtt_sensors = []

def publish_mqtt(client, topic, message):
    status = 1
    while status != 0:
        result = client.publish(
                topic=topic,
                payload=message,
                qos=MQTT_QOS,
                retain=True,
            )

        status = result[0]

        if status != 0:            
            mylog('info', ["Waiting to reconnect to MQTT broker"])
            time.sleep(0.1) 
    return True

#-------------------------------------------------------------------------------
def create_generic_device(client):  
    
    deviceName = 'PiAlert'
    deviceId = 'pialert'    
    
    create_sensor(client, deviceId, deviceName, 'sensor', 'online', 'wifi-check')    
    create_sensor(client, deviceId, deviceName, 'sensor', 'down', 'wifi-cancel')        
    create_sensor(client, deviceId, deviceName, 'sensor', 'all', 'wifi')
    create_sensor(client, deviceId, deviceName, 'sensor', 'archived', 'wifi-lock')
    create_sensor(client, deviceId, deviceName, 'sensor', 'new', 'wifi-plus')
    create_sensor(client, deviceId, deviceName, 'sensor', 'unknown', 'wifi-alert')
        

#-------------------------------------------------------------------------------
def create_sensor(client, deviceId, deviceName, sensorType, sensorName, icon):    

    new_sensor_config = sensor_config(deviceId, deviceName, sensorType, sensorName, icon)

    # check if config already in list and if not, add it, otherwise skip
    global mqtt_sensors, uniqueSensorCount

    is_unique = True

    for sensor in mqtt_sensors:
        if sensor.hash == new_sensor_config.hash:
            is_unique = False
            break
           
    # save if unique
    if is_unique:             
        publish_sensor(client, new_sensor_config)        


#-------------------------------------------------------------------------------
class sensor_config:
    def __init__(self, deviceId, deviceName, sensorType, sensorName, icon):
        self.deviceId = deviceId
        self.deviceName = deviceName
        self.sensorType = sensorType
        self.sensorName = sensorName
        self.icon = icon 
        self.hash = str(hash(str(deviceId) + str(deviceName)+ str(sensorType)+ str(sensorName)+ str(icon)))

#-------------------------------------------------------------------------------
def publish_sensor(client, sensorConf): 

    global mqtt_sensors             

    message = '{ \
                "name":"'+ sensorConf.deviceName +' '+sensorConf.sensorName+'", \
                "state_topic":"system-sensors/'+sensorConf.sensorType+'/'+sensorConf.deviceId+'/state", \
                "value_template":"{{value_json.'+sensorConf.sensorName+'}}", \
                "unique_id":"'+sensorConf.deviceId+'_sensor_'+sensorConf.sensorName+'", \
                "device": \
                    { \
                        "identifiers": ["'+sensorConf.deviceId+'_sensor"], \
                        "manufacturer": "PiAlert", \
                        "name":"'+sensorConf.deviceName+'" \
                    }, \
                "icon":"mdi:'+sensorConf.icon+'" \
                }'

    topic='homeassistant/'+sensorConf.sensorType+'/'+sensorConf.deviceId+'/'+sensorConf.sensorName+'/config'

    # add the sensor to the global list to keep track of succesfully added sensors
    if publish_mqtt(client, topic, message):        
                                     # hack - delay adding to the queue in case the process is 
        time.sleep(MQTT_DELAY_SEC)   # restarted and previous publish processes aborted 
                                     # (it takes ~2s to update a sensor config on the broker)
        mqtt_sensors.append(sensorConf)

#-------------------------------------------------------------------------------
def mqtt_create_client():
    def on_disconnect(client, userdata, rc):
        global mqtt_connected_to_broker
        mqtt_connected_to_broker = False
        
        # not sure is below line is correct / necessary        
        # client = mqtt_create_client() 

    def on_connect(client, userdata, flags, rc):
        global mqtt_connected_to_broker
        
        if rc == 0: 
            mylog('verbose', ["        Connected to broker"])            
            mqtt_connected_to_broker = True     # Signal connection 
        else: 
            mylog('none', ["        Connection failed"])
            mqtt_connected_to_broker = False


    client = mqtt_client.Client('PiAlert')   # Set Connecting Client ID    
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)    
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_start() 

    return client

#-------------------------------------------------------------------------------
def mqtt_start():    

    global client, mqtt_connected_to_broker

    if mqtt_connected_to_broker == False:
        mqtt_connected_to_broker = True           
        client = mqtt_create_client() 
    
    # General stats    

    # Create a generic device for overal stats
    create_generic_device(client)

    # Get the data
    row = get_device_stats()   

    columns = ["online","down","all","archived","new","unknown"]

    payload = ""

    # Update the values 
    for column in columns:       
        payload += '"'+column+'": ' + str(row[column]) +','       

    # Publish (warap into {} and remove last ',' from above)
    publish_mqtt(client, "system-sensors/sensor/pialert/state",              
            '{ \
                '+ payload[:-1] +'\
            }'
        )


    # Specific devices

    # Get all devices
    devices = get_all_devices()

    sec_delay = len(devices) * int(MQTT_DELAY_SEC)*5

    mylog('info', ["        Estimated delay: ", (sec_delay), 's ', '(', round(sec_delay/60,1) , 'min)' ])

    for device in devices:        

        # Create devices in Home Assistant - send config messages
        deviceId = 'mac_' + device["dev_MAC"].replace(" ", "").replace(":", "_").lower()
        deviceNameDisplay = re.sub('[^a-zA-Z0-9-_\s]', '', device["dev_Name"]) 

        create_sensor(client, deviceId, deviceNameDisplay, 'sensor', 'last_ip', 'ip-network')
        create_sensor(client, deviceId, deviceNameDisplay, 'binary_sensor', 'is_present', 'wifi')
        create_sensor(client, deviceId, deviceNameDisplay, 'sensor', 'mac_address', 'folder-key-network')
        create_sensor(client, deviceId, deviceNameDisplay, 'sensor', 'is_new', 'bell-alert-outline')
        create_sensor(client, deviceId, deviceNameDisplay, 'sensor', 'vendor', 'cog')
    
        # update device sensors in home assistant              

        publish_mqtt(client, 'system-sensors/sensor/'+deviceId+'/state', 
            '{ \
                "last_ip": "' + device["dev_LastIP"] +'", \
                "is_new": "' + str(device["dev_NewDevice"]) +'", \
                "vendor": "' + sanitize_string(device["dev_Vendor"]) +'", \
                "mac_address": "' + str(device["dev_MAC"]) +'" \
            }'
        ) 

        publish_mqtt(client, 'system-sensors/binary_sensor/'+deviceId+'/state', 
            '{ \
                "is_present": "' + to_binary_sensor(str(device["dev_PresentLastScan"])) +'"\
            }'
        ) 

        # delete device / topic
        #  homeassistant/sensor/mac_44_ef_bf_c4_b1_af/is_present/config
        # client.publish(
        #     topic="homeassistant/sensor/"+deviceId+"/is_present/config",
        #     payload="",
        #     qos=1,
        #     retain=True,
        # )        
    # time.sleep(10)


#===============================================================================
# DB
#===============================================================================
#-------------------------------------------------------------------------------
def upgradeDB (): 

    # indicates, if Online_History table is available 
    onlineHistoryAvailable = sql.execute("""
    SELECT name FROM sqlite_master WHERE type='table'
    AND name='Online_History'; 
    """).fetchall() != []

    # Check if it is incompatible (Check if table has all required columns)
    isIncompatible = False
    
    if onlineHistoryAvailable :
      isIncompatible = sql.execute ("""
      SELECT COUNT(*) AS CNTREC FROM pragma_table_info('Online_History') WHERE name='Archived_Devices'
      """).fetchone()[0] == 0
    
    # Drop table if available, but incompatible
    if onlineHistoryAvailable and isIncompatible:      
      file_print ('[upgradeDB] Table is incompatible, Dropping the Online_History table)')
      sql.execute("DROP TABLE Online_History;")
      onlineHistoryAvailable = False

    if onlineHistoryAvailable == False :
      sql.execute("""      
      CREATE TABLE "Online_History" (
        "Index"	INTEGER,
        "Scan_Date"	TEXT,
        "Online_Devices"	INTEGER,
        "Down_Devices"	INTEGER,
        "All_Devices"	INTEGER,
        "Archived_Devices" INTEGER,
        PRIMARY KEY("Index" AUTOINCREMENT)
      );      
      """)

    # Alter Devices table
    # dev_Network_Node_MAC_ADDR column
    dev_Network_Node_MAC_ADDR_missing = sql.execute ("""
      SELECT COUNT(*) AS CNTREC FROM pragma_table_info('Devices') WHERE name='dev_Network_Node_MAC_ADDR'
      """).fetchone()[0] == 0

    if dev_Network_Node_MAC_ADDR_missing :
      mylog('verbose', ["[upgradeDB] Adding dev_Network_Node_MAC_ADDR to the Devices table"])   
      sql.execute("""      
      ALTER TABLE "Devices" ADD "dev_Network_Node_MAC_ADDR" TEXT      
      """)

    # dev_Network_Node_port column
    dev_Network_Node_port_missing = sql.execute ("""
      SELECT COUNT(*) AS CNTREC FROM pragma_table_info('Devices') WHERE name='dev_Network_Node_port'
      """).fetchone()[0] == 0

    if dev_Network_Node_port_missing :
      mylog('verbose', ["[upgradeDB] Adding dev_Network_Node_port to the Devices table"])     
      sql.execute("""      
      ALTER TABLE "Devices" ADD "dev_Network_Node_port" INTEGER 
      """)

    # dev_Icon column
    dev_Icon_missing = sql.execute ("""
      SELECT COUNT(*) AS CNTREC FROM pragma_table_info('Devices') WHERE name='dev_Icon'
      """).fetchone()[0] == 0

    if dev_Icon_missing :
      mylog('verbose', ["[upgradeDB] Adding dev_Icon to the Devices table"])     
      sql.execute("""      
      ALTER TABLE "Devices" ADD "dev_Icon" TEXT 
      """)

    # indicates, if Settings table is available 
    settingsMissing = sql.execute("""
    SELECT name FROM sqlite_master WHERE type='table'
    AND name='Settings'; 
    """).fetchone() == None

    # Re-creating Settings table    
    mylog('verbose', ["[upgradeDB] Re-creating Settings table"])

    if settingsMissing == False:   
        sql.execute("DROP TABLE Settings;")       

    sql.execute("""      
    CREATE TABLE "Settings" (        
    "Code_Name"	    TEXT,
    "Display_Name"	TEXT,
    "Description"	TEXT,        
    "Type"          TEXT,
    "Options"       TEXT,
    "RegEx"         TEXT,
    "Value"	        TEXT,
    "Group"	        TEXT,
    "Events"	    TEXT
    );      
    """)

    # indicates, if Pholus_Scan table is available 
    pholusScanMissing = sql.execute("""
    SELECT name FROM sqlite_master WHERE type='table'
    AND name='Pholus_Scan'; 
    """).fetchone() == None

    # if pholusScanMissing == False:
    #     # Re-creating Pholus_Scan table  
    #     sql.execute("DROP TABLE Pholus_Scan;")       
    #     pholusScanMissing = True  

    if pholusScanMissing:
        mylog('verbose', ["[upgradeDB] Re-creating Pholus_Scan table"])
        sql.execute("""      
        CREATE TABLE "Pholus_Scan" (        
        "Index"	          INTEGER,
        "Info"	          TEXT,
        "Time"	          TEXT,
        "MAC"	          TEXT,
        "IP_v4_or_v6"	  TEXT,
        "Record_Type"	  TEXT,
        "Value"           TEXT,
        "Extra"           TEXT,
        PRIMARY KEY("Index" AUTOINCREMENT)
        );      
        """)

    # indicates, if Nmap_Scan table is available 
    nmapScanMissing = sql.execute("""
    SELECT name FROM sqlite_master WHERE type='table'
    AND name='Nmap_Scan'; 
    """).fetchone() == None

     # Re-creating Parameters table
    mylog('verbose', ["[upgradeDB] Re-creating Parameters table"])
    sql.execute("DROP TABLE Parameters;")

    sql.execute("""      
      CREATE TABLE "Parameters" (
        "par_ID" TEXT PRIMARY KEY,
        "par_Value"	TEXT
      );      
      """)

    # Initialize Parameters if unavailable
    initOrSetParam('Back_App_State','Initializing')

    # if nmapScanMissing == False:
    #     # Re-creating Nmap_Scan table    
    #     sql.execute("DROP TABLE Nmap_Scan;")       
    #     nmapScanMissing = True  

    if nmapScanMissing:
        mylog('verbose', ["[upgradeDB] Re-creating Nmap_Scan table"])
        sql.execute("""      
        CREATE TABLE "Nmap_Scan" (        
        "Index"	          INTEGER,
        "MAC"	          TEXT,
        "Port"	          TEXT,
        "Time"	          TEXT,        
        "State"	          TEXT,
        "Service"	      TEXT,       
        "Extra"           TEXT,
        PRIMARY KEY("Index" AUTOINCREMENT)
        );      
        """)

    # Plugin state
    sql_Plugins_Objects = """ CREATE TABLE IF NOT EXISTS Plugins_Objects(
                        "Index"	          INTEGER,
                        Plugin TEXT NOT NULL,
                        Object_PrimaryID TEXT NOT NULL,
                        Object_SecondaryID TEXT NOT NULL,
                        DateTimeCreated TEXT NOT NULL,                        
                        DateTimeChanged TEXT NOT NULL,                        
                        Watched_Value1 TEXT NOT NULL,
                        Watched_Value2 TEXT NOT NULL,
                        Watched_Value3 TEXT NOT NULL,
                        Watched_Value4 TEXT NOT NULL,
                        Status TEXT NOT NULL,  
                        Extra TEXT NOT NULL,
                        UserData TEXT NOT NULL,
                        PRIMARY KEY("Index" AUTOINCREMENT)
                    ); """
    sql.execute(sql_Plugins_Objects)

    # Plugin execution results
    sql_Plugins_Events = """ CREATE TABLE IF NOT EXISTS Plugins_Events(
                        "Index"	          INTEGER,
                        Plugin TEXT NOT NULL,
                        Object_PrimaryID TEXT NOT NULL,
                        Object_SecondaryID TEXT NOT NULL,
                        DateTimeCreated TEXT NOT NULL,                        
                        DateTimeChanged TEXT NOT NULL,                         
                        Watched_Value1 TEXT NOT NULL,
                        Watched_Value2 TEXT NOT NULL,
                        Watched_Value3 TEXT NOT NULL,
                        Watched_Value4 TEXT NOT NULL,
                        Status TEXT NOT NULL,              
                        Extra TEXT NOT NULL,
                        UserData TEXT NOT NULL,
                        PRIMARY KEY("Index" AUTOINCREMENT)
                    ); """
    sql.execute(sql_Plugins_Events)

    # Dynamically generated language strings
    # indicates, if Language_Strings table is available 
    languageStringsMissing = sql.execute("""
    SELECT name FROM sqlite_master WHERE type='table'
    AND name='Plugins_Language_Strings'; 
    """).fetchone() == None
    
    if languageStringsMissing == False:
        sql.execute("DROP TABLE Plugins_Language_Strings;") 

    sql.execute(""" CREATE TABLE IF NOT EXISTS Plugins_Language_Strings(
                        "Index"	          INTEGER,
                        Language_Code TEXT NOT NULL,
                        String_Key TEXT NOT NULL,
                        String_Value TEXT NOT NULL,
                        Extra TEXT NOT NULL,                                                    
                        PRIMARY KEY("Index" AUTOINCREMENT)
                    ); """)   
    
    commitDB ()

#-------------------------------------------------------------------------------
def initOrSetParam(parID, parValue):    

    sql.execute ("INSERT INTO Parameters(par_ID, par_Value) VALUES('"+str(parID)+"', '"+str(parValue)+"') ON CONFLICT(par_ID) DO UPDATE SET par_Value='"+str(parValue)+"' where par_ID='"+str(parID)+"'")        

    commitDB ()

#-------------------------------------------------------------------------------
def updateState(newState):    

    sql.execute ("UPDATE Parameters SET par_Value='"+ newState +"' WHERE par_ID='Back_App_State'")        

    commitDB ()

 
#===============================================================================
# Home Assistant UTILs
#===============================================================================
def to_binary_sensor(input):
    # In HA a binary sensor returns ON or OFF    
    result = "OFF"

    # bytestring
    if isinstance(input, str):
        if input == "1":
            result = "ON"
    elif isinstance(input, int):
        if input == 1:
            result = "ON"
    elif isinstance(input, bool):
        if input == True:
            result = "ON"
    elif isinstance(input, bytes):
        if bytes_to_string(input) == "1":
            result = "ON"
    return result
        

#===============================================================================
# API
#===============================================================================
def update_api(isNotification = False, updateOnlyDataSources = []):

    mylog('verbose', ['     [API] Updating files in /front/api'])    
    folder = pialertPath + '/front/api/'

    if isNotification:
        #  Update last notification alert in all formats
        write_file(folder + 'notification_text.txt'  , mail_text)
        write_file(folder + 'notification_text.html'  , mail_html)
        write_file(folder + 'notification_json_final.json'  , json.dumps(json_final))  

    # Save plugins
    write_file(folder + 'plugins.json'  , json.dumps({"data" : plugins.list}))  

    #  prepare databse tables we want to expose 
    dataSourcesSQLs = [
        ["devices", sql_devices_all],
        ["nmap_scan", sql_nmap_scan_all],
        ["pholus_scan", sql_pholus_scan_all],
        ["events_pending_alert", sql_events_pending_alert],
        ["settings", sql_settings],
        ["plugins_events", sql_plugins_events],
        ["plugins_objects", sql_plugins_objects],
        ["language_strings", sql_language_strings],
        ["custom_endpoint", API_CUSTOM_SQL],
    ]

    # Save selected database tables
    for dsSQL in dataSourcesSQLs:

        if updateOnlyDataSources == [] or dsSQL[0] in updateOnlyDataSources:

            json_string = get_table_as_json(dsSQL[1]).json

            write_file(folder + 'table_' + dsSQL[0] + '.json'  , json.dumps(json_string))     

#-------------------------------------------------------------------------------
def get_table_as_json(sqlQuery):

    sql.execute(sqlQuery) 

    columnNames = list(map(lambda x: x[0], sql.description)) 

    rows = sql.fetchall()    

    result = {"data":[]}

    for row in rows: 
        tmp = row_to_json(columnNames, row)
        result["data"].append(tmp)
    return json_struc(result, columnNames)

#-------------------------------------------------------------------------------
class json_struc:
    def __init__(self, jsn, columnNames):
        # mylog('verbose', ['     [] tmp: ', str(json.dumps(jsn))]) 
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

#===============================================================================
# UTIL
#===============================================================================

#-------------------------------------------------------------------------------
def write_file (pPath, pText):
    # Write the text depending using the correct python version
    if sys.version_info < (3, 0):
        file = io.open (pPath , mode='w', encoding='utf-8')
        file.write ( pText.decode('unicode_escape') ) 
        file.close() 
    else:
        file = open (pPath, 'w', encoding='utf-8') 
        if pText is None:
            pText = ""
        file.write (pText) 
        file.close() 

#-------------------------------------------------------------------------------
def append_line_to_file (pPath, pText):
    # append the line depending using the correct python version
    if sys.version_info < (3, 0):
        file = io.open (pPath , mode='a', encoding='utf-8')
        file.write ( pText.decode('unicode_escape') ) 
        file.close() 
    else:
        file = open (pPath, 'a', encoding='utf-8') 
        file.write (pText) 
        file.close() 

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
def get_file_content(path):

    f = open(path, 'r') 
    content = f.read() 
    f.close() 

    return content

#-------------------------------------------------------------------------------

def updateSubnets():
    global userSubnets
    
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

def sanitize_string(input):
    if isinstance(input, bytes):
        input = input.decode('utf-8')
    value = bytes_to_string(re.sub('[^a-zA-Z0-9-_\s]', '', str(input)))
    return value

#-------------------------------------------------------------------------------

def if_byte_then_to_str(input):
    if isinstance(input, bytes):
        input = input.decode('utf-8')
        input = bytes_to_string(re.sub('[^a-zA-Z0-9-_\s]', '', str(input)))
    return input

#-------------------------------------------------------------------------------

def bytes_to_string(value):
    # if value is of type bytes, convert to string
    if isinstance(value, bytes):
        value = value.decode('utf-8')
    return value

#-------------------------------------------------------------------------------

def add_json_list (row, list):
    new_row = []
    for column in row :        
        column = bytes_to_string(column)

        new_row.append(column)

    list.append(new_row)    

    return list

#-------------------------------------------------------------------------------

def to_text(_json):
    payloadData = ""
    if len(_json['internet']) > 0 and 'internet' in INCLUDED_SECTIONS:
        payloadData += "INTERNET\n"
        for event in _json['internet']:
            payloadData += event[3] + ' on ' + event[2] + '. ' + event[4] + '. New address:' + event[1] + '\n'

    if len(_json['new_devices']) > 0 and 'new_devices' in INCLUDED_SECTIONS:
        payloadData += "NEW DEVICES:\n"
        for event in _json['new_devices']:
            if event[4] is None:
                event[4] = event[11]
            payloadData += event[1] + ' - ' + event[4] + '\n'

    if len(_json['down_devices']) > 0 and 'down_devices' in INCLUDED_SECTIONS:
        write_file (logPath + '/down_devices_example.log', _json['down_devices'])
        payloadData += 'DOWN DEVICES:\n'
        for event in _json['down_devices']:
            if event[4] is None:
                event[4] = event[11]
            payloadData += event[1] + ' - ' + event[4] + '\n'
    
    if len(_json['events']) > 0 and 'events' in INCLUDED_SECTIONS:
        payloadData += "EVENTS:\n"
        for event in _json['events']:
            if event[8] != "Internet":
                payloadData += event[8] + " on " + event[1] + " " + event[3] + " at " + event[2] + "\n"

    return payloadData

#-------------------------------------------------------------------------------
def get_device_stats():

    # columns = ["online","down","all","archived","new","unknown"]
    sql.execute(sql_devices_stats)

    row = sql.fetchone()
    commitDB()

    return row
#-------------------------------------------------------------------------------
def get_all_devices():    

    sql.execute(sql_devices_all)

    row = sql.fetchall()

    commitDB()
    return row

#-------------------------------------------------------------------------------
def get_sql_array(query):    

    sql.execute(query)

    rows = sql.fetchall()

    commitDB()

    #  convert result into list of lists
    arr = []
    for row in rows:
        r_temp = []
        for column in row:
            r_temp.append(column)
        arr.append(r_temp)

    return arr


#-------------------------------------------------------------------------------
def removeDuplicateNewLines(text):
    if "\n\n\n" in text:
        return removeDuplicateNewLines(text.replace("\n\n\n", "\n\n"))
    else:
        return text

    
#-------------------------------------------------------------------------------
def hide_email(email):
    m = email.split('@')

    if len(m) == 2:
        return f'{m[0][0]}{"*"*(len(m[0])-2)}{m[0][-1] if len(m[0]) > 1 else ""}@{m[1]}'

    return email    

#-------------------------------------------------------------------------------
def check_and_run_event():
    sql.execute(""" select * from Parameters where par_ID = "Front_Event" """)
    rows = sql.fetchall()    

    event, param = ['','']
    if len(rows) > 0 and rows[0]['par_Value'] != 'finished':        
        event = rows[0]['par_Value'].split('|')[0]
        param = rows[0]['par_Value'].split('|')[1]
    else:
        return

    if event == 'test':
        handle_test(param)
    if event == 'run':
        handle_run(param)

    # clear event execution flag
    sql.execute ("UPDATE Parameters SET par_Value='finished' WHERE par_ID='Front_Event'")        

    # commit to DB  
    commitDB ()

#-------------------------------------------------------------------------------
def handle_run(runType):
    global last_network_scan

    mylog('info', ['[', timeNow(), '] START Run: ', runType])  

    if runType == 'ENABLE_ARPSCAN':
        last_network_scan = now_minus_24h        

    mylog('info', ['[', timeNow(), '] END Run: ', runType])

#-------------------------------------------------------------------------------
def handle_test(testType):

    mylog('info', ['[', timeNow(), '] START Test: ', testType])    

    # Open text sample    
    sample_txt = get_file_content(pialertPath + '/back/report_sample.txt')

    # Open html sample     
    sample_html = get_file_content(pialertPath + '/back/report_sample.html')

    # Open json sample and get only the payload part      
    sample_json_payload = json.loads(get_file_content(pialertPath + '/back/webhook_json_sample.json'))[0]["body"]["attachments"][0]["text"]      
    
    if testType == 'REPORT_MAIL':
        send_email(sample_txt, sample_html)
    if testType == 'REPORT_WEBHOOK':
        send_webhook (sample_json_payload, sample_txt)
    if testType == 'REPORT_APPRISE':
        send_apprise (sample_html, sample_txt) 
    if testType == 'REPORT_NTFY':
        send_ntfy (sample_txt)
    if testType == 'REPORT_PUSHSAFER':
        send_pushsafer (sample_txt)

    mylog('info', ['[', timeNow(), '] END Test: ', testType])


#-------------------------------------------------------------------------------
#  Return setting value
def get_setting_value(key):
    
    set = get_setting(key)

    if get_setting(key) is not None:

        setVal = set[6] # setting value
        setTyp = set[3] # setting type

        return setVal

    return ''

#-------------------------------------------------------------------------------
#  Return whole setting touple
def get_setting(key):
    result = None
    # index order: key, name, desc, inputtype, options, regex, result, group, events
    for set in mySettings:
        if set[0] == key:
            result = set
    
    if result is None:
        mylog('info', [' Error - setting_missing - Setting not found for key: ', key])           
        mylog('info', [' Error - logging the settings into file: ', logPath + '/setting_missing.json'])           
        write_file (logPath + '/setting_missing.json', json.dumps({ 'data' : mySettings}))    

    return result

#-------------------------------------------------------------------------------
def isNewVersion():   
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
        if len(data) > 0 and "published_at" in data[0]:        

            dateTimeStr = data[0]["published_at"]            

            realeaseTimestamp = int(datetime.datetime.strptime(dateTimeStr, '%Y-%m-%dT%H:%M:%SZ').strftime('%s'))            

            if realeaseTimestamp > buildTimestamp + 600:        
                mylog('none', ["    New version of the container available!"])
                newVersionAvailable = True 
                initOrSetParam('Back_New_Version_Available', str(newVersionAvailable))                

    return newVersionAvailable


#-------------------------------------------------------------------------------
# Plugins
#-------------------------------------------------------------------------------
def get_plugins_configs():

    pluginsDict = []
    pluginsList = []

    for root, dirs, files in os.walk(pluginsPath):
        for d in dirs:            # Loop over directories, not files
            pluginsDict.append(json.loads(get_file_content(pluginsPath + "/" + d + '/config.json'), object_hook=custom_plugin_decoder))   
            pluginsList.append(json.loads(get_file_content(pluginsPath + "/" + d + '/config.json')))          

    return plugins_class(pluginsDict, pluginsList)

#-------------------------------------------------------------------------------
class plugins_class:
    def __init__(self, dict, list):
        self.dict = dict
        self.list = list

#-------------------------------------------------------------------------------
def collect_lang_strings(json, pref):

    for prop in json["localized"]:                   
        for language_string in json[prop]:
            import_language_string(language_string["language_code"], pref + "_" + prop, language_string["string"])   
        

#-------------------------------------------------------------------------------
def import_language_string(code, key, value, extra = ""):

    sql.execute ("""INSERT INTO Plugins_Language_Strings ("Language_Code", "String_Key", "String_Value", "Extra") VALUES (?, ?, ?, ?)""", (str(code), str(key), str(value), str(extra))) 

    commitDB ()


#-------------------------------------------------------------------------------
def custom_plugin_decoder(pluginDict):
    return namedtuple('X', pluginDict.keys())(*pluginDict.values())

#-------------------------------------------------------------------------------
def run_plugin_scripts(runType):
    
    global plugins, tz, mySchedules

    # Header
    updateState("Run: Plugins")

    mylog('debug', ['     [Plugins] Check if any plugins need to be executed on run type: ', runType])

    for plugin in plugins.list:

        shouldRun = False

        set = get_plugin_setting(plugin, "RUN")
        if set != None and set['value'] == runType:
            if runType != "schedule":
                shouldRun = True
            elif  runType == "schedule":
                # run if overdue scheduled time   
                prefix = plugin["unique_prefix"]

                #  check scheduels if any contains a unique plugin prefix matching the current plugin
                for schd in mySchedules:
                    if schd.service == prefix:          
                        # Check if schedule overdue
                        shouldRun = schd.runScheduleCheck()  
                        if shouldRun:
                            # note the last time the scheduled plugin run was executed
                            schd.last_run = datetime.datetime.now(tz).replace(microsecond=0)

        if shouldRun:            
                        
            print_plugin_info(plugin, ['display_name'])
            mylog('debug', ['     [Plugins] CMD: ', get_plugin_setting(plugin, "CMD")["value"]])
            execute_plugin(plugin)

#-------------------------------------------------------------------------------
# Executes the plugin command specified in the setting with the function specified as CMD 
def execute_plugin(plugin):

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

    #  Prepare custom params
    params = []

    if "params" in plugin:
        for param in plugin["params"]:            
            resolved = ""

            #  Get setting value
            if param["type"] == "setting":
                resolved = get_setting(param["value"])

                if resolved != None:
                    resolved = plugin_param_from_glob_set(resolved)

            #  Get Sql result
            if param["type"] == "sql":
                resolved = flatten_array(get_sql_array(param["value"]))

            if resolved == None:
                mylog('none', ['     [Plugins] The parameter "name":"', param["name"], '" was resolved as None'])

            else:
                params.append( [param["name"], resolved] )
    

    # ------- prepare params --------
    # prepare command from plugin settings, custom parameters  
    command = resolve_wildcards(set_CMD, params).split()

    # Execute command
    mylog('verbose', ['     [Plugins] Executing: ', set_CMD])

    try:
        # try runnning a subprocess with a forced timeout in case the subprocess hangs
        output = subprocess.check_output (command, universal_newlines=True,  stderr=subprocess.STDOUT, timeout=(set_RUN_TIMEOUT))
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        mylog('none', [e.output])
        mylog('none', ['        [Plugins] Error - enable LOG_LEVEL=debug and check logs'])            
    except subprocess.TimeoutExpired as timeErr:
        mylog('none', ['        [Plugins] TIMEOUT - the process forcefully terminated as timeout reached']) 


    #  check the last run output
    f = open(pluginsPath + '/' + plugin["code_name"] + '/last_result.log', 'r+')
    newLines = f.read().split('\n')
    f.close()        

    # cleanup - select only lines containing a separator to filter out unnecessary data
    newLines = list(filter(lambda x: '|' in x, newLines))  

    if len(newLines) == 0: # check if the subprocess failed / there was no valid output
        mylog('none', ['        [Plugins] No output received from the plugin - enable LOG_LEVEL=debug and check logs'])
        return  
    else: 
        mylog('verbose', ['[', timeNow(), '] [Plugins]: SUCCESS, received ', len(newLines), ' entries'])      

    # # regular logging
    # for line in newLines:
    #     append_line_to_file (pluginsPath + '/plugin.log', line +'\n')         
    
    # build SQL query parameters to insert into the DB
    sqlParams = []

    for line in newLines:
        columns = line.split("|")
        # There has to be always 8 columns
        if len(columns) == 8:
            sqlParams.append((plugin["unique_prefix"], columns[0], columns[1], 'null', columns[2], columns[3], columns[4], columns[5], columns[6], 0, columns[7], 'null'))
        else:
            mylog('none', ['        [Plugins]: Skipped invalid line in the output: ', line])

    if len(sqlParams) > 0:                
        sql.executemany ("""INSERT INTO Plugins_Events ("Plugin", "Object_PrimaryID", "Object_SecondaryID", "DateTimeCreated", "DateTimeChanged", "Watched_Value1", "Watched_Value2", "Watched_Value3", "Watched_Value4", "Status" ,"Extra", "UserData") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", sqlParams) 
        commitDB ()

        process_plugin_events(plugin)

        # update API endpoints
        update_api(False, ["plugins_events","plugins_objects"])


#-------------------------------------------------------------------------------
# Check if watched values changed for the given plugin
def process_plugin_events(plugin):    

    global pluginObjects, pluginEvents

    pluginPref = plugin["unique_prefix"]

    plugObjectsArr = get_sql_array ("SELECT * FROM Plugins_Objects where Plugin = '" + str(pluginPref)+"'") 
    plugEventsArr  = get_sql_array ("SELECT * FROM Plugins_Events where Plugin = '" + str(pluginPref)+"'") 

    pluginObjects = []
    pluginEvents  = []

    for obj in plugObjectsArr: 
        pluginObjects.append(plugin_object_class(plugin, obj))

    existingPluginObjectsCount = len(pluginObjects)

    mylog('debug', ['     [Plugins] Existing objects: ', existingPluginObjectsCount])

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
            mylog('debug', ['     [Plugins] Found existing object'])
            pluginEvents[index].status = "exists"            

            # plugEventsArr.pop(index) # remove processed entry

        index += 1

    # Loop thru events and update the one that exist to determine if watched columns changed
    index = 0
    for tmpObjFromEvent in pluginEvents:  

        if tmpObjFromEvent.status == "exists": 

            #  compare hash of the changed watched columns for uniqueness
            if any(x.watchedHash != tmpObject.watchedHash for x in pluginObjects):
                pluginEvents[index].status = "watched-changed"                            

                # plugEventsArr.pop(index) # remove processed entry
            else:
                pluginEvents[index].status = "watched-not-changed"  

        index += 1

    # Merge existing plugin objects with newly discovered ones and update existin ones with new values
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
        
        q = f"UPDATE Plugins_Objects set Plugin = '{plugObj.pluginPref}', DateTimeChanged = '{plugObj.changed}', Watched_Value1 = '{plugObj.watched1}', Watched_Value2 = '{plugObj.watched2}', Watched_Value3 = '{plugObj.watched3}', Watched_Value4 = '{plugObj.watched4}', Status = '{plugObj.status}', Extra = '{plugObj.extra}' WHERE 'Index' = {plugObj.index}"

        sql.execute (q)

    # Update the Plugins_Events with the new statuses    
    
    sql.execute ("DELETE FROM Plugins_Events")

    for plugObj in pluginEvents: 

        createdTime = plugObj.created

        if plugObj.status == 'new':
            createdTime = plugObj.changed        

        sql.execute ("INSERT INTO Plugins_Events (Plugin, Object_PrimaryID, Object_SecondaryID, DateTimeCreated, DateTimeChanged, Watched_Value1, Watched_Value2, Watched_Value3, Watched_Value4, Status,  Extra, UserData) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (plugObj.pluginPref, plugObj.primaryId , plugObj.secondaryId , createdTime, plugObj.changed , plugObj.watched1 , plugObj.watched2 , plugObj.watched3 , plugObj.watched4 , plugObj.status , plugObj.extra, plugObj.userData ))    

        commitDB()

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

        self.idsHash      = str(hash(str(self.primaryId) + str(self.secondaryId)))    

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
def resolve_wildcards(command, params):

    mylog('debug', ['        [Plugins]: Pre-Resolved CMD: ', command])

    for param in params:
        mylog('debug', ['        [Plugins]: key     : {', param[0], '}'])
        mylog('debug', ['        [Plugins]: resolved: ', param[1]])
        command = command.replace('{' + param[0] + '}', param[1])

    mylog('debug', ['        [Plugins]: Resolved CMD: ', command])

    return command

#-------------------------------------------------------------------------------
# Check if there are events which need to be reported on based on settings
def plugin_check_smth_to_report(notifs):
    
    for notJsn in notifs:
        
        pref = notJsn['Plugin'] #"Plugin" column 
        stat = notJsn['Status'] #"Status" column 
                 
        val = get_setting_value(pref + '_REPORT_ON')

        if set is not None:
            
            # report if there is at least one value in teh events to be reported on
            # future improvement - selectively remove events based on this
            if stat in val: 
                return True

    return False


#-------------------------------------------------------------------------------
# Flattens a setting to make it passable to a script
def plugin_param_from_glob_set(globalSetting):

    setVal = globalSetting[6] # setting value
    setTyp = globalSetting[3] # setting type


    noConversion = ['text', 'integer', 'boolean', 'password', 'readonly', 'selectinteger', 'selecttext' ]
    arrayConversion = ['multiselect', 'list'] 

    if setTyp in noConversion:
        return setVal

    if setTyp in arrayConversion:
        return flatten_array(setVal)


#-------------------------------------------------------------------------------
# Gets the whole setting object
def get_plugin_setting(plugin, function_key):
    
    result = None

    for set in plugin['settings']:
        if set["function"] == function_key:
          result =  set 

    if result == None:
        mylog('none', ['     [Plugins] Setting with "function":"', function_key, '" is missing in plugin: ', get_plugin_string(plugin, 'display_name')])

    return result


#-------------------------------------------------------------------------------
# Get localized string value on the top JSON depth, not recursive
def get_plugin_string(props, el):

    result = ''

    if el in props['localized']:
        for str in props[el]:
            if str['language_code'] == 'en_us':
                result = str['string']
        
        if result == '':
            result = 'en_us string missing'

    else:
        result = props[el]
    
    return result

#-------------------------------------------------------------------------------
def print_plugin_info(plugin, elements = ['display_name']):

    mylog('verbose', ['     [Plugins] ---------------------------------------------']) 

    for el in elements:
        res = get_plugin_string(plugin, el)
        mylog('verbose', ['     [Plugins] ', el ,': ', res]) 

#-------------------------------------------------------------------------------
def flatten_array(arr):
    
    tmp = ''

    for arrayItem in arr:        
        # only one column flattening is supported
        if isinstance(arrayItem, list):            
            arrayItem = str(arrayItem[0])

        tmp += arrayItem + ','
        tmp = tmp.replace("'","").replace(' ','') # No single quotes or empty spaces allowed

    return tmp[:-1] # Remove last comma ','

    

#-------------------------------------------------------------------------------
# Cron-like Scheduling
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
            print_log("Scheduler run: YES")
            self.was_last_schedule_used = True
            result = True
        else:
            print_log("Scheduler run: NO")
        
        if self.was_last_schedule_used:
            self.was_last_schedule_used = False
            self.last_next_schedule = self.scheduleObject.next()            

        return result

#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    sys.exit(main())       
