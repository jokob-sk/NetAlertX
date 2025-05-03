import sys

# Register NetAlertX directories
INSTALL_PATH="/app"
sys.path.extend([f"{INSTALL_PATH}/server"])

import subprocess
import conf
import os
import re
from helper import timeNowTZ, get_setting, get_setting_value, list_to_where, resolve_device_name_dig, get_device_name_nbtlookup, get_device_name_nslookup, get_device_name_mdns, check_IP_format, sanitize_SQL_input
from logger import mylog
from const import vendorsPath, vendorsPathNewest, sql_generateGuid
from models.device_instance import DeviceInstance

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
def update_devices_names (db):
    sql = db.sql #TO-DO
    # Initialize variables
    recordsToUpdate = []
    recordsNotFound = []

    nameNotFound = "(name not found)"

    ignored = 0
    notFound = 0

    foundDig = 0
    foundmDNSLookup = 0
    foundNsLookup = 0
    foundNbtLookup = 0

    # Gen unknown devices    
    device_handler = DeviceInstance(db)
    # Retrieve devices
    unknownDevices = device_handler.getUnknown()

    # skip checks if no unknown devices
    if len(unknownDevices) == 0:
        return

    # Devices without name
    mylog('verbose', f'[Update Device Name] Trying to resolve devices without name. Unknown devices count: {len(unknownDevices)}')

    for device in unknownDevices:
        newName = nameNotFound
        
        # Resolve device name with DiG
        newName = resolve_device_name_dig (device['devMac'], device['devLastIP'])
        
        # count
        if newName != nameNotFound:
            foundDig += 1
            
        # Resolve device name with AVAHISCAN plugin data
        if newName == nameNotFound:
            newName = get_device_name_mdns(db, device['devMac'], device['devLastIP'])

            if newName != nameNotFound:
               foundmDNSLookup += 1

        # Resolve device name with NSLOOKUP plugin data
        if newName == nameNotFound:
            newName = get_device_name_nslookup(db, device['devMac'], device['devLastIP'])

            if newName != nameNotFound:
               foundNsLookup += 1
               
        # Resolve device name with NBTLOOKUP plugin data
        if newName == nameNotFound:
            newName = get_device_name_nbtlookup(db, device['devMac'], device['devLastIP'])

            if newName != nameNotFound:
               foundNbtLookup += 1
        
        # if still not found update name so we can distinguish the devices where we tried already
        if newName == nameNotFound :

            notFound += 1

            # if devName is the same as what we will change it to, take no action
            # this mitigates a race condition which would overwrite a users edits that occured since the select earlier
            if device['devName'] != nameNotFound:
                recordsNotFound.append (["(name not found)", device['devMac']])          
        else:
            # name was found 
            recordsToUpdate.append ([newName, device['devMac']])

    # Print log            
    mylog('verbose', [f'[Update Device Name] Names Found (DiG/mDNS/NSLOOKUP/NBTSCAN): {len(recordsToUpdate)} ({foundDig}/{foundmDNSLookup}/{foundNsLookup}/{foundNbtLookup})'] )                 
    mylog('verbose', [f'[Update Device Name] Names Not Found         : {notFound}'] )    
     
    # update not found devices with (name not found) 
    sql.executemany ("UPDATE Devices SET devName = ? WHERE devMac = ? ", recordsNotFound )
    # update names of devices which we were bale to resolve
    sql.executemany ("UPDATE Devices SET devName = ? WHERE devMac = ? ", recordsToUpdate )
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
# Base64 encoded HTML string for FontAwesome icons
icons = {
    "globe": "PGkgY2xhc3M9ImZhcyBmYS1nbG9iZSI+PC9pPg==",  # globe icon
    "phone": "PGkgY2xhc3M9ImZhcyBmYS1tb2JpbGUtYWx0Ij48L2k+",
    "laptop": "PGkgY2xhc3M9ImZhIGZhLWxhcHRvcCI+PC9pPg==",
    "printer": "PGkgY2xhc3M9ImZhIGZhLXByaW50ZXIiPjwvaT4=",
    "router": "PGkgY2xhc3M9ImZhcyBmYS1yYW5kb20iPjwvaT4=",
    "tv": "PGkgY2xhc3M9ImZhIGZhLXR2Ij48L2k+",
    "desktop": "PGkgY2xhc3M9ImZhIGZhLWRlc2t0b3AiPjwvaT4=",
    "tablet": "PGkgY2xhc3M9ImZhIGZhLXRhYmxldCI+PC9pPg==",
    "watch": "PGkgY2xhc3M9ImZhIGZhLXdhbmNoIj48L2k+",
    "camera": "PGkgY2xhc3M9ImZhIGZhLWNhbWVyYSI+PC9pPg==",
    "home": "PGkgY2xhc3M9ImZhIGZhLWhvbWUiPjwvaT4=",
    "apple": "PGkgY2xhc3M9ImZhYiBmYS1hcHBsZSI+PC9pPg==",
    "ethernet": "PGkgY2xhc3M9ImZhcyBmYS1ldGhlcm5ldCI+PC9pPg==",
    "google": "PGkgY2xhc3M9ImZhYiBmYS1nb29nbGUiPjwvaT4=",
    "raspberry": "PGkgY2xhc3M9ImZhYiBmYS1yYXNwYmVycnktcGkiPjwvaT4=",
    "microchip": "PGkgY2xhc3M9ImZhcyBmYS1taWNyb2NoaXAiPjwvaT4="
}

