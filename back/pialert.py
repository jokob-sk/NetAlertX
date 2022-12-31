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
import subprocess
import os
import re
import time
import decimal
import datetime
from datetime import timedelta
# from datetime import datetime
# from datetime import date
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

# from ssdpy import SSDPClient
# import upnpclient

#===============================================================================
# PATHS
#===============================================================================
PIALERT_BACK_PATH = os.path.dirname(os.path.abspath(__file__))
pialertPath = PIALERT_BACK_PATH + "/.."  #to fix - remove references and use pialertPath instead
logPath     = pialertPath + '/front/log'
pialertPath = '/home/pi/pialert'
confPath = "/config/pialert.conf"
dbPath = '/db/pialert.db'
fullConfPath = pialertPath + confPath
fullDbPath   = pialertPath + dbPath
STOPARPSCAN = pialertPath + "/db/setting_stoparpscan"

# Global variables

userSubnets = []
time_started = datetime.datetime.now()
cron_instance = Cron()
log_timestamp = time_started
lastTimeImported = 0
sql_connection = None

#-------------------------------------------------------------------------------
def timeNow():
    return datetime.datetime.now().replace(microsecond=0)
#-------------------------------------------------------------------------------
def file_print(*args):

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
    if not PRINT_LOG :
        return

    # Current Time    
    log_timestamp2 = datetime.datetime.now()

    # Print line + time + elapsed time + text
    file_print('[PRINT_LOG] ',
        log_timestamp2, ' ',
        log_timestamp2 - log_timestamp, ' ',
        pText)

    # Save current time to calculate elapsed time until next log
    log_timestamp = log_timestamp2 
    
#-------------------------------------------------------------------------------
# check RW access of DB and config file
def checkPermissionsOK():
    global confR_access, confW_access, dbR_access, dbW_access
    
    confR_access = (os.access(fullConfPath, os.R_OK))
    confW_access = (os.access(fullConfPath, os.W_OK))
    dbR_access = (os.access(fullDbPath, os.R_OK))
    dbW_access = (os.access(fullDbPath, os.W_OK))


    file_print('\n Permissions check (All should be True)')
    file_print('------------------------------------------------')
    file_print( "  " , confPath ,     " | " , " READ  | " , confR_access)
    file_print( "  " , confPath ,     " | " , " WRITE | " , confW_access)
    file_print( "  " , dbPath , "       | " , " READ  | " , dbR_access)
    file_print( "  " , dbPath , "       | " , " WRITE | " , dbW_access)
    file_print('------------------------------------------------')

    return dbR_access and dbW_access and confR_access and confW_access 

