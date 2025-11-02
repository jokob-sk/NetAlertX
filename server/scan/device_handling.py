import sys
import subprocess
import conf
import os
import re

# Register NetAlertX directories
INSTALL_PATH="/app"
sys.path.extend([f"{INSTALL_PATH}/server"])

from helper import timeNowTZ, get_setting_value, check_IP_format
from logger import mylog
from const import vendorsPath, vendorsPathNewest, sql_generateGuid
from models.device_instance import DeviceInstance
from scan.name_resolution import NameResolver
from scan.device_heuristics import guess_icon, guess_type
from db.db_helper import sanitize_SQL_input, list_to_where

#-------------------------------------------------------------------------------
# Removing devices from the CurrentScan DB table which the user chose to ignore by MAC or IP
def exclude_ignored_devices(db):
    sql = db.sql  # Database interface for executing queries

    mac_condition = list_to_where('OR', 'cur_MAC', 'LIKE', get_setting_value('NEWDEV_ignored_MACs'))
    ip_condition = list_to_where('OR', 'cur_IP', 'LIKE', get_setting_value('NEWDEV_ignored_IPs'))

    # Only delete if either the MAC or IP matches an ignored condition
    conditions = []
    if mac_condition:
        conditions.append(mac_condition)
    if ip_condition:
        conditions.append(ip_condition)

    # Join conditions and prepare the query
    conditions_str = " OR ".join(conditions)
    if conditions_str:
        query = f"""DELETE FROM CurrentScan WHERE 
                        1=1
                        AND (
                            {conditions_str}
                        )
                """
    else:
        query = "DELETE FROM CurrentScan WHERE 1=1 AND 1=0"  # No valid conditions, prevent deletion

    mylog('debug', f'[New Devices] Excluding Ignored Devices Query: {query}')

    sql.execute(query)
    

