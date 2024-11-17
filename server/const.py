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
sql_devices_all = """
                    SELECT 
                        rowid, 
                        *,
                        CASE 
                            WHEN devIsNew = 1 THEN 'New'
                            WHEN devPresentLastScan = 1 THEN 'On-line'
                            WHEN devPresentLastScan = 0 AND devAlertDown != 0 THEN 'Down'
                            WHEN devIsArchived = 1 THEN 'Archived'
                            WHEN devPresentLastScan = 0 THEN 'Off-line'
                            ELSE 'Unknown status'
                        END AS devStatus
                    FROM Devices
                    """
sql_appevents = """select * from AppEvents"""
# The below query calculates counts of devices in various categories: 
#  (connected/online, offline, down, new, archived), 
#  as well as a combined count for devices that match any status listed in the UI_MY_DEVICES setting
sql_devices_tiles = """
                        WITH Statuses AS (
                            SELECT Value
                            FROM Settings
                            WHERE Code_Name = 'UI_MY_DEVICES'
                        ),
                        MyDevicesFilter AS (
                            SELECT
                                -- Build a dynamic filter for devices matching any status in UI_MY_DEVICES
                                devPresentLastScan, devAlertDown, devIsNew, devIsArchived
                            FROM Devices
                            WHERE
                                (instr((SELECT Value FROM Statuses), 'online') > 0 AND devPresentLastScan = 1) OR
                                (instr((SELECT Value FROM Statuses), 'offline') > 0 AND devPresentLastScan = 0) OR
                                (instr((SELECT Value FROM Statuses), 'down') > 0 AND devPresentLastScan = 0 AND devAlertDown = 1) OR
                                (instr((SELECT Value FROM Statuses), 'new') > 0 AND devIsNew = 1) OR
                                (instr((SELECT Value FROM Statuses), 'archived') > 0 AND devIsArchived = 1)
                        )
                        SELECT
                            -- Counts for each individual status
                            (SELECT COUNT(*) FROM Devices WHERE devPresentLastScan = 1) AS connected,
                            (SELECT COUNT(*) FROM Devices WHERE devPresentLastScan = 0) AS offline,
                            (SELECT COUNT(*) FROM Devices WHERE devPresentLastScan = 0 AND devAlertDown = 1) AS down,
                            (SELECT COUNT(*) FROM Devices WHERE devIsNew = 1) AS new,
                            (SELECT COUNT(*) FROM Devices WHERE devIsArchived = 1) AS archived,
                            -- My Devices count
                            (SELECT COUNT(*) FROM MyDevicesFilter) AS my_devices
                        FROM Statuses; 
                    """
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