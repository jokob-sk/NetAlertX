
import subprocess

import conf
import re
from helper import timeNowTZ, get_setting, get_setting_value,resolve_device_name_dig, resolve_device_name_pholus, check_IP_format
from logger import mylog, print_log
from const import vendorsPath

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

    if str(stats[0]["new_devices"]) != '0':
        mylog('debug', f'   ================ DEVICES table content  ================')
        sql.execute('select * from Devices')
        rows = sql.fetchall()
        for row in rows:
            row_dict = dict(row)
            mylog('debug', f'    {row_dict}')
        
        mylog('debug', f'   ================ CurrentScan table content  ================')
        sql.execute('select * from CurrentScan')
        rows = sql.fetchall()
        for row in rows:
            row_dict = dict(row)
            mylog('debug', f'    {row_dict}')
        
        mylog('debug', f'   ================ Events table content where eve_PendingAlertEmail = 1  ================')
        sql.execute('select * from Events where eve_PendingAlertEmail = 1')
        rows = sql.fetchall()
        for row in rows:
            row_dict = dict(row)
            mylog('debug', f'    {row_dict}')

        mylog('debug', f'   ================ Events table COUNT  ================')
        sql.execute('select count(*) from Events')
        rows = sql.fetchall()
        for row in rows:
            row_dict = dict(row)
            mylog('debug', f'    {row_dict}')
        

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
    sql.execute (f"""INSERT INTO Events (eve_MAC, eve_IP, eve_DateTime,
                        eve_EventType, eve_AdditionalInfo,
                        eve_PendingAlertEmail)
                    SELECT cur_MAC, cur_IP, '{startTime}', 'New Device', cur_Vendor, 1
                    FROM CurrentScan
                    WHERE NOT EXISTS (SELECT 1 FROM Devices
                                      WHERE dev_MAC = cur_MAC) """ ) 

    mylog('debug','[New Devices] Insert Connection into session table')
    sql.execute (f"""INSERT INTO Sessions (ses_MAC, ses_IP, ses_EventTypeConnection, ses_DateTimeConnection,
                        ses_EventTypeDisconnection, ses_DateTimeDisconnection, ses_StillConnected, ses_AdditionalInfo)
                    SELECT cur_MAC, cur_IP,'Connected','{startTime}', NULL , NULL ,1, cur_Vendor
                    FROM CurrentScan 
                    WHERE NOT EXISTS (SELECT 1 FROM Sessions
                                      WHERE ses_MAC = cur_MAC) """)
                    
    # Create new devices from CurrentScan
    mylog('debug','[New Devices] 2 Create devices')

    # default New Device values preparation
    newDevColumns  =   """dev_AlertEvents, 
                          dev_AlertDeviceDown, 
                          dev_PresentLastScan, 
                          dev_Archived, 
                          dev_NewDevice, 
                          dev_SkipRepeated, 
                          dev_ScanCycle, 
                          dev_Owner, 
                          dev_DeviceType, 
                          dev_Favorite, 
                          dev_Group, 
                          dev_Comments, 
                          dev_LogEvents, 
                          dev_Location, 
                          dev_Network_Node_MAC_ADDR, 
                          dev_Icon"""

    newDevDefaults =  f"""{get_setting_value('NEWDEV_dev_AlertEvents')}, 
                          {get_setting_value('NEWDEV_dev_AlertDeviceDown')}, 
                          {get_setting_value('NEWDEV_dev_PresentLastScan')}, 
                          {get_setting_value('NEWDEV_dev_Archived')}, 
                          {get_setting_value('NEWDEV_dev_NewDevice')}, 
                          {get_setting_value('NEWDEV_dev_SkipRepeated')}, 
                          {get_setting_value('NEWDEV_dev_ScanCycle')}, 
                          '{get_setting_value('NEWDEV_dev_Owner')}', 
                          '{get_setting_value('NEWDEV_dev_DeviceType')}',
                          {get_setting_value('NEWDEV_dev_Favorite')}, 
                          '{get_setting_value('NEWDEV_dev_Group')}', 
                          '{get_setting_value('NEWDEV_dev_Comments')}', 
                          {get_setting_value('NEWDEV_dev_LogEvents')}, 
                          '{get_setting_value('NEWDEV_dev_Location')}',  
                          '{get_setting_value('NEWDEV_dev_Network_Node_MAC_ADDR')}',  
                          '{get_setting_value('NEWDEV_dev_Icon')}'
                    """
    
    sqlQuery = f"""INSERT OR IGNORE INTO Devices (dev_MAC, dev_name, dev_Vendor,
                        dev_LastIP, dev_FirstConnection, dev_LastConnection,
                        {newDevColumns})
                    SELECT cur_MAC, 
                        CASE WHEN LENGTH(TRIM(cur_Name)) > 0 THEN cur_Name
                                ELSE '(unknown)' END,
                        cur_Vendor, cur_IP, ?, ?,
                        {newDevDefaults}
                    FROM CurrentScan"""


    mylog('debug',f'[New Devices] Create devices SQL: {sqlQuery}')

    sql.execute (sqlQuery, (startTime, startTime) ) 

    
    mylog('debug','[New Devices] New Devices end')
    db.commitDB()