#-------------------------------------------------------------------------------
def update_devices_data_from_scan (db):
    sql = db.sql #TO-DO    
    startTime = timeNowTZ().strftime('%Y-%m-%d %H:%M:%S')

    # Update Last Connection
    mylog('debug', '[Update Devices] 1 Last Connection')
    sql.execute(f"""UPDATE Devices SET devLastConnection = '{startTime}',
                        devPresentLastScan = 1
                    WHERE EXISTS (SELECT 1 FROM CurrentScan 
                                  WHERE devMac = cur_MAC) """)

    # Clean no active devices
    mylog('debug', '[Update Devices] 2 Clean no active devices')
    sql.execute("""UPDATE Devices SET devPresentLastScan = 0
                    WHERE NOT EXISTS (SELECT 1 FROM CurrentScan 
                                      WHERE devMac = cur_MAC) """)

    # Update IP 
    mylog('debug', '[Update Devices] - cur_IP -> devLastIP (always updated)')
    sql.execute("""UPDATE Devices
            SET devLastIP = (
                SELECT cur_IP
                FROM CurrentScan
                WHERE devMac = cur_MAC
                AND cur_IP IS NOT NULL
                AND cur_IP NOT IN ('', 'null', '(unknown)', '(Unknown)')
                ORDER BY cur_DateTime DESC
                LIMIT 1
            )
            WHERE EXISTS (
                SELECT 1
                FROM CurrentScan
                WHERE devMac = cur_MAC
                AND cur_IP IS NOT NULL
                AND cur_IP NOT IN ('', 'null', '(unknown)', '(Unknown)')
            )""")


    # Update only devices with empty, NULL or (u(U)nknown) vendors
    mylog('debug', '[Update Devices] - cur_Vendor -> (if empty) devVendor')
    sql.execute("""UPDATE Devices
                    SET devVendor = (
                        SELECT cur_Vendor
                        FROM CurrentScan
                        WHERE Devices.devMac = CurrentScan.cur_MAC
                    )
                    WHERE 
                        (devVendor IS NULL OR devVendor IN ("", "null", "(unknown)", "(Unknown)"))
                        AND EXISTS (
                            SELECT 1
                            FROM CurrentScan
                            WHERE Devices.devMac = CurrentScan.cur_MAC
                        )""")

    # Update only devices with empty or NULL devParentPort 
    mylog('debug', '[Update Devices] - (if not empty) cur_Port -> devParentPort')
    sql.execute("""UPDATE Devices
                    SET devParentPort = (
                    SELECT cur_Port
                    FROM CurrentScan        
                    WHERE Devices.devMac = CurrentScan.cur_MAC          
                )
                WHERE 
                    (devParentPort IS NULL OR devParentPort IN ("", "null", "(unknown)", "(Unknown)"))
                    AND    
                EXISTS (
                    SELECT 1
                    FROM CurrentScan
                    WHERE Devices.devMac = CurrentScan.cur_MAC
                      AND CurrentScan.cur_Port IS NOT NULL AND CurrentScan.cur_Port NOT IN ("", "null")
                )""")

    # Update only devices with empty or NULL devParentMAC 
    mylog('debug', '[Update Devices] - (if not empty) cur_NetworkNodeMAC -> devParentMAC')
    sql.execute("""UPDATE Devices
                    SET devParentMAC = (
                        SELECT cur_NetworkNodeMAC
                        FROM CurrentScan
                        WHERE Devices.devMac = CurrentScan.cur_MAC
                    )
                    WHERE 
                        (devParentMAC IS NULL OR devParentMAC IN ("", "null", "(unknown)", "(Unknown)"))
                        AND                
                        EXISTS (
                            SELECT 1
                            FROM CurrentScan
                            WHERE Devices.devMac = CurrentScan.cur_MAC
                                AND CurrentScan.cur_NetworkNodeMAC IS NOT NULL AND CurrentScan.cur_NetworkNodeMAC NOT IN ("", "null")
                        )
                """)


    # Update only devices with empty or NULL devSite 
    mylog('debug', '[Update Devices] - (if not empty) cur_NetworkSite -> (if empty) devSite')
    sql.execute("""UPDATE Devices
                    SET devSite = (
                        SELECT cur_NetworkSite
                        FROM CurrentScan
                        WHERE Devices.devMac = CurrentScan.cur_MAC
                    )
                    WHERE 
                        (devSite IS NULL OR devSite IN ("", "null"))
                        AND EXISTS (
                            SELECT 1
                            FROM CurrentScan
                            WHERE Devices.devMac = CurrentScan.cur_MAC
                                AND CurrentScan.cur_NetworkSite IS NOT NULL AND CurrentScan.cur_NetworkSite NOT IN ("", "null")
                )""")

    # Update only devices with empty or NULL devSSID 
    mylog('debug', '[Update Devices] - (if not empty) cur_SSID -> (if empty) devSSID')
    sql.execute("""UPDATE Devices
                    SET devSSID = (
                        SELECT cur_SSID
                        FROM CurrentScan
                        WHERE Devices.devMac = CurrentScan.cur_MAC
                    )
                    WHERE 
                        (devSSID IS NULL OR devSSID IN ("", "null"))
                        AND EXISTS (
                            SELECT 1
                            FROM CurrentScan
                            WHERE Devices.devMac = CurrentScan.cur_MAC
                                AND CurrentScan.cur_SSID IS NOT NULL AND CurrentScan.cur_SSID NOT IN ("", "null")
                        )""")

    # Update only devices with empty or NULL devType
    mylog('debug', '[Update Devices] - (if not empty) cur_Type -> (if empty) devType')
    sql.execute("""UPDATE Devices
                    SET devType = (
                        SELECT cur_Type
                        FROM CurrentScan
                        WHERE Devices.devMac = CurrentScan.cur_MAC
                    )
                    WHERE 
                        (devType IS NULL OR devType IN ("", "null"))
                        AND EXISTS (
                            SELECT 1
                            FROM CurrentScan
                            WHERE Devices.devMac = CurrentScan.cur_MAC
                                AND CurrentScan.cur_Type IS NOT NULL AND CurrentScan.cur_Type NOT IN ("", "null")
                        )""")

    # Update (unknown) or (name not found) Names if available
    mylog('debug','[Update Devices] - (if not empty) cur_Name -> (if empty) devName')
    sql.execute ("""    UPDATE Devices
                        SET devName = COALESCE((
                            SELECT cur_Name 
                            FROM CurrentScan
                            WHERE cur_MAC = devMac
                            AND cur_Name IS NOT NULL
                            AND cur_Name <> 'null'
                            AND cur_Name <> ''
                        ), devName)
                        WHERE (devName IN ('(unknown)', '(name not found)', '') 
                            OR devName IS NULL)
                        AND EXISTS (
                            SELECT 1 
                            FROM CurrentScan
                            WHERE cur_MAC = devMac
                            AND cur_Name IS NOT NULL
                            AND cur_Name <> 'null'
                            AND cur_Name <> ''
                        ) """)

    # Update VENDORS
    recordsToUpdate = []
    query = """SELECT * FROM Devices
               WHERE devVendor IS NULL OR devVendor IN ("", "null", "(unknown)", "(Unknown)")
            """

    for device in sql.execute (query) :
        vendor = query_MAC_vendor (device['devMac'])
        if vendor != -1 and vendor != -2 :
            recordsToUpdate.append ([vendor, device['devMac']])

    if len(recordsToUpdate) > 0: 
        sql.executemany ("UPDATE Devices SET devVendor = ? WHERE devMac = ? ", recordsToUpdate )

    # Update devPresentLastScan based on NICs presence
    update_devPresentLastScan_based_on_nics(db)
    
    # Guess ICONS
    recordsToUpdate = []

    default_icon = get_setting_value('NEWDEV_devIcon')

    if get_setting_value('NEWDEV_replace_preset_icon'):
        query = f"""SELECT * FROM Devices
                    WHERE devIcon in ('', 'null', '{default_icon}')
                        OR devIcon IS NULL"""
    else:
        query = """SELECT * FROM Devices
                    WHERE devIcon in ('', 'null')
                        OR devIcon IS NULL"""
            
    for device in sql.execute (query) :
        # Conditional logic for devIcon guessing       
        devIcon = guess_icon(device['devVendor'], device['devMac'], device['devLastIP'], device['devName'], default_icon)

        recordsToUpdate.append ([devIcon, device['devMac']])


    mylog('debug',f'[Update Devices] recordsToUpdate: {recordsToUpdate}')
    
    if len(recordsToUpdate) > 0:        
        sql.executemany ("UPDATE Devices SET devIcon = ? WHERE devMac = ? ", recordsToUpdate )

    # Guess Type
    recordsToUpdate = []
    query = """SELECT * FROM Devices
                    WHERE devType in ('', 'null')
                OR devType IS NULL"""
    default_type = get_setting_value('NEWDEV_devType')
    
    for device in sql.execute (query) :
        # Conditional logic for devIcon guessing        
        devType = guess_type(device['devVendor'], device['devMac'], device['devLastIP'], device['devName'], default_type)

        recordsToUpdate.append ([devType, device['devMac']])
    
    if len(recordsToUpdate) > 0:        
        sql.executemany ("UPDATE Devices SET devType = ? WHERE devMac = ? ", recordsToUpdate )
    
    
    mylog('debug','[Update Devices] Update devices end')

