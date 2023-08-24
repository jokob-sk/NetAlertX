
import subprocess

import conf
import re
from helper import timeNowTZ, get_setting, get_setting_value,resolve_device_name_dig, resolve_device_name_pholus
from scanners.internet import check_IP_format, get_internet_IP
from logger import mylog, print_log
from mac_vendor import query_MAC_vendor

#-------------------------------------------------------------------------------


def save_scanned_devices (db):
    sql = db.sql #TO-DO
    cycle = 1 # always 1, only one cycle supported

    # mylog('debug', ['[ARP Scan] Detected devices:', len(p_arpscan_devices)])

    # handled by the ARPSCAN plugin

# ------------------------ TO CONVERT INTO PLUGIN
    # # Insert Pi-hole devices
    # startTime = timeNowTZ()
    # sql.execute ("""INSERT INTO CurrentScan (cur_ScanCycle, cur_MAC, 
    #                     cur_IP, cur_Vendor, cur_ScanMethod)
    #                 SELECT ?, PH_MAC, PH_IP, PH_Vendor, 'Pi-hole'
    #                 FROM PiHole_Network
    #                 WHERE PH_LastQuery >= ?
    #                   AND NOT EXISTS (SELECT 'X' FROM CurrentScan
    #                                   WHERE cur_MAC = PH_MAC
    #                                     AND cur_ScanCycle = ? )""",
    #                 (cycle,
    #                  (int(startTime.strftime('%s')) - 60 * p_cycle_interval),
    #                  cycle) )
# ------------------------ TO CONVERT INTO PLUGIN


    # Check Internet connectivity
    internet_IP = get_internet_IP( conf.DIG_GET_IP_ARG )
        # TESTING - Force IP
        # internet_IP = ""
    if internet_IP != "" :
        sql.execute (f"""INSERT INTO CurrentScan (cur_ScanCycle, cur_MAC, cur_IP, cur_Vendor, cur_ScanMethod)
                        VALUES ( 1, 'Internet', '{internet_IP}', Null, 'queryDNS') """)

    # #76 Add Local MAC of default local interface
      # BUGFIX #106 - Device that pialert is running
        # local_mac_cmd = ["bash -lc ifconfig `ip route list default | awk {'print $5'}` | grep ether | awk '{print $2}'"]
          # local_mac_cmd = ["/sbin/ifconfig `ip route list default | sort -nk11 | head -1 | awk {'print $5'}` | grep ether | awk '{print $2}'"]
    local_mac_cmd = ["/sbin/ifconfig `ip -o route get 1 | sed 's/^.*dev \\([^ ]*\\).*$/\\1/;q'` | grep ether | awk '{print $2}'"]
    local_mac = subprocess.Popen (local_mac_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0].decode().strip()

    # local_dev_cmd = ["ip -o route get 1 | sed 's/^.*dev \\([^ ]*\\).*$/\\1/;q'"]
    # local_dev = subprocess.Popen (local_dev_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0].decode().strip()
    
    # local_ip_cmd = ["ip route list default | awk {'print $7'}"]
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
            sql.execute (f"""INSERT INTO CurrentScan (cur_ScanCycle, cur_MAC, cur_IP, cur_Vendor, cur_ScanMethod) VALUES ( 1, '{local_mac}', '{local_ip}', Null, 'local_MAC') """)

#-------------------------------------------------------------------------------
def print_scan_stats (db):
    sql = db.sql #TO-DO
    # Devices Detected
    sql.execute ("""SELECT COUNT(*) FROM CurrentScan""")
    mylog('verbose', ['[Scan Stats]    Devices Detected.......: ', str (sql.fetchone()[0]) ])

    # Devices arp-scan
    sql.execute ("""SELECT COUNT(*) FROM CurrentScan WHERE cur_ScanMethod='arp-scan' """)
    mylog('verbose', ['[Scan Stats]        arp-scan detected..: ', str (sql.fetchone()[0]) ])

    # Devices Pi-hole
    sql.execute ("""SELECT COUNT(*) FROM CurrentScan WHERE cur_ScanMethod='PiHole'""")
    mylog('verbose', ['[Scan Stats]        Pi-hole detected...: +' + str (sql.fetchone()[0]) ])

    # New Devices
    sql.execute ("""SELECT COUNT(*) FROM CurrentScan
                    WHERE NOT EXISTS (SELECT 1 FROM Devices
                                      WHERE dev_MAC = cur_MAC) """)
    mylog('verbose', ['[Scan Stats]        New Devices........: ' + str (sql.fetchone()[0]) ])

    # Down Alerts
    sql.execute ("""SELECT COUNT(*) FROM Devices
                    WHERE dev_AlertDeviceDown = 1                      
                      AND NOT EXISTS (SELECT 1 FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC
                                         ) """)
    mylog('verbose', ['[Scan Stats]        Down Alerts........: ' + str (sql.fetchone()[0]) ])

    # New Down Alerts
    sql.execute ("""SELECT COUNT(*) FROM Devices
                    WHERE dev_AlertDeviceDown = 1
                      AND dev_PresentLastScan = 1                      
                      AND NOT EXISTS (SELECT 1 FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC
                                         ) """)
    mylog('verbose', ['[Scan Stats]        New Down Alerts....: ' + str (sql.fetchone()[0]) ])

    # New Connections
    sql.execute ("""SELECT COUNT(*) FROM Devices, CurrentScan
                    WHERE dev_MAC = cur_MAC  
                      AND dev_PresentLastScan = 0""")                      
    mylog('verbose', ['[Scan Stats]        New Connections....: ' + str ( sql.fetchone()[0]) ])

    # Disconnections
    sql.execute ("""SELECT COUNT(*) FROM Devices
                    WHERE dev_PresentLastScan = 1                      
                      AND NOT EXISTS (SELECT 1 FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC
                                         ) """)
    mylog('verbose', ['[Scan Stats]        Disconnections.....: ' + str ( sql.fetchone()[0]) ])

    # IP Changes
    sql.execute ("""SELECT COUNT(*) FROM Devices, CurrentScan
                    WHERE dev_MAC = cur_MAC                        
                      AND dev_LastIP <> cur_IP """)
    mylog('verbose', ['[Scan Stats]        IP Changes.........: ' + str ( sql.fetchone()[0]) ])



