""" CONSTANTS for Pi.Alert """

#===============================================================================
# PATHS
#===============================================================================
pialertPath = '/home/pi/pialert'
#pialertPath ='/home/roland/repos/Pi.Alert'

confPath = "/config/pialert.conf"
dbPath = '/db/pialert.db'


pluginsPath  = pialertPath + '/front/plugins'
logPath      = pialertPath + '/front/log'
apiPath      = pialertPath + '/front/api/'
fullConfPath = pialertPath + confPath
fullDbPath   = pialertPath + dbPath
fullPholusPath = pialertPath+'/pholus/pholus3.py'


vendorsDB              = '/usr/share/arp-scan/ieee-oui.txt'




#===============================================================================
# SQL queries
#===============================================================================
sql_devices_all = """select dev_MAC, dev_Name, dev_DeviceType, dev_Vendor, dev_Group, 
                     dev_FirstConnection, dev_LastConnection, dev_LastIP, dev_StaticIP, 
                     dev_PresentLastScan, dev_LastNotification, dev_NewDevice, 
                     dev_Network_Node_MAC_ADDR, dev_Network_Node_port,  
                     dev_Icon from Devices"""
sql_devices_stats =  """SELECT Online_Devices as online, Down_Devices as down, All_Devices as 'all', Archived_Devices as archived, 
                        (select count(*) from Devices a where dev_NewDevice = 1 ) as new, 
                        (select count(*) from Devices a where dev_Name = '(unknown)' or dev_Name = '(name not found)' ) as unknown 
                        from Online_History order by Scan_Date desc limit 1"""
sql_nmap_scan_all = "SELECT  * FROM Nmap_Scan"
sql_pholus_scan_all = "SELECT  * FROM Pholus_Scan"
sql_events_pending_alert = "SELECT  * FROM Events where eve_PendingAlertEmail is not 0"
sql_settings = "SELECT  * FROM Settings"
sql_plugins_objects = "SELECT  * FROM Plugins_Objects"
sql_language_strings = "SELECT  * FROM Plugins_Language_Strings"
sql_plugins_events = "SELECT  * FROM Plugins_Events"
sql_plugins_history = "SELECT  * FROM Plugins_History ORDER BY 'Index' DESC"
sql_new_devices = """SELECT * FROM ( 
                        SELECT eve_IP as dev_LastIP, eve_MAC as dev_MAC 
                        FROM Events_Devices
                        WHERE eve_PendingAlertEmail = 1
                        AND eve_EventType = 'New Device'
                        ORDER BY eve_DateTime ) t1
                        LEFT JOIN 
                        ( SELECT dev_Name, dev_MAC as dev_MAC_t2 FROM Devices) t2 
                        ON t1.dev_MAC = t2.dev_MAC_t2"""