#-------------------------------------------------------------------------------
def save_scanned_devices (db):
    sql = db.sql #TO-DO


    # Add Local MAC of default local interface
    local_mac_cmd = ["/sbin/ifconfig `ip -o route get 1 | sed 's/^.*dev \\([^ ]*\\).*$/\\1/;q'` | grep ether | awk '{print $2}'"]
    local_mac = subprocess.Popen (local_mac_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0].decode().strip()

    local_ip_cmd = ["ip -o route get 1 | sed 's/^.*src \\([^ ]*\\).*$/\\1/;q'"]
    local_ip = subprocess.Popen (local_ip_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0].decode().strip()

    mylog('debug', ['[Save Devices] Saving this IP into the CurrentScan table:', local_ip])

    if check_IP_format(local_ip) == '':
        local_ip = '0.0.0.0'

    # Proceed if variable contains valid MAC
    if check_mac_or_internet(local_mac):
        sql.execute (f"""INSERT OR IGNORE INTO CurrentScan (cur_MAC, cur_IP, cur_Vendor, cur_ScanMethod) VALUES ( '{local_mac}', '{local_ip}', Null, 'local_MAC') """)

#-------------------------------------------------------------------------------
def print_scan_stats(db):
    sql = db.sql # TO-DO

    query = """
    SELECT
        (SELECT COUNT(*) FROM CurrentScan) AS devices_detected,
        (SELECT COUNT(*) FROM CurrentScan WHERE NOT EXISTS (SELECT 1 FROM Devices WHERE devMac = cur_MAC)) AS new_devices,
        (SELECT COUNT(*) FROM Devices WHERE devAlertDown != 0 AND NOT EXISTS (SELECT 1 FROM CurrentScan WHERE devMac = cur_MAC)) AS down_alerts,
        (SELECT COUNT(*) FROM Devices WHERE devAlertDown != 0 AND devPresentLastScan = 1 AND NOT EXISTS (SELECT 1 FROM CurrentScan WHERE devMac = cur_MAC)) AS new_down_alerts,
        (SELECT COUNT(*) FROM Devices WHERE devPresentLastScan = 0) AS new_connections,
        (SELECT COUNT(*) FROM Devices WHERE devPresentLastScan = 1 AND NOT EXISTS (SELECT 1 FROM CurrentScan WHERE devMac = cur_MAC)) AS disconnections,
        (SELECT COUNT(*) FROM Devices, CurrentScan WHERE devMac = cur_MAC AND devLastIP <> cur_IP) AS ip_changes,
        cur_ScanMethod,
        COUNT(*) AS scan_method_count
    FROM CurrentScan
    GROUP BY cur_ScanMethod
    """

    sql.execute(query)
    stats = sql.fetchall()

    mylog('verbose', f'[Scan Stats] Devices Detected.......: {stats[0]["devices_detected"]}')
    mylog('verbose', f'[Scan Stats] New Devices............: {stats[0]["new_devices"]}')
    mylog('verbose', f'[Scan Stats] Down Alerts............: {stats[0]["down_alerts"]}')
    mylog('verbose', f'[Scan Stats] New Down Alerts........: {stats[0]["new_down_alerts"]}')
    mylog('verbose', f'[Scan Stats] New Connections........: {stats[0]["new_connections"]}')
    mylog('verbose', f'[Scan Stats] Disconnections.........: {stats[0]["disconnections"]}')
    mylog('verbose', f'[Scan Stats] IP Changes.............: {stats[0]["ip_changes"]}')

    # if str(stats[0]["new_devices"]) != '0':
    mylog('trace', f'   ================ DEVICES table content  ================')
    sql.execute('select * from Devices')
    rows = sql.fetchall()
    for row in rows:
        row_dict = dict(row)
        mylog('trace', f'    {row_dict}')
    
    mylog('trace', f'   ================ CurrentScan table content  ================')
    sql.execute('select * from CurrentScan')
    rows = sql.fetchall()
    for row in rows:
        row_dict = dict(row)
        mylog('trace', f'    {row_dict}')
    
    mylog('trace', f'   ================ Events table content where eve_PendingAlertEmail = 1  ================')
    sql.execute('select * from Events where eve_PendingAlertEmail = 1')
    rows = sql.fetchall()
    for row in rows:
        row_dict = dict(row)
        mylog('trace', f'    {row_dict}')

    mylog('trace', f'   ================ Events table COUNT  ================')
    sql.execute('select count(*) from Events')
    rows = sql.fetchall()
    for row in rows:
        row_dict = dict(row)
        mylog('trace', f'    {row_dict}')
        

    mylog('verbose', '[Scan Stats] Scan Method Statistics:')
    for row in stats:
        if row["cur_ScanMethod"] is not None:
            mylog('verbose', f'    {row["cur_ScanMethod"]}: {row["scan_method_count"]}')