#-------------------------------------------------------------------------------
def create_new_devices (db):
    sql = db.sql # TO-DO
    startTime = timeNowTZ()

    # arpscan - Insert events for new devices
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
                    
    # arpscan - Create new devices
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
    
    sqlQuery = f"""INSERT INTO Devices (dev_MAC, dev_name, dev_Vendor,
                        dev_LastIP, dev_FirstConnection, dev_LastConnection,
                        {newDevColumns})
                    SELECT cur_MAC, '(unknown)', cur_Vendor, cur_IP, ?, ?,
                        {newDevDefaults}
                    FROM CurrentScan
                    WHERE NOT EXISTS (SELECT 1 FROM Devices
                                      WHERE dev_MAC = cur_MAC) """

    mylog('debug',f'[New Devices] 2 Create devices SQL: {sqlQuery}')

    sql.execute (sqlQuery, (startTime, startTime) ) 

    # Pi-hole - Insert events for new devices
    # NOT STRICYLY NECESARY (Devices can be created through Current_Scan)
    # Bugfix #2 - Pi-hole devices w/o IP
    mylog('debug','[New Devices] 3 Pi-hole Events')
    sql.execute ("""INSERT INTO Events (eve_MAC, eve_IP, eve_DateTime,
                        eve_EventType, eve_AdditionalInfo,
                        eve_PendingAlertEmail)
                    SELECT PH_MAC, IFNULL (PH_IP,'-'), ?, 'New Device',
                        '(Pi-Hole) ' || PH_Vendor, 1
                    FROM PiHole_Network
                    WHERE NOT EXISTS (SELECT 1 FROM Devices
                                      WHERE dev_MAC = PH_MAC) """,
                    (startTime, ) ) 

    # Pi-hole - Create New Devices
    # Bugfix #2 - Pi-hole devices w/o IP
    mylog('debug','[New Devices] 4 Pi-hole Create devices')

    sqlQuery = f"""INSERT INTO Devices (dev_MAC, dev_name, dev_Vendor,
                        dev_LastIP, dev_FirstConnection, dev_LastConnection,
                        {newDevColumns})
                    SELECT PH_MAC, PH_Name, PH_Vendor, IFNULL (PH_IP,'-'),
                        ?, ?,
                        {newDevDefaults}
                    FROM PiHole_Network
                    WHERE NOT EXISTS (SELECT 1 FROM Devices
                                      WHERE dev_MAC = PH_MAC) """
    
    mylog('debug',f'[New Devices] 4 Create devices SQL: {sqlQuery}')

    sql.execute (sqlQuery, (startTime, startTime) ) 

    # DHCP Leases - Insert events for new devices
    mylog('debug','[New Devices] 5 DHCP Leases Events')

    sql.execute (f"""INSERT INTO Events (eve_MAC, eve_IP, eve_DateTime,
                        eve_EventType, eve_AdditionalInfo,
                        eve_PendingAlertEmail)
                    SELECT DHCP_MAC, DHCP_IP, '{startTime}', 'New Device', '(DHCP lease)',1
                    FROM DHCP_Leases
                    WHERE NOT EXISTS (SELECT 1 FROM Devices
                                      WHERE dev_MAC = DHCP_MAC) """) 

    # DHCP Leases - Create New Devices
    mylog('debug','[New Devices] 6 DHCP Leases Create devices')

    sqlQuery = f"""INSERT INTO Devices (dev_MAC, dev_name, dev_LastIP, 
                        dev_Vendor, dev_FirstConnection, dev_LastConnection,                        
                        {newDevColumns})
                    SELECT DISTINCT DHCP_MAC,
                        (SELECT DHCP_Name FROM DHCP_Leases AS D2
                         WHERE D2.DHCP_MAC = D1.DHCP_MAC
                         ORDER BY DHCP_DateTime DESC LIMIT 1),
                        (SELECT DHCP_IP FROM DHCP_Leases AS D2
                         WHERE D2.DHCP_MAC = D1.DHCP_MAC
                         ORDER BY DHCP_DateTime DESC LIMIT 1),
                        '(unknown)', ?, ?, 
                        {newDevDefaults}    
                    FROM DHCP_Leases AS D1
                    WHERE NOT EXISTS (SELECT 1 FROM Devices
                                      WHERE dev_MAC = DHCP_MAC) """

    mylog('debug',f'[New Devices] 6 Create devices SQL: {sqlQuery}')

    sql.execute (sqlQuery, (startTime, startTime) ) 

    mylog('debug','[New Devices] New Devices end')
    db.commitDB()


