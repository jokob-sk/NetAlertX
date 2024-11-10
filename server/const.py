""" CONSTANTS for NetAlertX """

#===============================================================================
# PATHS
#===============================================================================
applicationPath = '/app'
dbFileName      = 'app.db'
confFileName    = 'app.conf'
confPath        = "/config/" + confFileName

dbPath          = '/db/' + dbFileName


pluginsPath         = applicationPath + '/front/plugins'
logPath             = applicationPath + '/front/log'
apiPath             = applicationPath + '/front/api/'
reportTemplatesPath = applicationPath + '/front/report_templates/'
fullConfFolder      = applicationPath + '/config'
fullConfPath        = applicationPath + confPath
fullDbPath          = applicationPath + dbPath
vendorsPath         = '/usr/share/arp-scan/ieee-oui.txt'
vendorsPathNewest   = '/usr/share/arp-scan/ieee-oui_all_filtered.txt'

       


#===============================================================================
# SQL queries
#===============================================================================
sql_devices_all = """select rowid, * from Devices"""
sql_appevents = """select * from AppEvents"""
sql_devices_stats =  """SELECT Online_Devices as online, Down_Devices as down, All_Devices as 'all', Archived_Devices as archived, 
                        (select count(*) from Devices a where devIsNew = 1 ) as new, 
                        (select count(*) from Devices a where devName = '(unknown)' or devName = '(name not found)' ) as unknown 
                        from Online_History order by Scan_Date desc limit 1"""
sql_events_pending_alert = "SELECT  * FROM Events where eve_PendingAlertEmail is not 0"
sql_settings = "SELECT  * FROM Settings"
sql_plugins_objects = "SELECT  * FROM Plugins_Objects"
sql_language_strings = "SELECT  * FROM Plugins_Language_Strings"
sql_notifications_all = "SELECT  * FROM Notifications"
sql_online_history = "SELECT  * FROM Online_History"
sql_plugins_events = "SELECT  * FROM Plugins_Events"
sql_plugins_history = "SELECT  * FROM Plugins_History ORDER BY DateTimeChanged DESC"
sql_new_devices = """SELECT * FROM ( 
                        SELECT eve_IP as devLastIP, eve_MAC as devMac 
                        FROM Events_Devices
                        WHERE eve_PendingAlertEmail = 1
                        AND eve_EventType = 'New Device'
                        ORDER BY eve_DateTime ) t1
                        LEFT JOIN 
                        ( SELECT devName, devMac as devMac_t2 FROM Devices) t2 
                        ON t1.devMac = t2.devMac_t2"""


sql_generateGuid = '''
                lower(
                    hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || '4' || 
                    substr(hex( randomblob(2)), 2) || '-' || 
                    substr('AB89', 1 + (abs(random()) % 4) , 1)  ||
                    substr(hex(randomblob(2)), 2) || '-' || 
                    hex(randomblob(6))
                )
            '''