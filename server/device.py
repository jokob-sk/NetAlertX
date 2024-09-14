
import subprocess

import conf
import os
import re
from helper import timeNowTZ, get_setting, get_setting_value, list_to_where, resolve_device_name_dig, resolve_device_name_pholus, get_device_name_nbtlookup, get_device_name_nslookup, check_IP_format
from logger import mylog, print_log
from const import vendorsPath, vendorsPathNewest, sql_generateGuid

#-------------------------------------------------------------------------------
# Device object handling (WIP)
#-------------------------------------------------------------------------------
class Device_obj:
    def __init__(self, db):
        self.db = db

    # Get all
    def getAll(self):
        self.db.sql.execute("""
            SELECT * FROM Devices
        """)
        return self.db.sql.fetchall()
    
    # Get all with unknown names
    def getUnknown(self):
        self.db.sql.execute("""
            SELECT * FROM Devices WHERE dev_Name in ("(unknown)", "(name not found)", "" )
        """)
        return self.db.sql.fetchall()

    # Get specific column value based on dev_MAC
    def getValueWithMac(self, column_name, dev_MAC):

        query = f"SELECT {column_name} FROM Devices WHERE dev_MAC = ?"

        self.db.sql.execute(query, (dev_MAC,))

        result = self.db.sql.fetchone()

        return result[column_name] if result else None


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
        # Check if local mac has been detected with other methods
        sql.execute (f"SELECT COUNT(*) FROM CurrentScan WHERE cur_MAC = '{local_mac}'")
        if sql.fetchone()[0] == 0 :
            sql.execute (f"""INSERT INTO CurrentScan (cur_MAC, cur_IP, cur_Vendor, cur_ScanMethod) VALUES ( '{local_mac}', '{local_ip}', Null, 'local_MAC') """)