#-------------------------------------------------------------------------------
def update_devices_data_from_scan (db):
    sql = db.sql #TO-DO    
    startTime = timeNowTZ()
    # Update Last Connection
    mylog('debug','[Update Devices] 1 Last Connection')
    sql.execute (f"""UPDATE Devices SET dev_LastConnection = '{startTime}',
                        dev_PresentLastScan = 1
                    WHERE dev_PresentLastScan = 0
                      AND EXISTS (SELECT 1 FROM CurrentScan 
                                  WHERE dev_MAC = cur_MAC) """)

    # Clean no active devices
    mylog('debug','[Update Devices] 2 Clean no active devices')
    sql.execute ("""UPDATE Devices SET dev_PresentLastScan = 0
                    WHERE NOT EXISTS (SELECT 1 FROM CurrentScan 
                                      WHERE dev_MAC = cur_MAC) """)

    # Update IP & Vendor
    mylog('debug','[Update Devices] - 3 LastIP & Vendor')
    sql.execute ("""UPDATE Devices
                    SET dev_LastIP = (SELECT cur_IP FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC),
                        dev_Vendor = (SELECT cur_Vendor FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC
                                        )
                    WHERE EXISTS (SELECT 1 FROM CurrentScan
                                  WHERE dev_MAC = cur_MAC) """) 

    # Pi-hole Network - Update (unknown) Name
    mylog('debug','[Update Devices] - 4 Unknown Name')
    sql.execute ("""UPDATE Devices
                    SET dev_NAME = (SELECT PH_Name FROM PiHole_Network
                                    WHERE PH_MAC = dev_MAC)
                    WHERE (dev_Name in ("(unknown)", "(name not found)", "" )
                           OR dev_Name IS NULL)
                      AND EXISTS (SELECT 1 FROM PiHole_Network
                                  WHERE PH_MAC = dev_MAC
                                    AND PH_NAME IS NOT NULL
                                    AND PH_NAME <> '') """)

    # DHCP Leases - Update (unknown) Name
    sql.execute ("""UPDATE Devices
                    SET dev_NAME = (SELECT DHCP_Name FROM DHCP_Leases
                                    WHERE DHCP_MAC = dev_MAC)
                    WHERE (dev_Name in ("(unknown)", "(name not found)", "" )                           
                           OR dev_Name IS NULL)
                      AND EXISTS (SELECT 1 FROM DHCP_Leases
                                  WHERE DHCP_MAC = dev_MAC)""")

    # DHCP Leases - Vendor
    mylog('debug','[Update Devices] - 5 Vendor')

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

    # clean-up device leases table
    sql.execute ("DELETE FROM DHCP_Leases")
    mylog('debug','[Update Devices] Update devices end')

#-------------------------------------------------------------------------------
def update_devices_names (db):
    sql = db.sql #TO-DO
    # Initialize variables
    recordsToUpdate = []
    recordsNotFound = []

    ignored = 0
    notFound = 0

    foundDig = 0
    foundPholus = 0

    # BUGFIX #97 - Updating name of Devices w/o IP    
    sql.execute ("SELECT * FROM Devices WHERE dev_Name IN ('(unknown)','', '(name not found)') AND dev_LastIP <> '-'")
    unknownDevices = sql.fetchall() 
    db.commitDB()

    # skip checks if no unknown devices
    if len(unknownDevices) == 0 and conf.PHOLUS_FORCE == False:
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
        newName = -1
        
        # Resolve device name with DiG
        newName = resolve_device_name_dig (device['dev_MAC'], device['dev_LastIP'])
        
        # count
        if newName != -1:
            foundDig += 1

        # Resolve with Pholus 
        if newName == -1:
            newName =  resolve_device_name_pholus (device['dev_MAC'], device['dev_LastIP'], pholusResults)
            # count
            if newName != -1:
                foundPholus += 1
        
        # isf still not found update name so we can distinguish the devices where we tried already
        if newName == -1 :
            # if dev_Name is the same as what we will change it to, take no action
            # this mitigates a race condition which would overwrite a users edits that occured since the select earlier
            if device['dev_Name'] != "(name not found)":
                recordsNotFound.append (["(name not found)", device['dev_MAC']])          
        else:
            # name wa sfound with DiG or Pholus
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