#-------------------------------------------------------------------------------
def create_new_devices (db):
    sql = db.sql # TO-DO
    startTime = timeNowTZ()

    # Insert events for new devices from CurrentScan (not yet in Devices)


    mylog('debug', '[New Devices] Insert "New Device" Events')
    query_new_device_events = f"""
    INSERT INTO Events (
        eve_MAC, eve_IP, eve_DateTime,
        eve_EventType, eve_AdditionalInfo,
        eve_PendingAlertEmail
    )
    SELECT cur_MAC, cur_IP, '{startTime}', 'New Device', cur_Vendor, 1
    FROM CurrentScan
    WHERE NOT EXISTS (
        SELECT 1 FROM Devices
        WHERE devMac = cur_MAC
    )
    """
    
    # mylog('debug',f'[New Devices] Log Events Query: {query_new_device_events}')
    
    sql.execute(query_new_device_events)

    mylog('debug',f'[New Devices] Insert Connection into session table')

    sql.execute (f"""INSERT INTO Sessions (
                        ses_MAC, ses_IP, ses_EventTypeConnection, ses_DateTimeConnection,
                        ses_EventTypeDisconnection, ses_DateTimeDisconnection,
                        ses_StillConnected, ses_AdditionalInfo
                    )
                    SELECT cur_MAC, cur_IP, 'Connected', '{startTime}', NULL, NULL, 1, cur_Vendor
                    FROM CurrentScan
                    WHERE EXISTS (
                        SELECT 1 FROM Devices
                        WHERE devMac = cur_MAC
                    )
                    AND NOT EXISTS (
                        SELECT 1 FROM Sessions
                        WHERE ses_MAC = cur_MAC AND ses_StillConnected = 1
                    )
                    """)
                    
    # Create new devices from CurrentScan
    mylog('debug','[New Devices] 2 Create devices')

    # default New Device values preparation
    newDevColumns =  """devAlertEvents, 
                        devAlertDown, 
                        devPresentLastScan, 
                        devIsArchived, 
                        devIsNew, 
                        devSkipRepeated, 
                        devScan, 
                        devOwner, 
                        devFavorite, 
                        devGroup, 
                        devComments, 
                        devLogEvents, 
                        devLocation,
                        devCustomProps,
                        devParentRelType,
                        devReqNicsOnline
                        """

    newDevDefaults = f"""{get_setting_value('NEWDEV_devAlertEvents')}, 
                        {get_setting_value('NEWDEV_devAlertDown')}, 
                        {get_setting_value('NEWDEV_devPresentLastScan')}, 
                        {get_setting_value('NEWDEV_devIsArchived')}, 
                        {get_setting_value('NEWDEV_devIsNew')}, 
                        {get_setting_value('NEWDEV_devSkipRepeated')}, 
                        {get_setting_value('NEWDEV_devScan')}, 
                        '{sanitize_SQL_input(get_setting_value('NEWDEV_devOwner'))}', 
                        {get_setting_value('NEWDEV_devFavorite')}, 
                        '{sanitize_SQL_input(get_setting_value('NEWDEV_devGroup'))}', 
                        '{sanitize_SQL_input(get_setting_value('NEWDEV_devComments'))}', 
                        {get_setting_value('NEWDEV_devLogEvents')}, 
                        '{sanitize_SQL_input(get_setting_value('NEWDEV_devLocation'))}',
                        '{sanitize_SQL_input(get_setting_value('NEWDEV_devCustomProps'))}',
                        '{sanitize_SQL_input(get_setting_value('NEWDEV_devParentRelType'))}',
                        {sanitize_SQL_input(get_setting_value('NEWDEV_devReqNicsOnline'))}
                        """

    # Fetch data from CurrentScan skipping ignored devices by IP and MAC
    query = f"""SELECT cur_MAC, cur_Name, cur_Vendor, cur_ScanMethod, cur_IP, cur_SyncHubNodeName, cur_NetworkNodeMAC, cur_PORT, cur_NetworkSite, cur_SSID, cur_Type 
                FROM CurrentScan """ 

    
    mylog('debug',f'[New Devices] Collecting New Devices Query: {query}')
    current_scan_data = sql.execute(query).fetchall()

    for row in current_scan_data:
        cur_MAC, cur_Name, cur_Vendor, cur_ScanMethod, cur_IP, cur_SyncHubNodeName, cur_NetworkNodeMAC, cur_PORT, cur_NetworkSite, cur_SSID, cur_Type = row

        # Handle NoneType
        cur_Name = str(cur_Name).strip() if cur_Name else '(unknown)'
        cur_Type = str(cur_Type).strip() if cur_Type else get_setting_value("NEWDEV_devType")
        cur_NetworkNodeMAC = cur_NetworkNodeMAC.strip() if cur_NetworkNodeMAC else ''
        cur_NetworkNodeMAC = cur_NetworkNodeMAC if cur_NetworkNodeMAC and cur_MAC != "Internet" else (get_setting_value("NEWDEV_devParentMAC") if cur_MAC != "Internet" else "null")
        cur_SyncHubNodeName = cur_SyncHubNodeName if cur_SyncHubNodeName and cur_SyncHubNodeName != "null" else (get_setting_value("SYNC_node_name"))

        # Preparing the individual insert statement
        sqlQuery = f"""INSERT OR IGNORE INTO Devices 
                        (
                            devMac, 
                            devName, 
                            devVendor,
                            devLastIP, 
                            devFirstConnection, 
                            devLastConnection, 
                            devSyncHubNode, 
                            devGUID,
                            devParentMAC, 
                            devParentPort,
                            devSite, 
                            devSSID,
                            devType,                          
                            devSourcePlugin,                          
                            {newDevColumns}
                        )
                        VALUES 
                        (
                            '{sanitize_SQL_input(cur_MAC)}', 
                            '{sanitize_SQL_input(cur_Name)}',
                            '{sanitize_SQL_input(cur_Vendor)}', 
                            '{sanitize_SQL_input(cur_IP)}', 
                            ?, 
                            ?, 
                            '{sanitize_SQL_input(cur_SyncHubNodeName)}', 
                            {sql_generateGuid},
                            '{sanitize_SQL_input(cur_NetworkNodeMAC)}',
                            '{sanitize_SQL_input(cur_PORT)}',
                            '{sanitize_SQL_input(cur_NetworkSite)}', 
                            '{sanitize_SQL_input(cur_SSID)}',
                            '{sanitize_SQL_input(cur_Type)}', 
                            '{sanitize_SQL_input(cur_ScanMethod)}', 
                            {newDevDefaults}
                        )"""

        mylog('trace', f'[New Devices] Create device SQL: {sqlQuery}')

        sql.execute(sqlQuery, (startTime, startTime))

    
    mylog('debug','[New Devices] New Devices end')
    db.commitDB()



