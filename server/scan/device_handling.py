import sys
from typing import Optional, List, Tuple, Dict
import subprocess
import conf
import os
import re

# Register NetAlertX directories
INSTALL_PATH="/app"
sys.path.extend([f"{INSTALL_PATH}/server"])

from helper import timeNowTZ, get_setting, get_setting_value, list_to_where, check_IP_format, sanitize_SQL_input
from logger import mylog
from const import vendorsPath, vendorsPathNewest, sql_generateGuid
from models.device_instance import DeviceInstance
from scan.name_resolution import NameResolver

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

    # Insert events for new devices from CurrentScan
    mylog('debug','[New Devices] New devices - 1 Events')

    query = f"""INSERT INTO Events (eve_MAC, eve_IP, eve_DateTime,
                        eve_EventType, eve_AdditionalInfo,
                        eve_PendingAlertEmail)
                    SELECT cur_MAC, cur_IP, '{startTime}', 'New Device', cur_Vendor, 1
                    FROM CurrentScan
                    WHERE NOT EXISTS (SELECT 1 FROM Devices
                                      WHERE devMac = cur_MAC)
                """ 

    
    mylog('debug',f'[New Devices] Log Events Query: {query}')
    
    sql.execute(query)

    mylog('debug',f'[New Devices] Insert Connection into session table')

    sql.execute (f"""INSERT INTO Sessions (ses_MAC, ses_IP, ses_EventTypeConnection, ses_DateTimeConnection,
                        ses_EventTypeDisconnection, ses_DateTimeDisconnection, ses_StillConnected, ses_AdditionalInfo)
                    SELECT cur_MAC, cur_IP,'Connected','{startTime}', NULL , NULL ,1, cur_Vendor
                    FROM CurrentScan 
                    WHERE NOT EXISTS (SELECT 1 FROM Sessions
                                      WHERE ses_MAC = cur_MAC) 
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
                        devCustomProps"""

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
                        '{sanitize_SQL_input(get_setting_value('NEWDEV_devCustomProps'))}'
                        """

    # Fetch data from CurrentScan skipping ignored devices by IP and MAC
    query = f"""SELECT cur_MAC, cur_Name, cur_Vendor, cur_ScanMethod, cur_IP, cur_SyncHubNodeName, cur_NetworkNodeMAC, cur_PORT, cur_NetworkSite, cur_SSID, cur_Type 
                FROM CurrentScan """ 

    
    mylog('debug',f'[New Devices] Collecting New Devices Query: {query}')
    current_scan_data = sql.execute(query).fetchall()

    for row in current_scan_data:
        cur_MAC, cur_Name, cur_Vendor, cur_ScanMethod, cur_IP, cur_SyncHubNodeName, cur_NetworkNodeMAC, cur_PORT, cur_NetworkSite, cur_SSID, cur_Type = row

        # Handle NoneType
        cur_Name = cur_Name.strip() if cur_Name else '(unknown)'
        cur_Type = cur_Type.strip() if cur_Type else get_setting_value("NEWDEV_devType")
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
def update_devices_data_from_scan (db):
    sql = db.sql #TO-DO    
    startTime = timeNowTZ().strftime('%Y-%m-%d %H:%M:%S')

    # Update Last Connection
    mylog('debug', '[Update Devices] 1 Last Connection')
    sql.execute(f"""UPDATE Devices SET devLastConnection = '{startTime}',
                        devPresentLastScan = 1
                    WHERE devPresentLastScan = 0
                      AND EXISTS (SELECT 1 FROM CurrentScan 
                                  WHERE devMac = cur_MAC) """)

    # Clean no active devices
    mylog('debug', '[Update Devices] 2 Clean no active devices')
    sql.execute("""UPDATE Devices SET devPresentLastScan = 0
                    WHERE NOT EXISTS (SELECT 1 FROM CurrentScan 
                                      WHERE devMac = cur_MAC) """)

    # Update IP 
    mylog('debug', '[Update Devices] - cur_IP -> devLastIP (always updated)')
    sql.execute("""UPDATE Devices
                    SET devLastIP = (SELECT cur_IP FROM CurrentScan
                                      WHERE devMac = cur_MAC)
                    WHERE EXISTS (SELECT 1 FROM CurrentScan
                                  WHERE devMac = cur_MAC) """)

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
def update_devices_names(db):
    sql = db.sql
    resolver = NameResolver(db)
    device_handler = DeviceInstance(db)

    nameNotFound = "(name not found)"

    # Define resolution strategies in priority order
    strategies = [
        (resolver.resolve_dig, 'dig'),
        (resolver.resolve_mdns, 'mdns'),
        (resolver.resolve_nslookup, 'nslookup'),
        (resolver.resolve_nbtlookup, 'nbtlookup')
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
        mylog('verbose', f"[Update Device Name] Names Found (DiG/mDNS/NSLOOKUP/NBTSCAN): {len(recordsToUpdate)} ({foundStats['dig']}/{foundStats['mdns']}/{foundStats['nslookup']}/{foundStats['nbtlookup']})")
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
            mylog('verbose', f"[Update FQDN] Names Found (DiG/mDNS/NSLOOKUP/NBTSCAN): {len(recordsToUpdate)} ({foundStats['dig']}/{foundStats['mdns']}/{foundStats['nslookup']}/{foundStats['nbtlookup']})")
            mylog('verbose', f'[Update FQDN] Names Not Found         : {notFound}')

            # Apply FQDN-only updates
            sql.executemany("UPDATE Devices SET devFQDN = ? WHERE devMac = ?", recordsToUpdate)

    # Commit all database changes
    db.commitDB()




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


#===============================================================================
# Lookup unknown vendors on devices
#===============================================================================

#-------------------------------------------------------------------------------
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


#===============================================================================
# Icons
#===============================================================================
#-------------------------------------------------------------------------------
# Base64 encoded HTML strings for FontAwesome icons, now with an extended icons dictionary for broader device coverage
ICONS = {
    "globe": "PGkgY2xhc3M9ImZhcyBmYS1nbG9iZSI+PC9pPg==",  # Internet or global network
    "phone": "PGkgY2xhc3M9ImZhcyBmYS1tb2JpbGUtYWx0Ij48L2k+",  # Smartphone
    "laptop": "PGkgY2xhc3M9ImZhIGZhLWxhcHRvcCI+PC9pPg==",  # Laptop
    "printer": "PGkgY2xhc3M9ImZhIGZhLXByaW50ZXIiPjwvaT4=",  # Printer
    "router": "PGkgY2xhc3M9ImZhcyBmYS1yYW5kb20iPjwvaT4=",  # Router or network switch
    "tv": "PGkgY2xhc3M9ImZhIGZhLXR2Ij48L2k+",  # Television
    "desktop": "PGkgY2xhc3M9ImZhIGZhLWRlc2t0b3AiPjwvaT4=",  # Desktop PC
    "tablet": "PGkgY2xhc3M9ImZhIGZhLXRhYmxldCI+PC9pPg==",  # Tablet
    "watch": "PGkgY2xhc3M9ImZhcyBmYS1jbG9jayI+PC9pPg==",  # Fallback to clock since smartwatch is nonfree in FontAwesome
    "camera": "PGkgY2xhc3M9ImZhIGZhLWNhbWVyYSI+PC9pPg==",  # Camera or webcam
    "home": "PGkgY2xhc3M9ImZhIGZhLWhvbWUiPjwvaT4=",  # Smart home device
    "apple": "PGkgY2xhc3M9ImZhYiBmYS1hcHBsZSI+PC9pPg==",  # Apple device
    "ethernet": "PGkgY2xhc3M9ImZhcyBmYS1uZXR3b3JrLXdpcmVkIj48L2k+",  # Free alternative for ethernet icon in FontAwesome
    "google": "PGkgY2xhc3M9ImZhYiBmYS1nb29nbGUiPjwvaT4=",  # Google device
    "raspberry": "PGkgY2xhc3M9ImZhYiBmYS1yYXNwYmVycnktcGkiPjwvaT4=",  # Raspberry Pi
    "microchip": "PGkgY2xhc3M9ImZhcyBmYS1taWNyb2NoaXAiPjwvaT4=",  # IoT or embedded device
    "server": "PGkgY2xhc3M9ImZhcyBmYS1zZXJ2ZXIiPjwvaT4=",  # Server
    "gamepad": "PGkgY2xhc3M9ImZhcyBmYS1nYW1lcGFkIj48L2k+",  # Gaming console
    "lightbulb": "PGkgY2xhc3M9ImZhcyBmYS1saWdodGJ1bGIiPjwvaT4=",  # Smart light
    "speaker": "PGkgY2xhc3M9ImZhcyBmYS12b2x1bWUtdXAiPjwvaT4=",  # Free speaker alt icon for smart speakers in FontAwesome
    "lock": "PGkgY2xhc3M9ImZhcyBmYS1sb2NrIj48L2k+",  # Security device
}

# Extended device types for comprehensive classification
DEVICE_TYPES = {
    "Internet": "Internet Gateway",
    "Phone": "Smartphone",
    "Laptop": "Laptop",
    "Printer": "Printer",
    "Router": "Router",
    "TV": "Television",
    "Desktop": "Desktop PC",
    "Tablet": "Tablet",
    "Smartwatch": "Smartwatch",
    "Camera": "Camera",
    "SmartHome": "Smart Home Device",
    "Server": "Server",
    "GamingConsole": "Gaming Console",
    "IoT": "IoT Device",
    "NetworkSwitch": "Network Switch",
    "AccessPoint": "Access Point",
    "SmartLight": "Smart Light",
    "SmartSpeaker": "Smart Speaker",
    "SecurityDevice": "Security Device",
    "Unknown": "Unknown Device",
}

#-------------------------------------------------------------------------------
# Guess device attributes such as type of device and associated device icon
def guess_device_attributes(
    vendor: Optional[str],
    mac: Optional[str],
    ip: Optional[str],
    name: Optional[str],
    default_icon: str,
    default_type: str
    ) -> Tuple[str, str]:
    """
    Guess the appropriate FontAwesome icon and device type based on device attributes.

    Args:
        vendor: Device vendor name.
        mac: Device MAC address.
        ip: Device IP address.
        name: Device name.
        default_icon: Default icon to return if no match is found.
        default_type: Default type to return if no match is found.

    Returns:
        Tuple[str, str]: A tuple containing the guessed icon (Base64-encoded HTML string)
                         and the guessed device type (string).
    """
    mylog('debug', f"[guess_device_attributes] Guessing attributes for (vendor|mac|ip|name): ('{vendor}'|'{mac}'|'{ip}'|'{name}')")
    # Normalize inputs
    vendor = str(vendor).lower().strip() if vendor else "unknown"
    mac = str(mac).upper().strip() if mac else "00:00:00:00:00:00"
    ip = str(ip).strip() if ip else "169.254.0.0"  # APIPA address for unknown IPs per RFC 3927
    name = str(name).lower().strip() if name else "(unknown)"

    # --- Icon Guessing Logic ---
    if mac == "INTERNET":
        icon = ICONS.get("globe", default_icon)
    else:
        # Vendor-based icon guessing
        icon_vendor_patterns = {
            "apple": "apple",
            "samsung|motorola|xiaomi|huawei": "phone",
            "dell|lenovo|asus|acer": "laptop",
            "hp|epson|canon|brother": "printer",
            "cisco|ubiquiti|netgear|tp-link|d-link|mikrotik": "router",
            "lg|samsung electronics|sony|vizio": "tv",
            "raspberry pi": "raspberry",
            "google": "google",
            "espressif|particle": "microchip",
            "intel|amd": "desktop",
            "amazon": "speaker",
            "philips hue|lifx": "lightbulb",
            "aruba|meraki": "ethernet",
            "qnap|synology": "server",
            "nintendo|sony interactive|microsoft": "gamepad",
            "ring|blink|arlo": "camera",
            "nest": "home",
        }
        for pattern, icon_key in icon_vendor_patterns.items():
            if re.search(pattern, vendor, re.IGNORECASE):
                icon = ICONS.get(icon_key, default_icon)
                break
        else:
            # MAC-based icon guessing
            mac_clean = mac.replace(':', '').replace('-', '').upper()
            icon_mac_patterns = {
                "001A79|B0BE83|BC926B": "apple",
                "001B63|BC4C4C": "tablet",
                "74ACB9|002468": "ethernet",
                "B827EB": "raspberry",
                "001422|001874": "desktop",
                "001CBF|002186": "server",
            }
            for pattern_str, icon_key in icon_mac_patterns.items():
                patterns = [p.replace(':', '').replace('-', '').upper() for p in pattern_str.split('|')]
                if any(mac_clean.startswith(p) for p in patterns):
                    icon = ICONS.get(icon_key, default_icon)
                    break
            else:
                # Name-based icon guessing
                icon_name_patterns = {
                    "iphone|ipad|macbook|imac": "apple",
                    "pixel|galaxy|redmi": "phone",
                    "laptop|notebook": "laptop",
                    "printer|print": "printer",
                    "router|gateway|ap|access[ -]?point": "router",
                    "tv|television|smarttv": "tv",
                    "desktop|pc|computer": "desktop",
                    "tablet|pad": "tablet",
                    "watch|wear": "watch",
                    "camera|cam|webcam": "camera",
                    "echo|alexa|dot": "speaker",
                    "hue|lifx|bulb": "lightbulb",
                    "server|nas": "server",
                    "playstation|xbox|switch": "gamepad",
                    "raspberry|pi": "raspberry",
                    "google|chromecast|nest": "google",
                    "doorbell|lock|security": "lock",
                }
                for pattern, icon_key in icon_name_patterns.items():
                    if re.search(pattern, name, re.IGNORECASE):
                        icon = ICONS.get(icon_key, default_icon)
                        break
                else:
                    # IP-based icon guessing
                    icon_ip_patterns = {
                        r"^192\.168\.[0-1]\.1$": "router",
                        r"^10\.0\.0\.1$": "router",
                        r"^192\.168\.[0-1]\.[2-9]$": "desktop",
                        r"^192\.168\.[0-1]\.1\d{2}$": "phone",
                    }
                    for pattern, icon_key in icon_ip_patterns.items():
                        if re.match(pattern, ip):
                            icon = ICONS.get(icon_key, default_icon)
                            break
                    else:
                        icon = default_icon

    # --- Type Guessing Logic ---
    if mac == "INTERNET":
        type_ = DEVICE_TYPES.get("Internet", default_type)
    else:
        # Vendor-based type guessing
        type_vendor_patterns = {
            "apple|samsung|motorola|xiaomi|huawei": "Phone",
            "dell|lenovo|asus|acer|hp": "Laptop",
            "epson|canon|brother": "Printer",
            "cisco|ubiquiti|netgear|tp-link|d-link|mikrotik|aruba|meraki": "Router",
            "lg|samsung electronics|sony|vizio": "TV",
            "raspberry pi": "IoT",
            "google|nest": "SmartHome",
            "espressif|particle": "IoT",
            "intel|amd": "Desktop",
            "amazon": "SmartSpeaker",
            "philips hue|lifx": "SmartLight",
            "qnap|synology": "Server",
            "nintendo|sony interactive|microsoft": "GamingConsole",
            "ring|blink|arlo": "Camera",
        }
        for pattern, type_key in type_vendor_patterns.items():
            if re.search(pattern, vendor, re.IGNORECASE):
                type_ = DEVICE_TYPES.get(type_key, default_type)
                break
        else:
            # MAC-based type guessing
            mac_clean = mac.replace(':', '').replace('-', '').upper()
            type_mac_patterns = {
                "00:1A:79|B0:BE:83|BC:92:6B": "Phone",
                "00:1B:63|BC:4C:4C": "Tablet",
                "74:AC:B9|00:24:68": "AccessPoint",
                "B8:27:EB": "IoT",
                "00:14:22|00:18:74": "Desktop",
                "00:1C:BF|00:21:86": "Server",
            }
            for pattern_str, type_key in type_mac_patterns.items():
                patterns = [p.replace(':', '').replace('-', '').upper() for p in pattern_str.split('|')]
                if any(mac_clean.startswith(p) for p in patterns):
                    type_ = DEVICE_TYPES.get(type_key, default_type)
                    break
            else:
                # Name-based type guessing
                type_name_patterns = {
                    "iphone|ipad": "Phone",
                    "macbook|imac": "Laptop",
                    "pixel|galaxy|redmi": "Phone",
                    "laptop|notebook": "Laptop",
                    "printer|print": "Printer",
                    "router|gateway|ap|access[ -]?point": "Router",
                    "tv|television|smarttv": "TV",
                    "desktop|pc|computer": "Desktop",
                    "tablet|pad": "Tablet",
                    "watch|wear": "Smartwatch",
                    "camera|cam|webcam": "Camera",
                    "echo|alexa|dot": "SmartSpeaker",
                    "hue|lifx|bulb": "SmartLight",
                    "server|nas": "Server",
                    "playstation|xbox|switch": "GamingConsole",
                    "raspberry|pi": "IoT",
                    "google|chromecast|nest": "SmartHome",
                    "doorbell|lock|security": "SecurityDevice",
                }
                for pattern, type_key in type_name_patterns.items():
                    if re.search(pattern, name, re.IGNORECASE):
                        type_ = DEVICE_TYPES.get(type_key, default_type)
                        break
                else:
                    # IP-based type guessing
                    type_ip_patterns = {
                        r"^192\.168\.[0-1]\.1$": "Router",
                        r"^10\.0\.0\.1$": "Router",
                        r"^192\.168\.[0-1]\.[2-9]$": "Desktop",
                        r"^192\.168\.[0-1]\.1\d{2}$": "Phone",
                    }
                    for pattern, type_key in type_ip_patterns.items():
                        if re.match(pattern, ip):
                            type_ = DEVICE_TYPES.get(type_key, default_type)
                            break
                    else:
                        type_ = default_type

    return icon, type_

# Deprecated functions with redirects (To be removed once all calls for these have been adjusted to use the updated function)
def guess_icon(
    vendor: Optional[str],
    mac: Optional[str],
    ip: Optional[str],
    name: Optional[str],
    default: str
    ) -> str:
    """
    [DEPRECATED] Guess the appropriate FontAwesome icon for a device based on its attributes.
    Use guess_device_attributes instead.

    Args:
        vendor: Device vendor name.
        mac: Device MAC address.
        ip: Device IP address.
        name: Device name.
        default: Default icon to return if no match is found.

    Returns:
        str: Base64-encoded FontAwesome icon HTML string.
    """
    
    icon, _ = guess_device_attributes(vendor, mac, ip, name, default, "unknown_type")
    return icon

def guess_type(
    vendor: Optional[str],
    mac: Optional[str],
    ip: Optional[str],
    name: Optional[str],
    default: str
    ) -> str:
    """
    [DEPRECATED] Guess the device type based on its attributes.
    Use guess_device_attributes instead.

    Args:
        vendor: Device vendor name.
        mac: Device MAC address.
        ip: Device IP address.
        name: Device name.
        default: Default type to return if no match is found.

    Returns:
        str: Device type from DEVICE_TYPES dictionary.
    """
    
    _, type_ = guess_device_attributes(vendor, mac, ip, name, "unknown_icon", default)
    return type_

# Handler for when this is run as a program instead of called as a module.
if __name__ == "__main__":
    mylog('error', "This module is not intended to be run directly.")
    