def fixPermissions():
    # Try fixing access rights if needed
    chmodCommands = []

    if dbR_access == False or dbW_access == False:
        chmodCommands.append(['sudo', 'chmod', 'a+rw', '-R', dbPath])
    if confR_access == False or confW_access == False:
        chmodCommands.append(['sudo', 'chmod', 'a+rw', '-R', confPath])

    for com in chmodCommands:
        # Execute command
        file_print("[Setup] Attempting to fix permissions.")
        try:
            # try runnning a subprocess
            result = subprocess.check_output (com, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            # An error occured, handle it
            file_print("[Setup] Fix Failed. Execute this command manually inside of the container: ", ' '.join(com)) 
            file_print(e.output)


checkPermissionsOK()

def initialiseFile(pathToCheck, defaultFile):
    # if file not readable (missing?) try to copy over the backed-up (default) one
    if str(os.access(pathToCheck, os.R_OK)) == "False":
        file_print("[Setup] The "+ pathToCheck +" file is not readable (missing?). Trying to copy over the backed-up (default) one.")      
        try:
            # try runnning a subprocess
            p = subprocess.Popen(["cp", defaultFile , pathToCheck], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            stdout, stderr = p.communicate()

            if str(os.access(pathToCheck, os.R_OK)) == "False":
                file_print("[Setup] Error copying the default file ("+defaultFile+") to it's destination ("+pathToCheck+"). Make sure the app has Read & Write access to the parent directory.")
            else:
                file_print("[Setup] Default file ("+defaultFile+") copied over successfully to ("+pathToCheck+").")

            # write stdout and stderr into .log files for debugging if needed
            logResult (stdout, stderr)
            
        except subprocess.CalledProcessError as e:
            # An error occured, handle it
            file_print("[Setup] Error copying the default file ("+defaultFile+"). Make sure the app has Read & Write access to " + pathToCheck)
            file_print(e.output)

#===============================================================================
# Basic checks and Setup
#===============================================================================

# check and initialize pialert.conf
if confR_access == False:
    initialiseFile(fullConfPath, "/home/pi/pialert/back/pialert.conf_bak" )

# check and initialize pialert.db
if dbR_access == False:
    initialiseFile(fullDbPath, "/home/pi/pialert/back/pialert.db_bak")

if dbR_access == False or confR_access == False:
    if checkPermissionsOK() == False:
        fixPermissions()


#===============================================================================
# USER CONFIG VARIABLES - DEFAULTS
#===============================================================================

vendorsDB              = '/usr/share/arp-scan/ieee-oui.txt'
piholeDB               = '/etc/pihole/pihole-FTL.db'
piholeDhcpleases       = '/etc/pihole/dhcp.leases'

# INITIALIZE VARIABLES from pialert.conf

# GENERAL settings
# ----------------------
PRINT_LOG               = False
TIMEZONE                = 'Europe/Berlin'
PIALERT_WEB_PROTECTION  = False
PIALERT_WEB_PASSWORD    = '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92'
INCLUDED_SECTIONS       = ['internet', 'new_devices', 'down_devices', 'events']  
SCAN_CYCLE_MINUTES      = 5            

SCAN_SUBNETS            = ['192.168.1.0/24 --interface=eth1', '192.168.1.0/24 --interface=eth0']

DAYS_TO_KEEP_EVENTS     = 90

# EMAIL settings
# ----------------------
SMTP_SERVER             = ''
SMTP_PORT               = 587
SMTP_USER               = ''
SMTP_PASS               = ''
SMTP_SKIP_TLS           = False
SMTP_SKIP_LOGIN	        = False

REPORT_MAIL             = False
REPORT_FROM             = 'Pi.Alert <' + SMTP_USER +'>'
REPORT_TO               = 'user@gmail.com'
REPORT_DASHBOARD_URL    = 'http://pi.alert/'

# Webhook settings
# ----------------------
REPORT_WEBHOOK          = False
WEBHOOK_URL             = ''
WEBHOOK_PAYLOAD         = 'json'       
WEBHOOK_REQUEST_METHOD  = 'GET'        

# Apprise settings
#-----------------------
REPORT_APPRISE          = False
APPRISE_URL = ''
APPRISE_HOST = ''

# NTFY (https://ntfy.sh/) settings
# ----------------------
REPORT_NTFY             = False
NTFY_USER = ''
NTFY_PASSWORD = ''
NTFY_TOPIC = ''
NTFY_HOST = 'https://ntfy.sh'

# PUSHSAFER (https://www.pushsafer.com/) settings
# ----------------------
REPORT_PUSHSAFER        = False
PUSHSAFER_TOKEN         = 'ApiKey'

# MQTT settings
# ----------------------
REPORT_MQTT = False
MQTT_BROKER = ''
MQTT_PORT   = ''
MQTT_CLIENT_ID = 'PiAlert'
MQTT_USER = ''
MQTT_PASSWORD = ''
MQTT_QOS = 0
MQTT_DELAY_SEC = 2

# DynDNS
# ----------------------
DDNS_ACTIVE             = False
DDNS_DOMAIN             = 'your_domain.freeddns.org'
DDNS_USER               = 'dynu_user'
DDNS_PASSWORD           = 'A0000000B0000000C0000000D0000000'
DDNS_UPDATE_URL         = 'https://api.dynu.com/nic/update?'

# PIHOLE settings
# ----------------------
PIHOLE_ACTIVE           = False                         
DHCP_ACTIVE             = False                         


# Pholus settings
# ----------------------
PHOLUS_ACTIVE           = True
PHOLUS_TIMEOUT          = 180  
PHOLUS_FORCE            = False
PHOLUS_DAYS_DATA        = 7

PHOLUS_RUN              = 'none'
PHOLUS_RUN_SCHD         = '0 4 * * *'
PHOLUS_RUN_TIMEOUT      = 600


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
def closeDB ():
    global sql_connection
    global sql

    # Check if DB is open
    if sql_connection == None :
        return

    # Log    
    print_log ('Closing DB')

    # Close DB
    sql_connection.commit()
    sql_connection.close()
    sql_connection = None   

#-------------------------------------------------------------------------------
# Import user values

def check_config_dict(key, default, config):
    if key in config:
        return config[key]
    else: 
        return default

#-------------------------------------------------------------------------------

def importConfig (): 

    # Specify globals so they can be overwritten with the new config
    global lastTimeImported
    # General
    global SCAN_SUBNETS, PRINT_LOG, TIMEZONE, PIALERT_WEB_PROTECTION, PIALERT_WEB_PASSWORD, INCLUDED_SECTIONS, SCAN_CYCLE_MINUTES, DAYS_TO_KEEP_EVENTS, REPORT_DASHBOARD_URL
    # Email
    global REPORT_MAIL, SMTP_SERVER, SMTP_PORT, REPORT_TO, REPORT_FROM, SMTP_SKIP_LOGIN, SMTP_USER, SMTP_PASS, SMTP_SKIP_TLS
    # Webhooks
    global REPORT_WEBHOOK, WEBHOOK_URL, WEBHOOK_PAYLOAD, WEBHOOK_REQUEST_METHOD
    # Apprise
    global REPORT_APPRISE, APPRISE_HOST, APPRISE_URL
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

    # get config file
    config_file = Path(fullConfPath)

    # Skip import if last time of import is NEWER than file age 
    if (os.path.getmtime(config_file) < lastTimeImported) :
        return
    
    # load the variables from  pialert.conf
    code = compile(config_file.read_text(), config_file.name, "exec")
    config_dict = {}
    exec(code, {"__builtins__": {}}, config_dict)

    # Import setting if found in the dictionary
    # General
    SCAN_SUBNETS = check_config_dict('SCAN_SUBNETS', SCAN_SUBNETS , config_dict)
    PRINT_LOG = check_config_dict('PRINT_LOG', PRINT_LOG , config_dict)
    TIMEZONE = check_config_dict('TIMEZONE', TIMEZONE , config_dict)
    PIALERT_WEB_PROTECTION = check_config_dict('PIALERT_WEB_PROTECTION', PIALERT_WEB_PROTECTION , config_dict)
    PIALERT_WEB_PASSWORD = check_config_dict('PIALERT_WEB_PASSWORD', PIALERT_WEB_PASSWORD , config_dict)
    INCLUDED_SECTIONS = check_config_dict('INCLUDED_SECTIONS', INCLUDED_SECTIONS , config_dict)
    SCAN_CYCLE_MINUTES = check_config_dict('SCAN_CYCLE_MINUTES', SCAN_CYCLE_MINUTES , config_dict)
    DAYS_TO_KEEP_EVENTS = check_config_dict('DAYS_TO_KEEP_EVENTS', DAYS_TO_KEEP_EVENTS , config_dict)
    REPORT_DASHBOARD_URL = check_config_dict('REPORT_DASHBOARD_URL', REPORT_DASHBOARD_URL , config_dict)

    # Email
    REPORT_MAIL = check_config_dict('REPORT_MAIL', REPORT_MAIL , config_dict)
    SMTP_SERVER = check_config_dict('SMTP_SERVER', SMTP_SERVER , config_dict)
    SMTP_PORT = check_config_dict('SMTP_PORT', SMTP_PORT , config_dict)
    REPORT_TO = check_config_dict('REPORT_TO', REPORT_TO , config_dict)
    REPORT_FROM = check_config_dict('REPORT_FROM', REPORT_FROM , config_dict)
    SMTP_SKIP_LOGIN = check_config_dict('SMTP_SKIP_LOGIN', SMTP_SKIP_LOGIN , config_dict)
    SMTP_USER = check_config_dict('SMTP_USER', SMTP_USER , config_dict)
    SMTP_PASS = check_config_dict('SMTP_PASS', SMTP_PASS , config_dict)
    SMTP_SKIP_TLS = check_config_dict('SMTP_SKIP_TLS', SMTP_SKIP_TLS , config_dict)

    # Webhooks
    REPORT_WEBHOOK = check_config_dict('REPORT_WEBHOOK', REPORT_WEBHOOK , config_dict)
    WEBHOOK_URL = check_config_dict('WEBHOOK_URL', WEBHOOK_URL , config_dict)
    WEBHOOK_PAYLOAD = check_config_dict('WEBHOOK_PAYLOAD', WEBHOOK_PAYLOAD , config_dict)
    WEBHOOK_REQUEST_METHOD = check_config_dict('WEBHOOK_REQUEST_METHOD', WEBHOOK_REQUEST_METHOD , config_dict)

    # Apprise
    REPORT_APPRISE = check_config_dict('REPORT_APPRISE', REPORT_APPRISE , config_dict)
    APPRISE_HOST = check_config_dict('APPRISE_HOST', APPRISE_HOST , config_dict)
    APPRISE_URL = check_config_dict('APPRISE_URL', APPRISE_URL , config_dict)

    # NTFY
    REPORT_NTFY = check_config_dict('REPORT_NTFY', REPORT_NTFY , config_dict)
    NTFY_HOST = check_config_dict('NTFY_HOST', NTFY_HOST , config_dict)
    NTFY_TOPIC = check_config_dict('NTFY_TOPIC', NTFY_TOPIC , config_dict)
    NTFY_USER = check_config_dict('NTFY_USER', NTFY_USER , config_dict)
    NTFY_PASSWORD = check_config_dict('NTFY_PASSWORD', NTFY_PASSWORD , config_dict)

    # PUSHSAFER
    REPORT_PUSHSAFER = check_config_dict('REPORT_PUSHSAFER', REPORT_PUSHSAFER , config_dict)
    PUSHSAFER_TOKEN = check_config_dict('PUSHSAFER_TOKEN', PUSHSAFER_TOKEN , config_dict)

    # MQTT
    REPORT_MQTT = check_config_dict('REPORT_MQTT', REPORT_MQTT , config_dict)
    MQTT_BROKER = check_config_dict('MQTT_BROKER', MQTT_BROKER , config_dict)
    MQTT_PORT = check_config_dict('MQTT_PORT', MQTT_PORT , config_dict)
    MQTT_USER = check_config_dict('MQTT_USER', MQTT_USER , config_dict)
    MQTT_PASSWORD = check_config_dict('MQTT_PASSWORD', MQTT_PASSWORD , config_dict)
    MQTT_QOS = check_config_dict('MQTT_QOS', MQTT_QOS , config_dict)
    MQTT_DELAY_SEC = check_config_dict('MQTT_DELAY_SEC', MQTT_DELAY_SEC , config_dict)

    # DynDNS
    DDNS_ACTIVE = check_config_dict('DDNS_ACTIVE', DDNS_ACTIVE , config_dict)
    DDNS_DOMAIN = check_config_dict('DDNS_DOMAIN', DDNS_DOMAIN , config_dict)
    DDNS_USER = check_config_dict('DDNS_USER', DDNS_USER , config_dict)
    DDNS_PASSWORD = check_config_dict('DDNS_PASSWORD', DDNS_PASSWORD , config_dict)
    DDNS_UPDATE_URL = check_config_dict('DDNS_UPDATE_URL', DDNS_UPDATE_URL , config_dict)

    # PiHole
    PIHOLE_ACTIVE = check_config_dict('PIHOLE_ACTIVE',  PIHOLE_ACTIVE, config_dict)
    DHCP_ACTIVE = check_config_dict('DHCP_ACTIVE', DHCP_ACTIVE , config_dict)

    # PHOLUS
    PHOLUS_ACTIVE = check_config_dict('PHOLUS_ACTIVE', PHOLUS_ACTIVE , config_dict)
    PHOLUS_TIMEOUT = check_config_dict('PHOLUS_TIMEOUT', PHOLUS_TIMEOUT , config_dict)
    PHOLUS_FORCE = check_config_dict('PHOLUS_FORCE', PHOLUS_FORCE , config_dict)
    PHOLUS_RUN = check_config_dict('PHOLUS_RUN', PHOLUS_RUN , config_dict)
    PHOLUS_RUN_TIMEOUT = check_config_dict('PHOLUS_RUN_TIMEOUT', PHOLUS_RUN_TIMEOUT , config_dict)   
    PHOLUS_RUN_SCHD = check_config_dict('PHOLUS_RUN_SCHD', PHOLUS_RUN_SCHD , config_dict)
    PHOLUS_DAYS_DATA = check_config_dict('PHOLUS_DAYS_DATA', PHOLUS_DAYS_DATA , config_dict)
 

    openDB()    

    #  Code_Name, Display_Name, Description, Type, Options, Value, Group
    settings = [

        # General
        ('SCAN_SUBNETS', 'Subnets to scan', '',  'subnets', '', '' , str(SCAN_SUBNETS) , 'General'),
        ('PRINT_LOG', 'Print additional logging', '',  'boolean', '', '' , str(PRINT_LOG) , 'General'),
        ('TIMEZONE', 'Time zone', '',  'text', '', '' ,str(TIMEZONE) , 'General'),
        ('PIALERT_WEB_PROTECTION', 'Enable logon', '', 'boolean', '', '' , str(PIALERT_WEB_PROTECTION) , 'General'),
        ('PIALERT_WEB_PASSWORD', 'Logon password', '', 'readonly', '', '' , str(PIALERT_WEB_PASSWORD) , 'General'),
        ('INCLUDED_SECTIONS', 'Notify on changes in', '', 'multiselect', "['internet', 'new_devices', 'down_devices', 'events']", '' , str(INCLUDED_SECTIONS) , 'General'),
        ('SCAN_CYCLE_MINUTES', 'Scan cycle delay (m)', '', 'integer', '', '' , str(SCAN_CYCLE_MINUTES) , 'General'),
        ('DAYS_TO_KEEP_EVENTS', 'Delete events older than (days)', '', 'integer', '', '' , str(DAYS_TO_KEEP_EVENTS) , 'General'),
        ('REPORT_DASHBOARD_URL', 'PiAlert URL', '',  'text', '', '' , str(REPORT_DASHBOARD_URL) , 'General'),        

        # Email
        ('REPORT_MAIL', 'Enable email', '',  'boolean', '', '' , str(REPORT_MAIL) , 'Email'),
        ('SMTP_SERVER', 'SMTP server URL', '',  'text', '', '' , str(SMTP_SERVER) , 'Email'),
        ('SMTP_PORT', 'SMTP port', '',  'integer', '', '' , str(SMTP_PORT) , 'Email'),
        ('REPORT_TO', 'Email to', '',  'text', '', '' , str(REPORT_TO) , 'Email'),
        ('REPORT_FROM', 'Email Subject', '',  'text', '', '' , str(REPORT_FROM) , 'Email'),
        ('SMTP_SKIP_LOGIN', 'SMTP skip login', '',  'boolean', '', '' , str(SMTP_SKIP_LOGIN) , 'Email'),
        ('SMTP_USER', 'SMTP user', '',  'text', '', '' , str(SMTP_USER) , 'Email'),
        ('SMTP_PASS', 'SMTP password', '',  'password', '', '' , str(SMTP_PASS) , 'Email'),
        ('SMTP_SKIP_TLS', 'SMTP skip TLS', '',  'boolean', '', '' , str(SMTP_SKIP_TLS) , 'Email'), 

        # Webhooks
        ('REPORT_WEBHOOK', 'Enable Webhooks', '',  'boolean', '', '' , str(REPORT_WEBHOOK) , 'Webhooks'),
        ('WEBHOOK_URL', 'Target URL', '',  'text', '', '' , str(WEBHOOK_URL) , 'Webhooks'),
        ('WEBHOOK_PAYLOAD', 'Payload type', '',  'selecttext', "['json', 'html', 'text']", '' , str(WEBHOOK_PAYLOAD) , 'Webhooks'),
        ('WEBHOOK_REQUEST_METHOD', 'Request type', '',  'selecttext', "['GET', 'POST', 'PUT']", '' , str(WEBHOOK_REQUEST_METHOD) , 'Webhooks'),

        # Apprise
        ('REPORT_APPRISE', 'Enable Apprise', '',  'boolean', '', '' , str(REPORT_APPRISE) , 'Apprise'),
        ('APPRISE_HOST', 'Apprise host URL', '',  'text', '', '' , str(APPRISE_HOST) , 'Apprise'),
        ('APPRISE_URL', 'Apprise notification URL', '',  'text', '', '' , str(APPRISE_URL) , 'Apprise'),

        # NTFY
        ('REPORT_NTFY', 'Enable NTFY', '',  'boolean', '', '' , str(REPORT_NTFY) , 'NTFY'),
        ('NTFY_HOST', 'NTFY host URL', '',  'text', '', '' , str(NTFY_HOST) , 'NTFY'),
        ('NTFY_TOPIC', 'NTFY topic', '',  'text', '', '' , str(NTFY_TOPIC) , 'NTFY'),
        ('NTFY_USER', 'NTFY user', '',  'text', '', '' , str(NTFY_USER) , 'NTFY'),
        ('NTFY_PASSWORD', 'NTFY password', '',  'password', '', '' , str(NTFY_PASSWORD) , 'NTFY'),

        # PUSHSAFER
        ('REPORT_PUSHSAFER', 'Enable PUSHSAFER', '',  'boolean', '', '' , str(REPORT_PUSHSAFER) , 'PUSHSAFER'),
        ('PUSHSAFER_TOKEN', 'PUSHSAFER token', '',  'text', '', '' , str(PUSHSAFER_TOKEN) , 'PUSHSAFER'),

        # MQTT
        ('REPORT_MQTT', 'Enable MQTT', '',  'boolean', '', '' , str(REPORT_MQTT) , 'MQTT'),
        ('MQTT_BROKER', 'MQTT broker host URL', '',  'text', '', '' , str(MQTT_BROKER) , 'MQTT'),
        ('MQTT_PORT', 'MQTT broker port', '',  'integer', '', '' , str(MQTT_PORT) , 'MQTT'),
        ('MQTT_USER', 'MQTT user', '',  'text', '', '' , str(MQTT_USER) , 'MQTT'),
        ('MQTT_PASSWORD', 'MQTT password', '',  'password', '', '' , str(MQTT_PASSWORD) , 'MQTT'),
        ('MQTT_QOS', 'MQTT Quality of Service', '',  'selectinteger', "['0', '1', '2']", '' , str(MQTT_QOS) , 'MQTT'),
        ('MQTT_DELAY_SEC', 'MQTT delay per device (s)', '',  'selectinteger', "['2', '3', '4', '5']", '' , str(MQTT_DELAY_SEC) , 'MQTT'),

        #DynDNS
        ('DDNS_ACTIVE', 'Enable DynDNS', '',  'boolean', '', '' , str(DDNS_ACTIVE) , 'DynDNS'),
        # ('QUERY_MYIP_SERVER', 'Query MY IP Server URL', '',  'text', '', '' , QUERY_MYIP_SERVER , 'DynDNS'),
        ('DDNS_DOMAIN', 'DynDNS domain URL', '',  'text', '', '' , str(DDNS_DOMAIN) , 'DynDNS'),
        ('DDNS_USER', 'DynDNS user', '',  'text', '', '' , str(DDNS_USER) , 'DynDNS'),
        ('DDNS_PASSWORD', 'DynDNS password', '',  'password', '', '' , str(DDNS_PASSWORD) , 'DynDNS'),
        ('DDNS_UPDATE_URL', 'DynDNS update URL', '',  'text', '', '' , str(DDNS_UPDATE_URL) , 'DynDNS'),

        # PiHole
        ('PIHOLE_ACTIVE', 'Enable PiHole mapping', '',  'boolean', '', '' , str(PIHOLE_ACTIVE) , 'PiHole'),
        ('DHCP_ACTIVE', 'Enable PiHole DHCP', '',  'boolean', '', '' , str(DHCP_ACTIVE) , 'PiHole'),

        # Pholus
        ('PHOLUS_ACTIVE', 'Enable Pholus scans', '',  'boolean', '', '' , str(PHOLUS_ACTIVE) , 'Pholus'),
        ('PHOLUS_TIMEOUT', 'Pholus timeout', '',  'integer', '', '' , str(PHOLUS_TIMEOUT) , 'Pholus'),
        ('PHOLUS_FORCE', 'Pholus force check', '',  'boolean', '', '' , str(PHOLUS_FORCE) , 'Pholus'),        
        ('PHOLUS_RUN', 'Pholus enable schedule', '',  'selecttext', "['none', 'once', 'schedule']", '' , str(PHOLUS_RUN) , 'Pholus'),
        ('PHOLUS_RUN_TIMEOUT', 'Pholus timeout schedule', '',  'integer', '', '' , str(PHOLUS_RUN_TIMEOUT) , 'Pholus'),
        ('PHOLUS_RUN_SCHD', 'Pholus schedule', '',  'text', '', '' , str(PHOLUS_RUN_SCHD) , 'Pholus'),
        ('PHOLUS_DAYS_DATA', 'Pholus keep days', '',  'integer', '', '' , str(PHOLUS_DAYS_DATA) , 'Pholus')        

    ]
    # Insert into DB    
    sql.execute ("DELETE FROM Settings")
    
    sql.executemany ("""INSERT INTO Settings ("Code_Name", "Display_Name", "Description", "Type", "Options",
         "RegEx", "Value", "Group" ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", settings)


    # Used to determine the next import
    lastTimeImported = time.time()
    
    closeDB()

    # Update scheduler
    global schedule, tz, last_next_pholus_schedule, last_next_pholus_schedule_used

    tz       = timezone(TIMEZONE)    
    cron     = Cron(PHOLUS_RUN_SCHD)
    schedule = cron.schedule(start_date=datetime.datetime.now(tz))

    last_next_pholus_schedule = schedule.next()
    last_next_pholus_schedule_used = False

    # Format and prepare the list of subnets
    updateSubnets()

    file_print('[', timeNow(), '] Config: Imported new config')  
#-------------------------------------------------------------------------------

#===============================================================================
# USER CONFIG VARIABLES - END
#===============================================================================

#===============================================================================
# MAIN
#===============================================================================
cycle = ""
check_report = [1, "internet_IP", "update_vendors_silent"]
last_pholus_scheduled_run = 0

# timestamps of last execution times
startTime = time_started
now_minus_24h = time_started - datetime.timedelta(hours = 24)

last_network_scan = now_minus_24h
last_internet_IP_scan = now_minus_24h
last_run = now_minus_24h
last_cleanup = now_minus_24h
last_update_vendors = time_started - datetime.timedelta(days = 6) # update vendors 24h after first run and than once a week


def main ():
    # Initialize global variables
    global time_started, cycle, last_network_scan, last_internet_IP_scan, last_run, last_cleanup, last_update_vendors, last_pholus_scheduled_run
    # second set of global variables
    global startTime, log_timestamp, sql_connection, sql

    # DB
    sql_connection = None
    sql            = None

    # Upgrade DB if needed
    upgradeDB()
    
    while True:

        # update NOW time
        time_started = datetime.datetime.now()

        # re-load user configuration
        importConfig() 

        # proceed if 1 minute passed
        if last_run + datetime.timedelta(minutes=1) < time_started :

             # last time any scan or maintenance/Upkeep was run
            last_run = time_started

            # Header
            updateState("Process: Start")
            file_print('[', timeNow(), '] Process: Start')                

            # Timestamp
            startTime = time_started
            startTime = startTime.replace (microsecond=0)      

            # determine run/scan type based on passed time
            if last_internet_IP_scan + datetime.timedelta(minutes=3) < time_started:
                cycle = 'internet_IP'                
                last_internet_IP_scan = time_started
                check_internet_IP()

            # Update vendors once a week
            if last_update_vendors + datetime.timedelta(days = 7) < time_started:
                last_update_vendors = time_started
                cycle = 'update_vendors'
                update_devices_MAC_vendors()

            # Execute Pholus scheduled scan if enabled and run conditions fulfilled
            if PHOLUS_RUN == "schedule" or PHOLUS_RUN == "once":

                runPholus = False

                # run once after application starts
                if PHOLUS_RUN == "once" and last_pholus_scheduled_run == 0:
                    runPholus = True

                # run if overdue scheduled time
                if (not runPholus) and (PHOLUS_RUN == "schedule"):
                    # cron_instance.from_string(PHOLUS_RUN_SCHD)
                    runPholus = runSchedule()

                if runPholus:
                    last_pholus_scheduled_run = datetime.datetime.now(tz).replace(microsecond=0)
                    performPholusScan(PHOLUS_RUN_TIMEOUT)

            # Perform an arp-scan if not disable with a file
            if last_network_scan + datetime.timedelta(minutes=SCAN_CYCLE_MINUTES) < time_started and os.path.exists(STOPARPSCAN) == False:
                last_network_scan = time_started
                cycle = 1 # network scan
                scan_network() 
            
            # Reporting   
            if cycle in check_report:         
                email_reporting()

            # clean up the DB once a day
            if last_cleanup + datetime.timedelta(hours = 24) < time_started:
                last_cleanup = time_started
                cycle = 'cleanup'  
                cleanup_database()   

            # Close SQL
            closeDB()            

            # Final message
            if cycle != "":
                action = str(cycle)
                if action == "1":
                    action = "network_scan"
                file_print('[', timeNow(), '] Last action: ', action)
                cycle = ""

            # Footer
            updateState("Process: Wait")
            file_print('[', timeNow(), '] Process: Wait')            
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
    file_print('[', startTime, '] Check Internet IP:')    

    # Get Internet IP
    file_print('    Retrieving Internet IP:')
    internet_IP = get_internet_IP()
    # TESTING - Force IP
        # internet_IP = "1.2.3.4"

    # Check result = IP
    if internet_IP == "" :
        file_print('    Error retrieving Internet IP')
        file_print('    Exiting...')
        return False
    file_print('      ', internet_IP)

    # Get previous stored IP
    file_print('    Retrieving previous IP:')    
    previous_IP = get_previous_internet_IP ()
    file_print('      ', previous_IP)

    # Check IP Change
    if internet_IP != previous_IP :
        file_print('    Saving new IP')
        save_new_internet_IP (internet_IP)
        file_print('        IP updated')        
    else :
        file_print('    No changes to perform')    

    # Get Dynamic DNS IP
    if DDNS_ACTIVE :
        file_print('    Retrieving Dynamic DNS IP')
        dns_IP = get_dynamic_DNS_IP()

        # Check Dynamic DNS IP
        if dns_IP == "" :
            file_print('    Error retrieving Dynamic DNS IP')
            file_print('    Exiting...')
        file_print('   ', dns_IP)

        # Check DNS Change
        if dns_IP != internet_IP :
            file_print('    Updating Dynamic DNS IP')
            message = set_dynamic_DNS_IP ()
            file_print('       ', message)            
        else :
            file_print('    No changes to perform')
    else :
        file_print('    Skipping Dynamic DNS update')



#-------------------------------------------------------------------------------
def get_internet_IP ():
    # BUGFIX #46 - curl http://ipv4.icanhazip.com repeatedly is very slow
    # Using 'dig'
    dig_args = ['dig', '+short', '-4', 'myip.opendns.com', '@resolver1.opendns.com']
    try:
        cmd_output = subprocess.check_output (dig_args, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        file_print(e.output)
        cmd_output = '' # no internet
    

    ## BUGFIX #12 - Query IPv4 address (not IPv6)
    ## Using 'curl' instead of 'dig'
    ## curl_args = ['curl', '-s', 'https://diagnostic.opendns.com/myip']
    #curl_args = ['curl', '-s', QUERY_MYIP_SERVER]
    #cmd_output = subprocess.check_output (curl_args, universal_newlines=True)

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
        file_print(e.output)
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
        file_print(e.output)
        curl_output = ""    
    
    return curl_output
    
#-------------------------------------------------------------------------------
def get_previous_internet_IP ():
    # get previos internet IP stored in DB
    openDB()
    sql.execute ("SELECT dev_LastIP FROM Devices WHERE dev_MAC = 'Internet' ")
    previous_IP = sql.fetchone()[0]
    closeDB()

    # return previous IP
    return previous_IP

#-------------------------------------------------------------------------------
def save_new_internet_IP (pNewIP):
    # Log new IP into logfile
    append_line_to_file (logPath + '/IP_changes.log',
        '['+str(startTime) +']\t'+ pNewIP +'\n')

    prevIp = get_previous_internet_IP() 

    openDB()
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
    sql_connection.commit()
    closeDB()
    
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
    file_print('[', startTime, '] Upkeep Database:' )

    openDB()    
   
    # Cleanup Online History
    file_print('    Upkeep Online_History')
    sql.execute ("DELETE FROM Online_History WHERE Scan_Date <= date('now', '-1 day')")
    file_print('    Optimize Database')

    # Cleanup Events
    file_print('    Upkeep Events, delete all older than '+str(DAYS_TO_KEEP_EVENTS)+' days')
    sql.execute ("DELETE FROM Events WHERE eve_DateTime <= date('now', '-"+str(DAYS_TO_KEEP_EVENTS)+" day')")

    # Cleanup Pholus_Scan
    file_print('    Upkeep Pholus_Scan, delete all older than ' + str(PHOLUS_DAYS_DATA) + ' days')
    sql.execute ("DELETE FROM Pholus_Scan WHERE Time <= date('now', '-"+ str(PHOLUS_DAYS_DATA) +" day')") # improvement possibility: keep at least N per mac

    # Shrink DB
    file_print('    Shrink Database')
    sql.execute ("VACUUM;")

    closeDB()

#===============================================================================
# UPDATE DEVICE MAC VENDORS
#===============================================================================
def update_devices_MAC_vendors (pArg = ''):
    # Header    
    updateState("Upkeep: Vendors")
    file_print('[', startTime, '] Upkeep - Update HW Vendors:' )

    # Update vendors DB (iab oui)
    file_print('    Updating vendors DB (iab & oui)')
    # update_args = ['sh', PIALERT_BACK_PATH + '/update_vendors.sh', ' > ', logPath +  '/update_vendors.log',    '2>&1']
    update_args = ['sh', PIALERT_BACK_PATH + '/update_vendors.sh', pArg]

    try:
        # try runnning a subprocess
        update_output = subprocess.check_output (update_args)
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        file_print(e.output)        
    
    # DEBUG
        # update_args = ['./vendors_db_update.sh']
        # subprocess.call (update_args, shell=True)

    # Initialize variables
    recordsToUpdate = []
    ignored = 0
    notFound = 0

    # All devices loop
    file_print('    Searching devices vendor')
    openDB()
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
    file_print("    Devices Ignored:  ", ignored)
    file_print("    Vendors Not Found:", notFound)
    file_print("    Vendors updated:  ", len(recordsToUpdate) )
    # DEBUG - print list of record to update
        # file_print(recordsToUpdate)

    # update devices
    sql.executemany ("UPDATE Devices SET dev_Vendor = ? WHERE dev_MAC = ? ",
        recordsToUpdate )

    # DEBUG - print number of rows updated
        # file_print(sql.rowcount)

    # Close DB
    closeDB()

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
            file_print(e.output)
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
    
    # # devtest start

    # file_print("---------------------------------------------")

    #     client = SSDPClient()

    # devices = client.m_search("ssdp:all")

    # for device in devices:
    #     print(device.get("usn"))
    #     print("000000000000000000000000000000000000000000000000000000000000\n")
    #     print(device)

    # print("---------------------------------------------")

    # devices = upnpclient.discover()

    # print("---------------------------------------------")

    # for device in devices:
    #     print(device)

    # print("---------------------------------------------")


    # sockAddr = ("192.168.1.14", 443);

    # sockInfo = socket.getnameinfo(sockAddr, socket.NI_NAMEREQD);

    # # find an example using NI_MAXHOST

    # print(sockInfo);


    # nmap > vendor > espressifg > ESP32 type
    # UDP ports
    #  nmap -sU 192.168.1.14 

    # # devtest end

    # Header
    updateState("Scan: Network")
    file_print('[', startTime, '] Scan Devices:' )       

    # # Query ScanCycle properties
    print_log ('Query ScanCycle confinguration')
    scanCycle_data = query_ScanCycle_Data (True)
    if scanCycle_data is None:
        file_print('\n*************** ERROR ***************')
        file_print('ScanCycle %s not found' % cycle )
        file_print('    Exiting...\n')
        return False

    # ScanCycle data        
    cycle_interval  = scanCycle_data['cic_EveryXmin']
    
    # arp-scan command    
    file_print('    arp-scan start')    
    arpscan_devices = execute_arpscan ()
    print_log ('arp-scan ends')
    
    # DEBUG - print number of rows updated    
    # file_print('aspr-scan result:', len(arpscan_devices))

    # Pi-hole method    
    if PIHOLE_ACTIVE :       
        file_print('    Pi-hole start')
        openDB()    
        copy_pihole_network() 
        closeDB() 

    # DHCP Leases method    
    if DHCP_ACTIVE :        
        file_print('    DHCP Leases start')
        openDB()
        read_DHCP_leases () 
        closeDB()

    # Load current scan data
    file_print('  Processing scan results') 
    openDB()   
    save_scanned_devices (arpscan_devices, cycle_interval)    
    
    # Print stats
    print_log ('Print Stats')
    print_scan_stats()
    print_log ('Stats end')

    # Create Events
    file_print('  Updating DB Info')
    file_print('    Sessions Events (connect / discconnect)')
    insert_events()

    # Create New Devices
    # after create events -> avoid 'connection' event
    file_print('    Creating new devices')
    create_new_devices ()

    # Update devices info
    file_print('    Updating Devices Info')
    update_devices_data_from_scan ()

    # Resolve devices names
    print_log ('    Resolve devices names')
    update_devices_names()

    # Void false connection - disconnections
    file_print('    Voiding false (ghost) disconnections')
    void_ghost_disconnections ()
  
    # Pair session events (Connection / Disconnection)
    file_print('    Pairing session events (connection / disconnection) ')
    pair_sessions_events()  
  
    # Sessions snapshot
    file_print('    Creating sessions snapshot')
    create_sessions_snapshot ()
  
    # Skip repeated notifications
    file_print('    Skipping repeated notifications')
    skip_repeated_notifications ()
  
    # Commit changes
    openDB()
    sql_connection.commit()
    closeDB()

    return reporting

#-------------------------------------------------------------------------------
def query_ScanCycle_Data (pOpenCloseDB = False):
    # Check if is necesary open DB
    if pOpenCloseDB :
        openDB()

    # Query Data
    sql.execute ("""SELECT cic_arpscanCycles, cic_EveryXmin
                    FROM ScanCycles
                    WHERE cic_ID = ? """, (cycle,))
    sqlRow = sql.fetchone()

    # Check if is necesary close DB
    if pOpenCloseDB :
        closeDB()

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

    # DEBUG
        # file_print(devices_list)
        # file_print(unique_mac)
        # file_print(unique_devices)
        # file_print(len(devices_list))
        # file_print(len(unique_mac))
        # file_print(len(unique_devices))

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
        file_print(e.output)
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
    # DEBUG
        # file_print(sql.rowcount)
    return reporting

#-------------------------------------------------------------------------------
def save_scanned_devices (p_arpscan_devices, p_cycle_interval):
    cycle = 1 # always 1, only one cycle supported

    openDB()    

    # Delete previous scan data
    sql.execute ("DELETE FROM CurrentScan WHERE cur_ScanCycle = ?",
                (cycle,))

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
    file_print('    Devices Detected.......: ', str (sql.fetchone()[0]) )

    # Devices arp-scan
    sql.execute ("""SELECT COUNT(*) FROM CurrentScan
                    WHERE cur_ScanMethod='arp-scan' AND cur_ScanCycle = ? """,
                    (cycle,))
    file_print('        arp-scan detected..: ', str (sql.fetchone()[0]) )

    # Devices Pi-hole
    sql.execute ("""SELECT COUNT(*) FROM CurrentScan
                    WHERE cur_ScanMethod='PiHole' AND cur_ScanCycle = ? """,
                    (cycle,))
    file_print('        Pi-hole detected...: +' + str (sql.fetchone()[0]) )

    # New Devices
    sql.execute ("""SELECT COUNT(*) FROM CurrentScan
                    WHERE cur_ScanCycle = ? 
                      AND NOT EXISTS (SELECT 1 FROM Devices
                                      WHERE dev_MAC = cur_MAC) """,
                    (cycle,))
    file_print('        New Devices........: ' + str (sql.fetchone()[0]) )

    # Devices in this ScanCycle
    sql.execute ("""SELECT COUNT(*) FROM Devices, CurrentScan
                    WHERE dev_MAC = cur_MAC AND dev_ScanCycle = cur_ScanCycle
                      AND dev_ScanCycle = ? """,
                    (cycle,))
    
    file_print('    Devices in this cycle..: ' + str (sql.fetchone()[0]) )

    # Down Alerts
    sql.execute ("""SELECT COUNT(*) FROM Devices
                    WHERE dev_AlertDeviceDown = 1
                      AND dev_ScanCycle = ?
                      AND NOT EXISTS (SELECT 1 FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC
                                        AND dev_ScanCycle = cur_ScanCycle) """,
                    (cycle,))
    file_print('        Down Alerts........: ' + str (sql.fetchone()[0]) )

    # New Down Alerts
    sql.execute ("""SELECT COUNT(*) FROM Devices
                    WHERE dev_AlertDeviceDown = 1
                      AND dev_PresentLastScan = 1
                      AND dev_ScanCycle = ?
                      AND NOT EXISTS (SELECT 1 FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC
                                        AND dev_ScanCycle = cur_ScanCycle) """,
                    (cycle,))
    file_print('        New Down Alerts....: ' + str (sql.fetchone()[0]) )

    # New Connections
    sql.execute ("""SELECT COUNT(*) FROM Devices, CurrentScan
                    WHERE dev_MAC = cur_MAC AND dev_ScanCycle = cur_ScanCycle
                      AND dev_PresentLastScan = 0
                      AND dev_ScanCycle = ? """,
                    (cycle,))
    file_print('        New Connections....: ' + str ( sql.fetchone()[0]) )

    # Disconnections
    sql.execute ("""SELECT COUNT(*) FROM Devices
                    WHERE dev_PresentLastScan = 1
                      AND dev_ScanCycle = ?
                      AND NOT EXISTS (SELECT 1 FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC
                                        AND dev_ScanCycle = cur_ScanCycle) """,
                    (cycle,))
    file_print('        Disconnections.....: ' + str ( sql.fetchone()[0]) )

    # IP Changes
    sql.execute ("""SELECT COUNT(*) FROM Devices, CurrentScan
                    WHERE dev_MAC = cur_MAC AND dev_ScanCycle = cur_ScanCycle
                      AND dev_ScanCycle = ?
                      AND dev_LastIP <> cur_IP """,
                    (cycle,))
    file_print('        IP Changes.........: ' + str ( sql.fetchone()[0]) )

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

    # DEBUG - print list of record to update
        # file_print(recordsToUpdate)
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

    # Devices without name
    file_print('        Trying to resolve devices without name')
    # BUGFIX #97 - Updating name of Devices w/o IP
    openDB()    
    sql.execute ("SELECT * FROM Devices WHERE dev_Name IN ('(unknown)','', '(name not found)') AND dev_LastIP <> '-'")
    unknownDevices = sql.fetchall() 
    closeDB()

    # perform Pholus scan if (unknown) devices found
    if PHOLUS_ACTIVE and (len(unknownDevices) > 0 or PHOLUS_FORCE):        
        performPholusScan(PHOLUS_TIMEOUT)

    # get names from Pholus scan 
    # sql.execute ('SELECT * FROM Pholus_Scan where "MAC" in (select "dev_MAC" from Devices where "dev_Name" IN ("(unknown)","")) and "Record_Type"="Answer"')        
    openDB()    
    sql.execute ('SELECT * FROM Pholus_Scan where "Record_Type"="Answer"')    
    pholusResults = list(sql.fetchall())        
    closeDB()

    # Number of entries from previous Pholus scans
    file_print("          Pholus entries from prev scans: ", len(pholusResults))

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
    file_print("        Names Found (DiG/Pholus): ", len(recordsToUpdate), " (",foundDig,"/",foundPholus ,")" )                 
    file_print("        Names Not Found         : ", len(recordsNotFound) )
    
    openDB()    
    # update not found devices with (name not found) 
    sql.executemany ("UPDATE Devices SET dev_Name = ? WHERE dev_MAC = ? ", recordsNotFound )
    # update names of devices which we were bale to resolve
    sql.executemany ("UPDATE Devices SET dev_Name = ? WHERE dev_MAC = ? ", recordsToUpdate )
    closeDB()
    # DEBUG - print number of rows updated
    # file_print(sql.rowcount)

#-------------------------------------------------------------------------------
def performPholusScan (timeout):

    # scan every interface
    for subnet in userSubnets:

        temp = subnet.split("--interface=")

        if len(temp) != 2:
            file_print("        Skip scan (need subnet in format '192.168.1.0/24 --inteface=eth0'), got: ", subnet)
            return

        mask = temp[0].strip()
        interface = temp[1].strip()

        file_print("        Pholus scan on [interface] ", interface, " [mask] " , mask)

        updateState("Scan: Pholus")        
        file_print('[', timeNow(), '] Scan: Pholus for ', str(timeout), 's ('+ str(round(int(timeout) / 60, 1)) +'min)')  
        
        adjustedTimeout = str(round(int(timeout) / 2, 0)) # the scan alwasy lasts 2x as long, so the desired user time from settings needs to be halved
        pholus_args = ['python3', '/home/pi/pialert/pholus/pholus3.py', interface, "-rdns_scanning", mask, "-stimeout", adjustedTimeout]

        # Execute command
        try:
            # try runnning a subprocess
            output = subprocess.check_output (pholus_args, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            # An error occured, handle it
            file_print(e.output)
            file_print("Error - PholusScan - check logs")
            output = ""

        if output != "":
            file_print('[', timeNow(), '] Scan: Pholus SUCCESS')
            write_file (logPath + '/pialert_pholus_lastrun.log', output)
            for line in output.split("\n"):
                append_line_to_file (logPath + '/pialert_pholus.log', line +'\n')        

            params = []

            for line in output.split("\n"):
                columns = line.split("|")
                if len(columns) == 4:
                    params.append(( interface + " " + mask, timeNow() , columns[0].replace(" ", ""), columns[1].replace(" ", ""), columns[2].replace(" ", ""), columns[3], ''))

            if len(params) > 0:
                openDB ()
                sql.executemany ("""INSERT INTO Pholus_Scan ("Info", "Time", "MAC", "IP_v4_or_v6", "Record_Type", "Value", "Extra") VALUES (?, ?, ?, ?, ?, ?, ?)""", params) 
                closeDB ()

        else:
            file_print('[', timeNow(), '] Scan: Pholus FAIL - check logs') 


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
    # Nest-Audio-ff77ff77ff77ff77ff77ff77ff77ff77 (remove 32 chars at the end matching a regex?)

    str = str.replace(".", "")

    return str


# Disclaimer - I'm interfacing with a script I didn't write (pholus3.py) so it's possible I'm missing types of answers
# it's also possible the pholus3.py script can be adjusted to provide a better output to interface with it
# Hit me with a PR if you know how! :)
def resolve_device_name_pholus (pMAC, pIP, allRes):
    
    pholusMatchesIndexes = []

    index = 0
    for result in allRes:
        if result["MAC"] == pMAC and result["Record_Type"] == "Answer" and '._googlezone' not in result["Value"]:
            # found entries with a matching MAC address, let's collect indexes 
            # pholusMatchesAll.append([list(item) for item in result]) 
            pholusMatchesIndexes.append(index)

        index += 1

    # file_print('pholusMatchesIndexes:', len(pholusMatchesIndexes))       

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
        # pMACstr = str(pMAC)
        
        # # Check MAC parameter
        # mac = pMACstr.replace (':','')
        # # file_print( ">>>>>> DIG >>>>>")
        # if len(pMACstr) != 17 or len(mac) != 12 :
        #     return -2

        # DEBUG
        # file_print(pMAC, pIP)

        # Resolve name with DIG
        # file_print( ">>>>>> DIG1 >>>>>")
        dig_args = ['dig', '+short', '-x', pIP]

        # Execute command
        try:
            # try runnning a subprocess
            newName = subprocess.check_output (dig_args, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            # An error occured, handle it
            file_print(e.output)            
            # newName = "Error - check logs"
            return -1

        # file_print( ">>>>>> DIG2 >>>>> Name", newName)

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
    openDB()
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
    closeDB()

#-------------------------------------------------------------------------------
def pair_sessions_events ():
    # NOT NECESSARY FOR INCREMENTAL UPDATE
    # print_log ('Pair session - 1 Clean')
    # sql.execute ("""UPDATE Events
    #                 SET eve_PairEventRowid = NULL
    #                 WHERE eve_EventType IN ('New Device', 'Connected')
    #              """ )

    openDB()

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

    closeDB()

#-------------------------------------------------------------------------------
def create_sessions_snapshot ():

    openDB()
    # Clean sessions snapshot
    print_log ('Sessions Snapshot - 1 Clean')
    sql.execute ("DELETE FROM SESSIONS" )

    # Insert sessions
    print_log ('Sessions Snapshot - 2 Insert')
    sql.execute ("""INSERT INTO Sessions
                    SELECT * FROM Convert_Events_to_Sessions""" )

#    OLD FORMAT INSERT IN TWO PHASES
#    PERFORMACE BETTER THAN SELECT WITH UNION
#
#    # Insert sessions from first query
#    print_log ('Sessions Snapshot - 2 Query 1')
#    sql.execute ("""INSERT INTO Sessions
#                    SELECT * FROM Convert_Events_to_Sessions_Phase1""" )
#
#    # Insert sessions from first query
#    print_log ('Sessions Snapshot - 3 Query 2')
#    sql.execute ("""INSERT INTO Sessions
#                    SELECT * FROM Convert_Events_to_Sessions_Phase2""" )

    print_log ('Sessions end')
    closeDB()



#-------------------------------------------------------------------------------
def skip_repeated_notifications ():
    
    openDB()

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

    closeDB()


#===============================================================================
# REPORTING
#===============================================================================
# create a json for webhook and mqtt notifications to provide further integration options  
json_final = []

def email_reporting ():
    global mail_text
    global mail_html

    deviceUrl              = REPORT_DASHBOARD_URL + '/deviceDetails.php?mac='

    # Reporting section
    file_print('  Check if something to report')
    openDB()

    # prepare variables for JSON construction
    json_internet = []
    json_new_devices = []
    json_down_devices = []
    json_events = []

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
    template_file = open(PIALERT_BACK_PATH + '/report_template.txt', 'r') 
    mail_text = template_file.read() 
    template_file.close() 

    # Open html Template
    template_file = open(PIALERT_BACK_PATH + '/report_template.html', 'r') 
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
        mail_section_Internet = False
        mail_text_Internet = ''
        mail_html_Internet = ''
        text_line_template = '{} \t{}\t{}\t{}\n'
        html_line_template = '<tr>\n'+ \
            '  <td> <a href="{}{}"> {} </a> </td>\n  <td> {} </td>\n'+ \
            '  <td style="font-size: 24px; color:#D02020"> {} </td>\n'+ \
            '  <td> {} </td>\n</tr>\n'

        sql.execute ("""SELECT * FROM Events
                        WHERE eve_PendingAlertEmail = 1 AND eve_MAC = 'Internet'
                        ORDER BY eve_DateTime""")

        
        for eventAlert in sql :
            mail_section_Internet = 'internet' in INCLUDED_SECTIONS
            # collect "internet" (IP changes) for the webhook json   
            json_internet = add_json_list (eventAlert, json_internet)

            mail_text_Internet += text_line_template.format (
                'Event:', eventAlert['eve_EventType'], 'Time:', eventAlert['eve_DateTime'],
                'IP:', eventAlert['eve_IP'], 'More Info:', eventAlert['eve_AdditionalInfo'])
            mail_html_Internet += html_line_template.format (
                deviceUrl, eventAlert['eve_MAC'],
                eventAlert['eve_EventType'], eventAlert['eve_DateTime'],
                eventAlert['eve_IP'], eventAlert['eve_AdditionalInfo'])


        format_report_section (mail_section_Internet, 'SECTION_INTERNET',
            'TABLE_INTERNET', mail_text_Internet, mail_html_Internet)

    if 'new_devices' in INCLUDED_SECTIONS:
        # Compose New Devices Section
        mail_section_new_devices = False
        mail_text_new_devices = ''
        mail_html_new_devices = ''
        text_line_template = '{}\t{}\n\t{}\t{}\n\t{}\t{}\n\t{}\t{}\n\t{}\t{}\n\n'
        html_line_template    = '<tr>\n'+ \
            '  <td> <a href="{}{}"> {} </a> </td>\n  <td> {} </td>\n'+\
            '  <td> {} </td>\n  <td> {} </td>\n  <td> {} </td>\n</tr>\n'
        
        sql.execute ("""SELECT * FROM Events_Devices
                        WHERE eve_PendingAlertEmail = 1
                        AND eve_EventType = 'New Device'
                        ORDER BY eve_DateTime""")

        for eventAlert in sql :
            mail_section_new_devices = 'new_devices' in INCLUDED_SECTIONS
            # collect "new_devices" for the webhook json  
            json_new_devices = add_json_list (eventAlert, json_new_devices)

            mail_text_new_devices += text_line_template.format (
                'Name: ', eventAlert['dev_Name'], 'MAC: ', eventAlert['eve_MAC'], 'IP: ', eventAlert['eve_IP'],
                'Time: ', eventAlert['eve_DateTime'], 'More Info: ', eventAlert['eve_AdditionalInfo'])
            mail_html_new_devices += html_line_template.format (
                deviceUrl, eventAlert['eve_MAC'], eventAlert['eve_MAC'],
                eventAlert['eve_DateTime'], eventAlert['eve_IP'],
                eventAlert['dev_Name'], eventAlert['eve_AdditionalInfo'])
    
        format_report_section (mail_section_new_devices, 'SECTION_NEW_DEVICES',
            'TABLE_NEW_DEVICES', mail_text_new_devices, mail_html_new_devices)


    if 'down_devices' in INCLUDED_SECTIONS:
        # Compose Devices Down Section
        mail_section_devices_down = False
        mail_text_devices_down = ''
        mail_html_devices_down = ''
        text_line_template = '{}\t{}\n\t{}\t{}\n\t{}\t{}\n\t{}\t{}\n\n'
        html_line_template     = '<tr>\n'+ \
            '  <td> <a href="{}{}"> {} </a>  </td>\n  <td> {} </td>\n'+ \
            '  <td> {} </td>\n  <td> {} </td>\n</tr>\n'

        sql.execute ("""SELECT * FROM Events_Devices
                        WHERE eve_PendingAlertEmail = 1
                        AND eve_EventType = 'Device Down'
                        ORDER BY eve_DateTime""")

        for eventAlert in sql :
            mail_section_devices_down = 'down_devices' in INCLUDED_SECTIONS
            # collect "down_devices" for the webhook json
            json_down_devices = add_json_list (eventAlert, json_down_devices)

            mail_text_devices_down += text_line_template.format (
                'Name: ', eventAlert['dev_Name'], 'MAC: ', eventAlert['eve_MAC'],
                'Time: ', eventAlert['eve_DateTime'],'IP: ', eventAlert['eve_IP'])
            mail_html_devices_down += html_line_template.format (
                deviceUrl, eventAlert['eve_MAC'], eventAlert['eve_MAC'],
                eventAlert['eve_DateTime'], eventAlert['eve_IP'],
                eventAlert['dev_Name'])

        format_report_section (mail_section_devices_down, 'SECTION_DEVICES_DOWN',
            'TABLE_DEVICES_DOWN', mail_text_devices_down, mail_html_devices_down)


    if 'events' in INCLUDED_SECTIONS:
        # Compose Events Section
        mail_section_events = False
        mail_text_events   = ''
        mail_html_events   = ''
        text_line_template = '{}\t{}\n\t{}\t{}\n\t{}\t{}\n\t{}\t{}\n\t{}\t{}\n\t{}\t{}\n\n'
        html_line_template = '<tr>\n  <td>'+ \
                ' <a href="{}{}"> {} </a> </td>\n  <td> {} </td>\n'+ \
                '  <td> {} </td>\n  <td> {} </td>\n  <td> {} </td>\n'+ \
                '  <td> {} </td>\n</tr>\n'

        sql.execute ("""SELECT * FROM Events_Devices
                        WHERE eve_PendingAlertEmail = 1
                        AND eve_EventType IN ('Connected','Disconnected',
                            'IP Changed')
                        ORDER BY eve_DateTime""")

        for eventAlert in sql :
            mail_section_events = 'events' in INCLUDED_SECTIONS
            # collect "events" for the webhook json
            json_events = add_json_list (eventAlert, json_events)
            
            mail_text_events += text_line_template.format (
                'Name: ', eventAlert['dev_Name'], 'MAC: ', eventAlert['eve_MAC'], 
                'IP: ', eventAlert['eve_IP'],'Time: ', eventAlert['eve_DateTime'],
                'Event: ', eventAlert['eve_EventType'],'More Info: ', eventAlert['eve_AdditionalInfo'])
            mail_html_events += html_line_template.format (
                deviceUrl, eventAlert['eve_MAC'], eventAlert['eve_MAC'],
                eventAlert['eve_DateTime'], eventAlert['eve_IP'],
                eventAlert['eve_EventType'], eventAlert['dev_Name'],
                eventAlert['eve_AdditionalInfo'])

        format_report_section (mail_section_events, 'SECTION_EVENTS',
            'TABLE_EVENTS', mail_text_events, mail_html_events)

    json_final = {
                    "internet": json_internet,                        
                    "new_devices": json_new_devices,
                    "down_devices": json_down_devices,                        
                    "events": json_events
                    }    

    # DEBUG - Write output emails for testing
    #if True :
    #    write_file (logPath + '/report_output.txt', mail_text) 
    #    write_file (logPath + '/report_output.html', mail_html) 

    # Send Mail
    if json_internet != [] or json_new_devices != [] or json_down_devices != [] or json_events != []:
        file_print('    Changes detected, sending reports')

        if REPORT_MAIL and check_config('email'):  
            updateState("Send: Email")
            file_print('      Sending report by Email')
            send_email (mail_text, mail_html)
        else :
            file_print('    Skip mail')
        if REPORT_APPRISE and check_config('apprise'):
            updateState("Send: Apprise")
            file_print('      Sending report by Apprise')
            send_apprise (mail_html)
        else :
            file_print('      Skip Apprise')
        if REPORT_WEBHOOK and check_config('webhook'):
            updateState("Send: Webhook")
            file_print('      Sending report by Webhook')
            send_webhook (json_final, mail_text)
        else :
            file_print('      Skip webhook')
        if REPORT_NTFY and check_config('ntfy'):
            updateState("Send: NTFY")
            file_print('      Sending report by NTFY')
            send_ntfy (mail_text)
        else :
            file_print('      Skip NTFY')
        if REPORT_PUSHSAFER and check_config('pushsafer'):
            updateState("Send: PUSHSAFER")
            file_print('      Sending report by PUSHSAFER')
            send_pushsafer (mail_text)
        else :
            file_print('      Skip PUSHSAFER')
        # Update MQTT entities
        if REPORT_MQTT and check_config('mqtt'):
            updateState("Send: MQTT")
            file_print('      Establishing MQTT thread')                          
            mqtt_start()        
        else :
            file_print('      Skip MQTT')
    else :
        file_print('    No changes to report')

    openDB()

    # Clean Pending Alert Events
    sql.execute ("""UPDATE Devices SET dev_LastNotification = ?
                    WHERE dev_MAC IN (SELECT eve_MAC FROM Events
                                      WHERE eve_PendingAlertEmail = 1)
                 """, (datetime.datetime.now(),) )
    sql.execute ("""UPDATE Events SET eve_PendingAlertEmail = 0
                    WHERE eve_PendingAlertEmail = 1""")

    # DEBUG - print number of rows updated
    file_print('    Notifications: ', sql.rowcount)

    # Commit changes
    sql_connection.commit()
    closeDB()

#-------------------------------------------------------------------------------
def check_config(service):

    if service == 'email':
        if SMTP_PASS == '' or SMTP_SERVER == '' or SMTP_USER == '' or REPORT_FROM == '' or REPORT_TO == '':
            file_print('    Error: Email service not set up correctly. Check your pialert.conf SMTP_*, REPORT_FROM and REPORT_TO variables.')
            return False
        else:
            return True   

    if service == 'apprise':
        if APPRISE_URL == '' or APPRISE_HOST == '':
            file_print('    Error: Apprise service not set up correctly. Check your pialert.conf APPRISE_* variables.')
            return False
        else:
            return True  

    if service == 'webhook':
        if WEBHOOK_URL == '':
            file_print('    Error: Webhook service not set up correctly. Check your pialert.conf WEBHOOK_* variables.')
            return False
        else:
            return True 

    if service == 'ntfy':
        if NTFY_HOST == '' or NTFY_TOPIC == '':
            file_print('    Error: NTFY service not set up correctly. Check your pialert.conf NTFY_* variables.')
            return False
        else:
            return True 

    if service == 'pushsafer':
        if PUSHSAFER_TOKEN == 'ApiKey':
            file_print('    Error: Pushsafer service not set up correctly. Check your pialert.conf PUSHSAFER_TOKEN variable.')
            return False
        else:
            return True 

    if service == 'mqtt':
        if MQTT_BROKER == '' or MQTT_PORT == '' or MQTT_USER == '' or MQTT_PASSWORD == '':
            file_print('    Error: MQTT service not set up correctly. Check your pialert.conf MQTT_* variables.')
            return False
        else:
            return True 

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
def write_file (pPath, pText):
    # Write the text depending using the correct python version
    if sys.version_info < (3, 0):
        file = io.open (pPath , mode='w', encoding='utf-8')
        file.write ( pText.decode('unicode_escape') ) 
        file.close() 
    else:
        file = open (pPath, 'w', encoding='utf-8') 
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
def send_email (pText, pHTML):

    # Print more info for debugging if PRINT_LOG enabled
    print_log ('REPORT_TO: ' + hide_email(str(REPORT_TO)) + '  SMTP_USER: ' + hide_email(str(SMTP_USER))) 

    # Compose email
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Pi.Alert Report'
    msg['From'] = REPORT_FROM
    msg['To'] = REPORT_TO
    msg.attach (MIMEText (pText, 'plain'))
    msg.attach (MIMEText (pHTML, 'html'))

    # Send mail
    smtp_connection = smtplib.SMTP (SMTP_SERVER, SMTP_PORT)
    smtp_connection.ehlo()

    if not SafeParseGlobalBool("SMTP_SKIP_TLS"):
        smtp_connection.starttls()
        smtp_connection.ehlo()
    if not SafeParseGlobalBool("SMTP_SKIP_LOGIN"):
        smtp_connection.login (SMTP_USER, SMTP_PASS)

    smtp_connection.sendmail (REPORT_FROM, REPORT_TO, msg.as_string())
    smtp_connection.quit()

#-------------------------------------------------------------------------------
def SafeParseGlobalBool(boolVariable):
    if boolVariable in globals():
        return eval(boolVariable)
    return False

#-------------------------------------------------------------------------------
def send_webhook (_json, _html):

    # use data type based on specified payload type
    if WEBHOOK_PAYLOAD == 'json':
        payloadData = _json        
    if WEBHOOK_PAYLOAD == 'html':
        payloadData = _html
    if WEBHOOK_PAYLOAD == 'text':
        payloadData = to_text(_json)

    #Define slack-compatible payload
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
        file_print(e.output)

#-------------------------------------------------------------------------------
def send_apprise (html):
    #Define Apprise compatible payload (https://github.com/caronc/apprise-api#stateless-solution)
    _json_payload={
    "urls": APPRISE_URL,
    "title": "Pi.Alert Notifications",
    "format": "html",
    "body": html
    }

    try:
        # try runnning a subprocess
        p = subprocess.Popen(["curl","-i","-X", "POST" ,"-H", "Content-Type:application/json" ,"-d", json.dumps(_json_payload), APPRISE_HOST], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = p.communicate()
        # write stdout and stderr into .log files for debugging if needed
        logResult (stdout, stderr)      
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        file_print(e.output)    

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
            file_print("Waiting to reconnect to MQTT broker")
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
            file_print("        Connected to broker")            
            mqtt_connected_to_broker = True     # Signal connection 
        else: 
            file_print("        Connection failed")
            mqtt_connected_to_broker = False


    client = mqtt_client.Client(MQTT_CLIENT_ID)   # Set Connecting Client ID    
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

    file_print("        Estimated delay: ", (len(devices) * int(MQTT_DELAY_SEC)), 's ', '(', round((len(devices) * int(MQTT_DELAY_SEC))/60,1) , 'min)' )

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

    openDB()

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
      file_print("[upgradeDB] Adding dev_Network_Node_MAC_ADDR to the Devices table")   
      sql.execute("""      
      ALTER TABLE "Devices" ADD "dev_Network_Node_MAC_ADDR" TEXT      
      """)

    # dev_Network_Node_port column
    dev_Network_Node_port_missing = sql.execute ("""
      SELECT COUNT(*) AS CNTREC FROM pragma_table_info('Devices') WHERE name='dev_Network_Node_port'
      """).fetchone()[0] == 0

    if dev_Network_Node_port_missing :
      file_print("[upgradeDB] Adding dev_Network_Node_port to the Devices table")     
      sql.execute("""      
      ALTER TABLE "Devices" ADD "dev_Network_Node_port" INTEGER 
      """)

    # Re-creating Parameters table
    file_print("[upgradeDB] Re-creating Parameters table")
    sql.execute("DROP TABLE Parameters;")

    sql.execute("""      
      CREATE TABLE "Parameters" (
        "par_ID"	TEXT,
        "par_Value"	TEXT
      );      
      """)    

    params = [
    # General
    ('Front_Events_Period', '1 day'),
    ('Front_Details_Sessions_Rows', '50'),
    ('Front_Details_Events_Rows', '50'),
    ('Front_Details_Events_Hide', 'True'),
    ('Front_Events_Rows', '50'),
    ('Front_Details_Period', '1 day'),
    ('Front_Devices_Order', '[[3,"desc"],[0,"asc"]]'),
    ('Front_Devices_Rows', '100'),
    ('Front_Details_Tab', 'tabDetails'),
    ('Back_App_State', 'Initializing')
    ] 

    sql.executemany ("""INSERT INTO Parameters ("par_ID", "par_Value") VALUES (?, ?)""", params)  

    # indicates, if Settings table is available 
    settingsMissing = sql.execute("""
    SELECT name FROM sqlite_master WHERE type='table'
    AND name='Settings'; 
    """).fetchone() == None

    # Re-creating Settings table    
    file_print("[upgradeDB] Re-creating Settings table")

    if settingsMissing == False:   
        sql.execute("DROP TABLE Settings;")       

    sql.execute("""      
    CREATE TABLE "Settings" (        
    "Code_Name"	TEXT,
    "Display_Name"	TEXT,
    "Description"	TEXT,        
    "Type" TEXT,
    "Options" TEXT,
    "RegEx"   TEXT,
    "Value"	TEXT,
    "Group"	TEXT
    );      
    """)

    # indicates, if Pholus_Scan table is available 
    pholusScanMissing = sql.execute("""
    SELECT name FROM sqlite_master WHERE type='table'
    AND name='Pholus_Scan'; 
    """).fetchone() == None

    # if pholusScanMissing == False:
    #     # Re-creating Pholus_Scan table    
    #     file_print("[upgradeDB] Re-creating Pholus_Scan table")
    #     sql.execute("DROP TABLE Pholus_Scan;")       
    #     pholusScanMissing = True  

    if pholusScanMissing:
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
      
    # don't hog DB access  
    closeDB ()

#-------------------------------------------------------------------------------
def updateState(newState):
    openDB()

    sql.execute ("UPDATE Parameters SET par_Value='"+ newState +"' WHERE par_ID='Back_App_State'")        

    # don't hog DB access  
    closeDB ()

 
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
# UTIL
#===============================================================================
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

    openDB()

    # columns = ["online","down","all","archived","new","unknown"]
    sql.execute("""      
      SELECT Online_Devices as online, Down_Devices as down, All_Devices as 'all', Archived_Devices as archived, (select count(*) from Devices a where dev_NewDevice = 1 ) as new, (select count(*) from Devices a where dev_Name = '(unknown)' or dev_Name = '(name not found)' ) as unknown from Online_History order by Scan_Date desc limit  1 
      """)

    row = sql.fetchone()

    closeDB()
    return row
#-------------------------------------------------------------------------------
def get_all_devices():

    openDB()

    sql.execute("""      
        select dev_MAC, dev_Name, dev_DeviceType, dev_Vendor, dev_Group, dev_FirstConnection, dev_LastConnection, dev_LastIP, dev_StaticIP, dev_PresentLastScan, dev_LastNotification, dev_NewDevice, dev_Network_Node_MAC_ADDR from Devices 
      """)

    row = sql.fetchall()

    closeDB()
    return row


#-------------------------------------------------------------------------------
def hide_email(email):
    m = email.split('@')
    return f'{m[0][0]}{"*"*(len(m[0])-2)}{m[0][-1] if len(m[0]) > 1 else ""}@{m[1]}'

#-------------------------------------------------------------------------------
def runSchedule():

    global last_next_pholus_schedule
    global last_pholus_scheduled_run
    global last_next_pholus_schedule_used

    result = False 

    # Initialize the last run time if never run before
    if last_pholus_scheduled_run == 0:
        last_pholus_scheduled_run =  (datetime.datetime.now(tz) - timedelta(days=365)).replace(microsecond=0)

    # get the current time with the currently specified timezone
    nowTime = datetime.datetime.now(tz).replace(microsecond=0)

    # #  DEBUG
    # file_print("now                      : ", nowTime.isoformat())
    # file_print("last_pholus_scheduled_run: ", last_pholus_scheduled_run.isoformat())
    # file_print("last_next_pholus_schedule: ", last_next_pholus_schedule.isoformat())
    # file_print("nowTime > last_next_pholus_schedule: ", nowTime > last_next_pholus_schedule)
    # file_print("last_pholus_scheduled_run < last_next_pholus_schedule: ", last_pholus_scheduled_run < last_next_pholus_schedule)

    # Run the schedule if the current time is past the schedule time we saved last time and 
    #               (maybe the following check is unnecessary:)
    # if the last run is past the last time we run a scheduled Pholus scan
    if nowTime > last_next_pholus_schedule and last_pholus_scheduled_run < last_next_pholus_schedule:
        print_log("Scheduler run: YES")
        last_next_pholus_schedule_used = True
        result = True
    else:
        print_log("Scheduler run: NO")
    
    if last_next_pholus_schedule_used:
        last_next_pholus_schedule_used = False
        last_next_pholus_schedule = schedule.next()            

    return result

#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    sys.exit(main())       