#-------------------------------------------------------------------------------
def update_devices_names(pm):
    sql = pm.db.sql
    resolver = NameResolver(pm.db)
    device_handler = DeviceInstance(pm.db)

    # --- Short-circuit if no plugin that resolves names changed ---
    name_plugins = ["DIGSCAN", "NSLOOKUP", "NBTSCAN", "AVAHISCAN"]
    
    # Get last check timestamp from plugin manager
    last_checked = pm.name_plugins_checked

    # Determine the latest 'lastChanged' timestamp among name plugins
    latest_change = max(
        [pm.plugin_states.get(p, {}).get("lastChanged") for p in name_plugins if pm.plugin_states.get(p)],
        default=None
    )

    # Convert to comparable datetime if needed
    from dateutil import parser
    latest_change_dt = parser.parse(latest_change) if latest_change else None

    # Skip if nothing changed since last check
    if last_checked and latest_change_dt and latest_change_dt <= last_checked:
        mylog('debug', '[Update Device Name] No relevant plugin changes since last check, skipping.')
        return

    nameNotFound = "(name not found)"

    # Define resolution strategies in priority order
    strategies = [
        (resolver.resolve_dig, 'DIGSCAN'),
        (resolver.resolve_mdns, 'AVAHISCAN'),
        (resolver.resolve_nslookup, 'NSLOOKUP'),
        (resolver.resolve_nbtlookup, 'NBTSCAN')
    ]

    def resolve_devices(devices, resolve_both_name_and_fqdn=True):
        """
        Attempts to resolve device names and/or FQDNs using available strategies.
        
        Parameters:
            devices (list): List of devices to resolve.
            resolve_both_name_and_fqdn (bool): If True, resolves both name and FQDN.
                                               If False, resolves only FQDN.
        
        Returns:
            recordsToUpdate (list): List of [newName, newFQDN, devMac] or [newFQDN, devMac] for DB update.
            recordsNotFound (list): List of [nameNotFound, devMac] for DB update.
            foundStats (dict): Number of successes per strategy.
            notFound (int): Number of devices not resolved.
        """
        recordsToUpdate = []
        recordsNotFound = []
        foundStats = {label: 0 for _, label in strategies}
        notFound = 0

        for device in devices:
            newName = nameNotFound
            newFQDN = ''

            # Attempt each resolution strategy in order
            for resolve_fn, label in strategies:
                resolved = resolve_fn(device['devMac'], device['devLastIP'])

                # Only use name if resolving both name and FQDN
                newName = resolved.cleaned if resolve_both_name_and_fqdn else None
                newFQDN = resolved.raw

                # If a valid result is found, record it and stop further attempts
                if newFQDN not in [nameNotFound, '', 'localhost.'] and ' communications error to ' not in newFQDN:
                    foundStats[label] += 1

                    if resolve_both_name_and_fqdn:
                        recordsToUpdate.append([newName, newFQDN, device['devMac']])
                    else:
                        recordsToUpdate.append([newFQDN, device['devMac']])
                    break

            # If no name was resolved, queue device for "(name not found)" update
            if resolve_both_name_and_fqdn and newName == nameNotFound:
                notFound += 1
                if device['devName'] != nameNotFound:
                    recordsNotFound.append([nameNotFound, device['devMac']])

        return recordsToUpdate, recordsNotFound, foundStats, notFound

    # --- Step 1: Update device names for unknown devices ---
    unknownDevices = device_handler.getUnknown()
    if unknownDevices:
        mylog('verbose', f'[Update Device Name] Trying to resolve devices without name. Unknown devices count: {len(unknownDevices)}')

        # Try resolving both name and FQDN
        recordsToUpdate, recordsNotFound, foundStats, notFound = resolve_devices(unknownDevices)

        # Log summary
        mylog('verbose', f"[Update Device Name] Names Found (DIGSCAN/AVAHISCAN/NSLOOKUP/NBTSCAN): {len(recordsToUpdate)} ({foundStats['DIGSCAN']}/{foundStats['AVAHISCAN']}/{foundStats['NSLOOKUP']}/{foundStats['NBTSCAN']})")
        mylog('verbose', f'[Update Device Name] Names Not Found         : {notFound}')

        # Apply updates to database
        sql.executemany("UPDATE Devices SET devName = ? WHERE devMac = ?", recordsNotFound)
        sql.executemany("UPDATE Devices SET devName = ?, devFQDN = ? WHERE devMac = ?", recordsToUpdate)

    # --- Step 2: Optionally refresh FQDN for all devices ---
    if get_setting_value("REFRESH_FQDN"):
        allDevices = device_handler.getAll()
        if allDevices:
            mylog('verbose', f'[Update FQDN] Trying to resolve FQDN. Devices count: {len(allDevices)}')

            # Try resolving only FQDN
            recordsToUpdate, _, foundStats, notFound = resolve_devices(allDevices, resolve_both_name_and_fqdn=False)

            # Log summary
            mylog('verbose', f"[Update FQDN] Names Found (DIGSCAN/AVAHISCAN/NSLOOKUP/NBTSCAN): {len(recordsToUpdate)} ({foundStats['DIGSCAN']}/{foundStats['AVAHISCAN']}/{foundStats['NSLOOKUP']}/{foundStats['NBTSCAN']})")
            mylog('verbose', f'[Update FQDN] Names Not Found         : {notFound}')

            # Apply FQDN-only updates
            sql.executemany("UPDATE Devices SET devFQDN = ? WHERE devMac = ?", recordsToUpdate)

    # Commit all database changes
    pm.db.commitDB()

    # --- Step 3: Log last checked time ---
    # After resolving names, update last checked
    pm.name_plugins_checked = timeNowTZ()