#-------------------------------------------------------------------------------
def update_devices_data_from_scan (db):
    sql = db.sql #TO-DO    
    startTime = timeNowTZ()

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
    mylog('debug', '[Update Devices] - 3 LastIP ')
    sql.execute("""UPDATE Devices
                    SET dev_LastIP = (SELECT cur_IP FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC)
                    WHERE EXISTS (SELECT 1 FROM CurrentScan
                                  WHERE dev_MAC = cur_MAC) """)

    # Update only devices with empty or NULL vendors
    mylog('debug', '[Update Devices] - 3 Vendor')
    sql.execute("""UPDATE Devices
                    SET dev_Vendor = (
                        SELECT cur_Vendor
                        FROM CurrentScan
                        WHERE dev_MAC = cur_MAC
                    )
                    WHERE 
                        (dev_Vendor = "" OR dev_Vendor IS NULL)
                        AND EXISTS (
                            SELECT 1
                            FROM CurrentScan
                            WHERE dev_MAC = cur_MAC
                        )""")

    # Update (unknown) or (name not found) Names if available
    mylog('debug','[Update Devices] - 4 Unknown Name')
    sql.execute ("""UPDATE Devices
                    SET dev_NAME = (SELECT cur_Name FROM CurrentScan
                                    WHERE cur_MAC = dev_MAC)
                    WHERE (dev_Name in ("(unknown)", "(name not found)", "" )
                           OR dev_Name IS NULL)
                      AND EXISTS (SELECT 1 FROM CurrentScan
                                  WHERE cur_MAC = dev_MAC
                                    AND cur_Name IS NOT NULL
                                    AND cur_Name IS NOT 'null'
                                    AND cur_Name <> '') """)

    recordsToUpdate = []
    query = """SELECT * FROM Devices
               WHERE dev_Vendor = '(unknown)' OR dev_Vendor =''
                  OR dev_Vendor IS NULL"""

    for device in sql.execute (query) :
        vendor = query_MAC_vendor (device['dev_MAC'])
        if vendor != -1 and vendor != -2 :
            recordsToUpdate.append ([vendor, device['dev_MAC']])

    sql.executemany ("UPDATE Devices SET dev_Vendor = ? WHERE dev_MAC = ? ",
        recordsToUpdate )
    
    
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
    foundPholus = 0

    # BUGFIX #97 - Updating name of Devices w/o IP    
    sql.execute ("SELECT * FROM Devices WHERE dev_Name IN ('(unknown)','', '(name not found)') AND dev_LastIP <> '-'")
    unknownDevices = sql.fetchall() 
    db.commitDB()

    # skip checks if no unknown devices
    if len(unknownDevices) == 0:
        return

    # Devices without name
    mylog('verbose', '[Update Device Name] Trying to resolve devices without name')

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
        
        # isf still not found update name so we can distinguish the devices where we tried already
        if newName == nameNotFound :
            # if dev_Name is the same as what we will change it to, take no action
            # this mitigates a race condition which would overwrite a users edits that occured since the select earlier
            if device['dev_Name'] != nameNotFound:
                recordsNotFound.append (["(name not found)", device['dev_MAC']])          
        else:
            # name was found with DiG or Pholus
            recordsToUpdate.append ([newName, device['dev_MAC']])

    # Print log            
    mylog('verbose', ['[Update Device Name] Names Found (DiG/Pholus): ', len(recordsToUpdate), " (",foundDig,"/",foundPholus ,")"] )                 
    mylog('verbose', ['[Update Device Name] Names Not Found         : ', len(recordsNotFound)] )    
     
    # update not found devices with (name not found) 
    sql.executemany ("UPDATE Devices SET dev_Name = ? WHERE dev_MAC = ? ", recordsNotFound )
    # update names of devices which we were bale to resolve
    sql.executemany ("UPDATE Devices SET dev_Name = ? WHERE dev_MAC = ? ", recordsToUpdate )
    db.commitDB()

#-------------------------------------------------------------------------------
# Check if the variable contains a valid MAC address or "Internet"
def check_mac_or_internet(input_str):
    # Regular expression pattern for matching a MAC address
    mac_pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'

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
    
    # Check MAC parameter
    mac = pMACstr.replace (':','')
    if len(pMACstr) != 17 or len(mac) != 12 :
        return -2 # return -2 if ignored MAC

    # Search vendor in HW Vendors DB
    mac_start_string6 = mac[0:6]    
    mac_start_string9 = mac[0:9]    

    try:
        with open(vendorsPath, 'r') as f:
            for line in f:
                if line.startswith(mac_start_string6):
                    vendor = line.split(' ', 1)[1].strip()
                    mylog('debug', [f"[Vendor Check] Found '{vendor}' for '{pMAC}' in {vendorsPath}"])
                    return vendor


        return -1  # MAC address not found in the database
    except FileNotFoundError:
        mylog('none', [f"[Vendor Check] ⚠ ERROR: Vendors file {vendorsPath} not found."])
        return -1