#-------------------------------------------------------------------------------
def print_scan_stats(db):
    sql = db.sql # TO-DO

    query = """
    SELECT
        (SELECT COUNT(*) FROM CurrentScan) AS devices_detected,
        (SELECT COUNT(*) FROM CurrentScan WHERE NOT EXISTS (SELECT 1 FROM Devices WHERE dev_MAC = cur_MAC)) AS new_devices,
        (SELECT COUNT(*) FROM Devices WHERE dev_AlertDeviceDown != 0 AND NOT EXISTS (SELECT 1 FROM CurrentScan WHERE dev_MAC = cur_MAC)) AS down_alerts,
        (SELECT COUNT(*) FROM Devices WHERE dev_AlertDeviceDown != 0 AND dev_PresentLastScan = 1 AND NOT EXISTS (SELECT 1 FROM CurrentScan WHERE dev_MAC = cur_MAC)) AS new_down_alerts,
        (SELECT COUNT(*) FROM Devices WHERE dev_PresentLastScan = 0) AS new_connections,
        (SELECT COUNT(*) FROM Devices WHERE dev_PresentLastScan = 1 AND NOT EXISTS (SELECT 1 FROM CurrentScan WHERE dev_MAC = cur_MAC)) AS disconnections,
        (SELECT COUNT(*) FROM Devices, CurrentScan WHERE dev_MAC = cur_MAC AND dev_LastIP <> cur_IP) AS ip_changes,
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
                                      WHERE dev_MAC = cur_MAC) 
                            {list_to_where('OR', 'cur_MAC', 'NOT LIKE', get_setting_value('NEWDEV_ignored_MACs'))}
                            {list_to_where('OR', 'cur_IP', 'NOT LIKE', get_setting_value('NEWDEV_ignored_IPs'))}
                """ 

    
    mylog('debug',f'[New Devices] Query: {query}')
    
    sql.execute(query)

    mylog('debug',f'[New Devices] Insert Connection into session table')

    sql.execute (f"""INSERT INTO Sessions (ses_MAC, ses_IP, ses_EventTypeConnection, ses_DateTimeConnection,
                        ses_EventTypeDisconnection, ses_DateTimeDisconnection, ses_StillConnected, ses_AdditionalInfo)
                    SELECT cur_MAC, cur_IP,'Connected','{startTime}', NULL , NULL ,1, cur_Vendor
                    FROM CurrentScan 
                    WHERE NOT EXISTS (SELECT 1 FROM Sessions
                                      WHERE ses_MAC = cur_MAC) 
                            {list_to_where('OR', 'cur_MAC', 'NOT LIKE', get_setting_value('NEWDEV_ignored_MACs'))}
                            {list_to_where('OR', 'cur_IP', 'NOT LIKE', get_setting_value('NEWDEV_ignored_IPs'))}
                    """)
                    
    # Create new devices from CurrentScan
    mylog('debug','[New Devices] 2 Create devices')

    # default New Device values preparation
    newDevColumns = """dev_AlertEvents, 
                    dev_AlertDeviceDown, 
                    dev_PresentLastScan, 
                    dev_Archived, 
                    dev_NewDevice, 
                    dev_SkipRepeated, 
                    dev_ScanCycle, 
                    dev_Owner, 
                    dev_Favorite, 
                    dev_Group, 
                    dev_Comments, 
                    dev_LogEvents, 
                    dev_Location"""

    newDevDefaults = f"""{get_setting_value('NEWDEV_dev_AlertEvents')}, 
                        {get_setting_value('NEWDEV_dev_AlertDeviceDown')}, 
                        {get_setting_value('NEWDEV_dev_PresentLastScan')}, 
                        {get_setting_value('NEWDEV_dev_Archived')}, 
                        {get_setting_value('NEWDEV_dev_NewDevice')}, 
                        {get_setting_value('NEWDEV_dev_SkipRepeated')}, 
                        {get_setting_value('NEWDEV_dev_ScanCycle')}, 
                        '{get_setting_value('NEWDEV_dev_Owner')}', 
                        {get_setting_value('NEWDEV_dev_Favorite')}, 
                        '{get_setting_value('NEWDEV_dev_Group')}', 
                        '{get_setting_value('NEWDEV_dev_Comments')}', 
                        {get_setting_value('NEWDEV_dev_LogEvents')}, 
                        '{get_setting_value('NEWDEV_dev_Location')}'"""

    # Fetch data from CurrentScan
    current_scan_data = sql.execute("SELECT cur_MAC, cur_Name, cur_Vendor, cur_IP, cur_SyncHubNodeName, cur_NetworkNodeMAC, cur_PORT, cur_NetworkSite, cur_SSID, cur_Type FROM CurrentScan").fetchall()

    for row in current_scan_data:
        cur_MAC, cur_Name, cur_Vendor, cur_IP, cur_SyncHubNodeName, cur_NetworkNodeMAC, cur_PORT, cur_NetworkSite, cur_SSID, cur_Type = row

        # Handle NoneType
        cur_Name = cur_Name.strip() if cur_Name else '(unknown)'
        cur_Type = cur_Type.strip() if cur_Type else get_setting_value("NEWDEV_dev_DeviceType")
        cur_NetworkNodeMAC = cur_NetworkNodeMAC.strip() if cur_NetworkNodeMAC else ''
        cur_NetworkNodeMAC = cur_NetworkNodeMAC if cur_NetworkNodeMAC and cur_MAC != "Internet" else (get_setting_value("NEWDEV_dev_Network_Node_MAC_ADDR") if cur_MAC != "Internet" else "null")

        # Preparing the individual insert statement
        sqlQuery = f"""INSERT OR IGNORE INTO Devices 
                        (
                            dev_MAC, 
                            dev_name, 
                            dev_Vendor,
                            dev_LastIP, 
                            dev_FirstConnection, 
                            dev_LastConnection, 
                            dev_SyncHubNodeName, 
                            dev_GUID,
                            dev_Network_Node_MAC_ADDR, 
                            dev_Network_Node_port,
                            dev_NetworkSite, 
                            dev_SSID,
                            dev_DeviceType,                          
                            {newDevColumns}
                        )
                        VALUES 
                        (
                            '{cur_MAC}', 
                            '{cur_Name}',
                            '{cur_Vendor}', 
                            '{cur_IP}', 
                            ?, 
                            ?, 
                            '{cur_SyncHubNodeName}', 
                            {sql_generateGuid},
                            '{cur_NetworkNodeMAC}',
                            '{cur_PORT}',
                            '{cur_NetworkSite}', 
                            '{cur_SSID}',
                            '{cur_Type}', 
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
    sql.execute(f"""UPDATE Devices SET dev_LastConnection = '{startTime}',
                        dev_PresentLastScan = 1
                    WHERE dev_PresentLastScan = 0
                      AND EXISTS (SELECT 1 FROM CurrentScan 
                                  WHERE dev_MAC = cur_MAC) """)

    # Clean no active devices
    mylog('debug', '[Update Devices] 2 Clean no active devices')
    sql.execute("""UPDATE Devices SET dev_PresentLastScan = 0
                    WHERE NOT EXISTS (SELECT 1 FROM CurrentScan 
                                      WHERE dev_MAC = cur_MAC) """)

    # Update IP 
    mylog('debug', '[Update Devices] - cur_IP -> dev_LastIP (always updated)')
    sql.execute("""UPDATE Devices
                    SET dev_LastIP = (SELECT cur_IP FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC)
                    WHERE EXISTS (SELECT 1 FROM CurrentScan
                                  WHERE dev_MAC = cur_MAC) """)

    # Update only devices with empty or NULL vendors
    mylog('debug', '[Update Devices] - cur_Vendor -> (if empty) dev_Vendor')
    sql.execute("""UPDATE Devices
                    SET dev_Vendor = (
                        SELECT cur_Vendor
                        FROM CurrentScan
                        WHERE Devices.dev_MAC = CurrentScan.cur_MAC
                    )
                    WHERE 
                        (dev_Vendor IS NULL OR dev_Vendor IN ("", "null"))
                        AND EXISTS (
                            SELECT 1
                            FROM CurrentScan
                            WHERE Devices.dev_MAC = CurrentScan.cur_MAC
                        )""")

    # Update only devices with empty or NULL dev_Network_Node_port 
    mylog('debug', '[Update Devices] - (if not empty) cur_Port -> dev_Network_Node_port')
    sql.execute("""UPDATE Devices
                    SET dev_Network_Node_port = (
                    SELECT cur_Port
                    FROM CurrentScan        
                    WHERE Devices.dev_MAC = CurrentScan.cur_MAC          
                )
                WHERE EXISTS (
                    SELECT 1
                    FROM CurrentScan
                    WHERE Devices.dev_MAC = CurrentScan.cur_MAC
                      AND CurrentScan.cur_Port IS NOT NULL AND CurrentScan.cur_Port NOT IN ("", "null")
                )""")

    # Update only devices with empty or NULL dev_Network_Node_MAC_ADDR 
    mylog('debug', '[Update Devices] - (if not empty) cur_NetworkNodeMAC -> dev_Network_Node_MAC_ADDR')
    sql.execute("""UPDATE Devices
                    SET dev_Network_Node_MAC_ADDR = (
                    SELECT cur_NetworkNodeMAC
                    FROM CurrentScan
                    WHERE Devices.dev_MAC = CurrentScan.cur_MAC
                )
                WHERE EXISTS (
                    SELECT 1
                    FROM CurrentScan
                    WHERE Devices.dev_MAC = CurrentScan.cur_MAC
                        AND CurrentScan.cur_NetworkNodeMAC IS NOT NULL AND CurrentScan.cur_NetworkNodeMAC NOT IN ("", "null")
                )""")

    # Update only devices with empty or NULL dev_NetworkSite 
    mylog('debug', '[Update Devices] - (if not empty) cur_NetworkSite -> (if empty) dev_NetworkSite')
    sql.execute("""UPDATE Devices
                    SET dev_NetworkSite = (
                        SELECT cur_NetworkSite
                        FROM CurrentScan
                        WHERE Devices.dev_MAC = CurrentScan.cur_MAC
                    )
                    WHERE 
                        (dev_NetworkSite IS NULL OR dev_NetworkSite IN ("", "null"))
                        AND EXISTS (
                            SELECT 1
                            FROM CurrentScan
                            WHERE Devices.dev_MAC = CurrentScan.cur_MAC
                                AND CurrentScan.cur_NetworkSite IS NOT NULL AND CurrentScan.cur_NetworkSite NOT IN ("", "null")
                )""")

    # Update only devices with empty or NULL dev_SSID 
    mylog('debug', '[Update Devices] - (if not empty) cur_SSID -> (if empty) dev_SSID')
    sql.execute("""UPDATE Devices
                    SET dev_SSID = (
                        SELECT cur_SSID
                        FROM CurrentScan
                        WHERE Devices.dev_MAC = CurrentScan.cur_MAC
                    )
                    WHERE 
                        (dev_SSID IS NULL OR dev_SSID IN ("", "null"))
                        AND EXISTS (
                            SELECT 1
                            FROM CurrentScan
                            WHERE Devices.dev_MAC = CurrentScan.cur_MAC
                                AND CurrentScan.cur_SSID IS NOT NULL AND CurrentScan.cur_SSID NOT IN ("", "null")
                        )""")

    # Update only devices with empty or NULL dev_DeviceType
    mylog('debug', '[Update Devices] - (if not empty) cur_Type -> (if empty) dev_DeviceType')
    sql.execute("""UPDATE Devices
                    SET dev_DeviceType = (
                        SELECT cur_Type
                        FROM CurrentScan
                        WHERE Devices.dev_MAC = CurrentScan.cur_MAC
                    )
                    WHERE 
                        (dev_DeviceType IS NULL OR dev_DeviceType IN ("", "null"))
                        AND EXISTS (
                            SELECT 1
                            FROM CurrentScan
                            WHERE Devices.dev_MAC = CurrentScan.cur_MAC
                                AND CurrentScan.cur_Type IS NOT NULL AND CurrentScan.cur_Type NOT IN ("", "null")
                        )""")

    # Update (unknown) or (name not found) Names if available
    mylog('debug','[Update Devices] - (if not empty) cur_Name -> (if empty) dev_NAME')
    sql.execute ("""    UPDATE Devices
                        SET dev_NAME = COALESCE((
                            SELECT cur_Name 
                            FROM CurrentScan
                            WHERE cur_MAC = dev_MAC
                            AND cur_Name IS NOT NULL
                            AND cur_Name <> 'null'
                            AND cur_Name <> ''
                        ), dev_NAME)
                        WHERE (dev_NAME IN ('(unknown)', '(name not found)', '') 
                            OR dev_NAME IS NULL)
                        AND EXISTS (
                            SELECT 1 
                            FROM CurrentScan
                            WHERE cur_MAC = dev_MAC
                            AND cur_Name IS NOT NULL
                            AND cur_Name <> 'null'
                            AND cur_Name <> ''
                        ) """)

    # Update VENDORS
    recordsToUpdate = []
    query = """SELECT * FROM Devices
               WHERE dev_Vendor = '(unknown)' OR dev_Vendor =''
                  OR dev_Vendor IS NULL"""

    for device in sql.execute (query) :
        vendor = query_MAC_vendor (device['dev_MAC'])
        if vendor != -1 and vendor != -2 :
            recordsToUpdate.append ([vendor, device['dev_MAC']])

    if len(recordsToUpdate) > 0: 
        sql.executemany ("UPDATE Devices SET dev_Vendor = ? WHERE dev_MAC = ? ", recordsToUpdate )
    
    # Guess ICONS
    recordsToUpdate = []
    query = """SELECT * FROM Devices
               WHERE dev_Icon in ('', 'null')
                  OR dev_Icon IS NULL"""
    default_icon = get_setting_value('NEWDEV_dev_Icon')
    
    for device in sql.execute (query) :
        # Conditional logic for dev_Icon guessing        
        dev_Icon = guess_icon(device['dev_Vendor'], device['dev_MAC'], device['dev_LastIP'], device['dev_Name'], default_icon)

        recordsToUpdate.append ([dev_Icon, device['dev_MAC']])
    
    if len(recordsToUpdate) > 0:        
        sql.executemany ("UPDATE Devices SET dev_Icon = ? WHERE dev_MAC = ? ", recordsToUpdate )

    # Guess Type
    recordsToUpdate = []
    query = """SELECT * FROM Devices
               WHERE dev_DeviceType in ('', 'null')
                  OR dev_DeviceType IS NULL"""
    default_type = get_setting_value('NEWDEV_dev_DeviceType')
    
    for device in sql.execute (query) :
        # Conditional logic for dev_Icon guessing        
        dev_DeviceType = guess_type(device['dev_Vendor'], device['dev_MAC'], device['dev_LastIP'], device['dev_Name'], default_type)

        recordsToUpdate.append ([dev_DeviceType, device['dev_MAC']])
    
    if len(recordsToUpdate) > 0:        
        sql.executemany ("UPDATE Devices SET dev_DeviceType = ? WHERE dev_MAC = ? ", recordsToUpdate )
    
    
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
    foundNsLookup = 0
    foundNbtLookup = 0
    foundPholus = 0

    # Gen unknown devices
    sql.execute ("SELECT * FROM Devices WHERE dev_Name IN ('(unknown)','', '(name not found)') AND dev_LastIP <> '-'")
    unknownDevices = sql.fetchall() 
    db.commitDB()

    # skip checks if no unknown devices
    if len(unknownDevices) == 0:
        return

    # Devices without name
    mylog('verbose', f'[Update Device Name] Trying to resolve devices without name. Unknown devices count: {len(unknownDevices)}')

    # get names from Pholus scan 
    sql.execute ('SELECT * FROM Pholus_Scan where "Record_Type"="Answer"')    
    pholusResults = list(sql.fetchall())        
    db.commitDB()

    # Number of entries from previous Pholus scans
    mylog('verbose', ['[Update Device Name] Pholus entries from prev scans: ', len(pholusResults)])


    for device in unknownDevices:
        newName = nameNotFound
        
        # Resolve device name with DiG
        newName = resolve_device_name_dig (device['dev_MAC'], device['dev_LastIP'])
        
        # count
        if newName != nameNotFound:
            foundDig += 1

        # Resolve device name with NSLOOKUP plugin data
        if newName == nameNotFound:
            newName = get_device_name_nslookup(db, device['dev_MAC'], device['dev_LastIP'])

            if newName != nameNotFound:
               foundNsLookup += 1
               
        # Resolve device name with NSLOOKUP plugin data
        if newName == nameNotFound:
            newName = get_device_name_nbtlookup(db, device['dev_MAC'], device['dev_LastIP'])

            if newName != nameNotFound:
               foundNbtLookup += 1


        # Resolve with Pholus 
        if newName == nameNotFound:

            # Try MAC matching
            newName =  resolve_device_name_pholus (device['dev_MAC'], device['dev_LastIP'], pholusResults, nameNotFound, False)
            # Try IP matching 
            if newName == nameNotFound:
                newName =  resolve_device_name_pholus (device['dev_MAC'], device['dev_LastIP'], pholusResults, nameNotFound, True)

            # count
            if newName != nameNotFound:
                foundPholus += 1
        
        # if still not found update name so we can distinguish the devices where we tried already
        if newName == nameNotFound :

            notFound += 1

            # if dev_Name is the same as what we will change it to, take no action
            # this mitigates a race condition which would overwrite a users edits that occured since the select earlier
            if device['dev_Name'] != nameNotFound:
                recordsNotFound.append (["(name not found)", device['dev_MAC']])          
        else:
            # name was found with DiG or Pholus
            recordsToUpdate.append ([newName, device['dev_MAC']])

    # Print log            
    mylog('verbose', ['[Update Device Name] Names Found (DiG/NSLOOKUP/NBTSCAN/Pholus): ', len(recordsToUpdate), " (",foundDig,"/",foundNsLookup,"/",foundNbtLookup,"/", foundPholus ,")"] )                 
    mylog('verbose', ['[Update Device Name] Names Not Found         : ', notFound] )    
     
    # update not found devices with (name not found) 
    sql.executemany ("UPDATE Devices SET dev_Name = ? WHERE dev_MAC = ? ", recordsNotFound )
    # update names of devices which we were bale to resolve
    sql.executemany ("UPDATE Devices SET dev_Name = ? WHERE dev_MAC = ? ", recordsToUpdate )
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
                    parts = line.split(' ', 1)
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
    elif mac == "INTERNET":  # Apple
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
    name   = name.lower() if name else "(unknown)"

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
    