#-------------------------------------------------------------------------------
# Updates devPresentLastScan for parent devices based on the presence of their NICs
def update_devPresentLastScan_based_on_nics(db):
    """
    Updates devPresentLastScan in the Devices table for parent devices
    based on the presence of their NICs and the devReqNicsOnline setting.

    Args:
        db: A database object with `.execute()` and `.fetchall()` methods.
    """

    sql = db.sql

    # Step 1: Load all devices from the DB
    devices = sql.execute("SELECT * FROM Devices").fetchall()

    # Convert rows to dicts (assumes sql.row_factory = sqlite3.Row or similar)
    devices = [dict(row) for row in devices]

    # Build MAC -> NICs map
    mac_to_nics = {}
    for device in devices:
        if device.get("devParentRelType") == "nic":
            parent_mac = device.get("devParentMAC")
            if parent_mac:
                mac_to_nics.setdefault(parent_mac, []).append(device)

    # Step 2: For each non-NIC device, determine new devPresentLastScan
    updates = []
    for device in devices:
        if device.get("devParentRelType") == "nic":
            continue  # skip NICs

        mac = device.get("devMac")
        if not mac:
            continue

        req_all = str(device.get("devReqNicsOnline")) == "1"
        nics = mac_to_nics.get(mac, [])

        original = device.get("devPresentLastScan", 0)
        new_present = original

        if nics:
            nic_statuses = [nic.get("devPresentLastScan") == 1 for nic in nics]
            if req_all:
                new_present = int(all(nic_statuses))
            else:
                new_present = int(any(nic_statuses))

        # Only add update if changed
        if original != new_present:
            updates.append((new_present, mac))

    # Step 3: Execute batch update
    for present, mac in updates:
        sql.execute(
            "UPDATE Devices SET devPresentLastScan = ? WHERE devMac = ?",
            (present, mac)
        )

    db.commitDB()
    return len(updates)

