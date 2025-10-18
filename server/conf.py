""" config related functions for NetAlertX """

# TODO: Create and manage this as part of an app_state class object
#===============================================================================

# These are global variables, not config items and should not exist !
mySettings = []
mySettingsSQLsafe = []
cycle = 1
userSubnets = []
mySchedules = [] # bad solution for global - TO-DO
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
UI_LANG         = 'English (en_us)' 
UI_PRESENCE       = ['online', 'offline', 'archived']  
UI_MY_DEVICES     = ['online', 'offline', 'archived', 'new', 'down']  
UI_NOT_RANDOM_MAC = []
DAYS_TO_KEEP_EVENTS     = 90 
REPORT_DASHBOARD_URL    = 'http://netalertx/' 

# -------------------------------------------
# Misc
# -------------------------------------------

# API     
API_CUSTOM_SQL  = 'SELECT * FROM Devices WHERE devPresentLastScan = 0'
