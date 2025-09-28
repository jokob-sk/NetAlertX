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
logPath             = applicationPath + '/log'
apiPath             = applicationPath + '/api/'
reportTemplatesPath = applicationPath + '/front/report_templates/'
fullConfFolder      = applicationPath + '/config'
fullConfPath        = applicationPath + confPath
fullDbPath          = applicationPath + dbPath
vendorsPath         = '/usr/share/arp-scan/ieee-oui.txt'
vendorsPathNewest   = '/usr/share/arp-scan/ieee-oui_all_filtered.txt'

default_tz          = 'Europe/Berlin'


#===============================================================================
# SQL queries
#===============================================================================
sql_devices_all = """
                    SELECT 
                        rowid,
                        IFNULL(devMac, '') AS devMac,
                        IFNULL(devName, '') AS devName,
                        IFNULL(devOwner, '') AS devOwner,
                        IFNULL(devType, '') AS devType,
                        IFNULL(devVendor, '') AS devVendor,
                        IFNULL(devFavorite, '') AS devFavorite,
                        IFNULL(devGroup, '') AS devGroup,
                        IFNULL(devComments, '') AS devComments,
                        IFNULL(devFirstConnection, '') AS devFirstConnection,
                        IFNULL(devLastConnection, '') AS devLastConnection,
                        IFNULL(devLastIP, '') AS devLastIP,
                        IFNULL(devStaticIP, '') AS devStaticIP,
                        IFNULL(devScan, '') AS devScan,
                        IFNULL(devLogEvents, '') AS devLogEvents,
                        IFNULL(devAlertEvents, '') AS devAlertEvents,
                        IFNULL(devAlertDown, '') AS devAlertDown,
                        IFNULL(devSkipRepeated, '') AS devSkipRepeated,
                        IFNULL(devLastNotification, '') AS devLastNotification,
                        IFNULL(devPresentLastScan, 0) AS devPresentLastScan,
                        IFNULL(devIsNew, '') AS devIsNew,
                        IFNULL(devLocation, '') AS devLocation,
                        IFNULL(devIsArchived, '') AS devIsArchived,
                        IFNULL(devParentMAC, '') AS devParentMAC,
                        IFNULL(devParentPort, '') AS devParentPort,
                        IFNULL(devIcon, '') AS devIcon,
                        IFNULL(devGUID, '') AS devGUID,
                        IFNULL(devSite, '') AS devSite,
                        IFNULL(devSSID, '') AS devSSID,
                        IFNULL(devSyncHubNode, '') AS devSyncHubNode,
                        IFNULL(devSourcePlugin, '') AS devSourcePlugin,
                        IFNULL(devCustomProps, '') AS devCustomProps,
                        IFNULL(devFQDN, '') AS devFQDN,
                        IFNULL(devParentRelType, '') AS devParentRelType,
                        IFNULL(devReqNicsOnline, '') AS devReqNicsOnline,
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

sql_appevents = """select * from AppEvents order by DateTimeCreated desc"""
# The below query calculates counts of devices in various categories: 
#  (connected/online, offline, down, new, archived), 
#  as well as a combined count for devices that match any status listed in the UI_MY_DEVICES setting
sql_devices_tiles = """
                        WITH Statuses AS (
                            SELECT setValue
                            FROM Settings
                            WHERE setKey = 'UI_MY_DEVICES'
                        ),
                        MyDevicesFilter AS (
                            SELECT
                                -- Build a dynamic filter for devices matching any status in UI_MY_DEVICES
                                devPresentLastScan, devAlertDown, devIsNew, devIsArchived
                            FROM Devices
                            WHERE
                                (instr((SELECT setValue FROM Statuses), 'online') > 0 AND devPresentLastScan = 1) OR
                                (instr((SELECT setValue FROM Statuses), 'offline') > 0 AND devPresentLastScan = 0 AND devIsArchived = 0) OR
                                (instr((SELECT setValue FROM Statuses), 'down') > 0 AND devPresentLastScan = 0 AND devAlertDown = 1) OR
                                (instr((SELECT setValue FROM Statuses), 'new') > 0 AND devIsNew = 1) OR
                                (instr((SELECT setValue FROM Statuses), 'archived') > 0 AND devIsArchived = 1)
                        )
                        SELECT
                            -- Counts for each individual status
                            (SELECT COUNT(*) FROM Devices WHERE devPresentLastScan = 1) AS connected,
                            (SELECT COUNT(*) FROM Devices WHERE devPresentLastScan = 0) AS offline,
                            (SELECT COUNT(*) FROM Devices WHERE devPresentLastScan = 0 AND devAlertDown = 1) AS down,
                            (SELECT COUNT(*) FROM Devices WHERE devIsNew = 1) AS new,
                            (SELECT COUNT(*) FROM Devices WHERE devIsArchived = 1) AS archived,
                            (SELECT COUNT(*) FROM Devices WHERE devFavorite = 1) AS favorites,
                            -- My Devices count
                            (SELECT COUNT(*) FROM MyDevicesFilter) AS my_devices
                        FROM Statuses; 
                    """
sql_devices_filters = """
                    SELECT DISTINCT 'devSite' AS columnName, devSite AS columnValue
                        FROM Devices WHERE devSite NOT IN ('', 'null') AND devSite IS NOT NULL
                    UNION
                    SELECT DISTINCT 'devSourcePlugin' AS columnName, devSourcePlugin AS columnValue
                        FROM Devices WHERE devSourcePlugin NOT IN ('', 'null') AND devSourcePlugin IS NOT NULL
                    UNION
                    SELECT DISTINCT 'devOwner' AS columnName, devOwner AS columnValue
                        FROM Devices WHERE devOwner NOT IN ('', 'null') AND devOwner IS NOT NULL
                    UNION
                    SELECT DISTINCT 'devType' AS columnName, devType AS columnValue
                        FROM Devices WHERE devType NOT IN ('', 'null') AND devType IS NOT NULL
                    UNION
                    SELECT DISTINCT 'devGroup' AS columnName, devGroup AS columnValue
                        FROM Devices WHERE devGroup NOT IN ('', 'null') AND devGroup IS NOT NULL
                    UNION
                    SELECT DISTINCT 'devLocation' AS columnName, devLocation AS columnValue
                        FROM Devices WHERE devLocation NOT IN ('', 'null') AND devLocation IS NOT NULL
                    UNION
                    SELECT DISTINCT 'devVendor' AS columnName, devVendor AS columnValue
                        FROM Devices WHERE devVendor NOT IN ('', 'null') AND devVendor IS NOT NULL
                    UNION
                    SELECT DISTINCT 'devSyncHubNode' AS columnName, devSyncHubNode AS columnValue
                        FROM Devices WHERE devSyncHubNode NOT IN ('', 'null') AND devSyncHubNode IS NOT NULL
                    UNION
                    SELECT DISTINCT 'devSSID' AS columnName, devSSID AS columnValue
                        FROM Devices WHERE devSSID NOT IN ('', 'null') AND devSSID IS NOT NULL
                    ORDER BY columnName;
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