#-------------------------------------------------------------------------------
# Guess device icon
def guess_icon(vendor, mac, ip, name,  default):    
            
    mylog('debug', [f"[guess_icon] Guessing icon for (vendor|mac|ip|name): ('{vendor}'|'{mac}'|{ip}|{name})"])
    
    result = default
    mac    = mac.upper()
    vendor = vendor.lower() if vendor else "unknown"
    name   = name.lower() if name else "(unknown)"

    # Guess icon based on vendor
    if any(brand in vendor for brand in {"samsung", "motorola"}):
        result = icons.get("phone")
    elif "dell" in vendor:
        result = icons.get("laptop")
    elif "hp" in vendor:
        result = icons.get("printer")
    elif "cisco" in vendor:
        result = icons.get("router")
    elif "lg" in vendor:
        result = icons.get("tv")
    elif "raspberry" in vendor:
        result = icons.get("raspberry")
    elif "apple" in vendor:
        result = icons.get("apple")
    elif "google" in vendor:
        result = icons.get("google")
    elif "ubiquiti" in vendor:
        result = icons.get("router")
    elif any(brand in vendor for brand in {"espressif"}):
        result = icons.get("microchip")

    # Guess icon based on MAC address patterns
    elif mac == "INTERNET":  
        result = icons.get("globe")
    elif mac.startswith("00:1A:79"):  # Apple
        result = icons.get("apple")
    elif mac.startswith("B0:BE:83"):  # Apple
        result = icons.get("apple")
    elif mac.startswith("00:1B:63"):  # Sony
        result = icons.get("tablet")
    elif mac.startswith("74:AC:B9"):  # Unifi
        result = icons.get("ethernet")
        
        
    # Guess icon based on name
    elif 'google' in name:
        result = icons.get("google")
    elif 'desktop' in name:
        result = icons.get("desktop")
    elif 'raspberry' in name:
        result = icons.get("raspberry")
    
    # Guess icon based on IP address ranges
    elif ip.startswith("192.168.1."):
        result = icons.get("laptop")       

    
    return result

#-------------------------------------------------------------------------------
# Guess device type
def guess_type(vendor, mac, ip, name,  default):
    result = default
    mac    = mac.upper()
    vendor = vendor.lower() if vendor else "unknown"
    name   = str(name).lower() if name else "(unknown)"

    # Guess icon based on vendor
    if any(brand in vendor for brand in {"samsung", "motorola"}):
        result = "Phone"
    elif "cisco" in vendor:
        result = "Router" 
    elif "lg" in vendor:
        result = "TV"
    elif "google" in vendor:
        result = "Phone"
    elif "ubiquiti" in vendor:
        result = "Router" 

    # Guess type based on MAC address patterns
    elif mac == "INTERNET":  
        result = "Internet"      
        
    # Guess type based on name
    elif 'google' in name:
        result = "Phone"
    
    # Guess type based on IP address ranges
    elif ip == ("192.168.1.1"):
        result = "Router"      
    
    return result
    