#-------------------------------------------------------------------------------
# Check if the variable contains a valid MAC address or "Internet"
def check_mac_or_internet(input_str):
    # Regular expression pattern for matching a MAC address
    mac_pattern = r'([0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2})'

    if input_str.lower() == 'internet':
        return True
    elif re.match(mac_pattern, input_str):
        return True
    else:
        return False

#-------------------------------------------------------------------------------
# Lookup unknown vendors on devices
def query_MAC_vendor (pMAC):

    pMACstr = str(pMAC)

    filePath = vendorsPath
    
    if os.path.isfile(vendorsPathNewest):
        filePath = vendorsPathNewest
    
    # Check MAC parameter
    mac = pMACstr.replace (':','').lower()
    if len(pMACstr) != 17 or len(mac) != 12 :
        return -2 # return -2 if ignored MAC

    # Search vendor in HW Vendors DB
    mac_start_string6 = mac[0:6]    
    mac_start_string9 = mac[0:9]    

    try:
        with open(filePath, 'r') as f:
            for line in f:
                line_lower = line.lower()  # Convert line to lowercase for case-insensitive matching
                if line_lower.startswith(mac_start_string6):                 
                    parts = line.split('\t', 1)
                    if len(parts) > 1:
                        vendor = parts[1].strip()
                        mylog('debug', [f"[Vendor Check] Found '{vendor}' for '{pMAC}' in {vendorsPath}"])
                        return vendor
                    else:
                        mylog('debug', [f'[Vendor Check] ⚠ ERROR: Match found, but line could not be processed: "{line_lower}"'])
                        return -1


        return -1  # MAC address not found in the database
    except FileNotFoundError:
        mylog('none', [f"[Vendor Check] ⚠ ERROR: Vendors file {vendorsPath} not found."])
        return -1



