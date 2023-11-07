""" config related functions for Pi.Alert """

# TODO: Create and manage this as part of an app_state class object
#===============================================================================

# These are global variables, not config items and should not exist !
mySettings = []
mySettingsSQLsafe = []
cycle = 1
userSubnets = []
mySchedules = [] # bad solution for global - TO-DO
plugins = []  # bad solution for global - TO-DO
tz = ''

# modified time of the most recently imported config file
# set to a small value to force import at first run
lastImportedConfFile = 1.1 

plugins_once_run = False
newVersionAvailable = False
time_started = ''
startTime = ''
last_scan_run = ''
last_version_check = ''
arpscan_devices = []

# ACTUAL CONFIGRATION ITEMS set to defaults

# -------------------------------------------
# General
# -------------------------------------------
SCAN_SUBNETS    = ['192.168.1.0/24 --interface=eth1', '192.168.1.0/24 --interface=eth0']   
LOG_LEVEL       = 'verbose' 
TIMEZONE        = 'Europe/Berlin'
DIG_GET_IP_ARG  = '-4 myip.opendns.com @resolver1.opendns.com' 
UI_LANG         = 'English' 
UI_PRESENCE     = ['online', 'offline', 'archived']  
PIALERT_WEB_PROTECTION  = False 
PIALERT_WEB_PASSWORD    = '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92' 
INCLUDED_SECTIONS       = ['new_devices', 'down_devices', 'events']   
DAYS_TO_KEEP_EVENTS     = 90 
REPORT_DASHBOARD_URL    = 'http://pi.alert/' 

# -------------------------------------------
# Misc
# -------------------------------------------

# API     
API_CUSTOM_SQL  = 'SELECT * FROM Devices WHERE dev_PresentLastScan = 0'
