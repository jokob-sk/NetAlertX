

import conf
from arpscan import execute_arpscan
from database import insertOnlineHistory
from device import create_new_devices, print_scan_stats, save_scanned_devices, update_devices_data_from_scan, update_devices_names
from helper import timeNow
from logger import mylog, print_log
from pihole import copy_pihole_network, read_DHCP_leases
from reporting import skip_repeated_notifications



#===============================================================================
# SCAN NETWORK
#===============================================================================


def scan_network (db):
    sql = db.sql #TO-DO
    reporting = False

    # Header
    # moved updateState to main loop
    # updateState(db,"Scan: Network")
    mylog('verbose', ['[', timeNow(), '] Scan Devices:' ])       

    # Query ScanCycle properties    
    scanCycle_data = query_ScanCycle_Data (db, True)
    if scanCycle_data is None:
        mylog('none', ['\n*************** ERROR ***************'])
        mylog('none', ['ScanCycle %s not found' % conf.cycle ])
        mylog('none', ['    Exiting...\n'])
        return False

    db.commitDB()

    # ScanCycle data        
    cycle_interval  = scanCycle_data['cic_EveryXmin']
    
    # arp-scan command
    arpscan_devices = []
    if conf.ENABLE_ARPSCAN:    
        mylog('verbose', ['    arp-scan start'])    
        arpscan_devices = execute_arpscan (conf.userSubnets)
        print_log ('arp-scan ends')

    # Pi-hole method    
    if conf.PIHOLE_ACTIVE :       
        mylog('verbose', ['    Pi-hole start'])        
        copy_pihole_network(db) 
        db.commitDB() 

    # DHCP Leases method    
    if conf.DHCP_ACTIVE :        
        mylog('verbose', ['    DHCP Leases start'])        
        read_DHCP_leases (db) 
        db.commitDB()

    # Load current scan data
    mylog('verbose', ['  Processing scan results'])     
    save_scanned_devices (db, arpscan_devices, cycle_interval)    
    
    # Print stats
    mylog ('none', 'Print Stats')
    print_scan_stats(db)
    mylog ('none', 'Stats end')

    # Create Events
    mylog('verbose', ['  Updating DB Info'])
    mylog('verbose', ['    Sessions Events (connect / discconnect)'])
    insert_events(db)

    # Create New Devices
    # after create events -> avoid 'connection' event
    mylog('verbose', ['    Creating new devices'])
    create_new_devices (db)

    # Update devices info
    mylog('verbose', ['    Updating Devices Info'])
    update_devices_data_from_scan (db)

    # Resolve devices names
    print_log ('    Resolve devices names')
    update_devices_names(db)

    # Void false connection - disconnections
    mylog('verbose', ['    Voiding false (ghost) disconnections'])    
    void_ghost_disconnections (db)

    # Pair session events (Connection / Disconnection)
    mylog('verbose', ['    Pairing session events (connection / disconnection) '])
    pair_sessions_events(db)  
  
    # Sessions snapshot
    mylog('verbose', ['    Creating sessions snapshot'])
    create_sessions_snapshot (db)

    # Sessions snapshot
    mylog('verbose', ['    Inserting scan results into Online_History'])
    insertOnlineHistory(db,conf.cycle)
  
    # Skip repeated notifications
    mylog('verbose', ['    Skipping repeated notifications'])
    skip_repeated_notifications (db)
  
    # Commit changes    
    db.commitDB()

    # moved plugin execution to main loop
    # if ENABLE_PLUGINS:
    #    run_plugin_scripts(db,'always_after_scan')

    return reporting

#-------------------------------------------------------------------------------
def query_ScanCycle_Data (db, pOpenCloseDB = False, cycle = 1):
    # Query Data
    db.sql.execute ("""SELECT cic_arpscanCycles, cic_EveryXmin
                    FROM ScanCycles
                    WHERE cic_ID = ? """, (cycle,))
    sqlRow = db.sql.fetchone()

    # Return Row
    return sqlRow



#-------------------------------------------------------------------------------
def void_ghost_disconnections (db):
    sql = db.sql #TO-DO
    startTime = timeNow()
    # Void connect ghost events (disconnect event exists in last X min.) 
    print_log ('Void - 1 Connect ghost events')
    sql.execute ("""UPDATE Events SET eve_PairEventRowid = Null,
                        eve_EventType ='VOIDED - ' || eve_EventType
                    WHERE eve_MAC != 'Internet'
                      AND eve_EventType = 'Connected'
                      AND eve_DateTime = ?
                      AND eve_MAC IN (
                          SELECT Events.eve_MAC
                          FROM CurrentScan, Devices, ScanCycles, Events 
                          WHERE cur_ScanCycle = ?
                            AND dev_MAC = cur_MAC
                            AND dev_ScanCycle = cic_ID
                            AND cic_ID = cur_ScanCycle
                            AND eve_MAC = cur_MAC
                            AND eve_EventType = 'Disconnected'
                            AND eve_DateTime >=
                                DATETIME (?, '-' || cic_EveryXmin ||' minutes')
                          ) """,
                    (startTime, conf.cycle, startTime)   )

    # Void connect paired events
    print_log ('Void - 2 Paired events')
    sql.execute ("""UPDATE Events SET eve_PairEventRowid = Null 
                    WHERE eve_MAC != 'Internet'
                      AND eve_PairEventRowid IN (
                          SELECT Events.RowID
                          FROM CurrentScan, Devices, ScanCycles, Events 
                          WHERE cur_ScanCycle = ?
                            AND dev_MAC = cur_MAC
                            AND dev_ScanCycle = cic_ID
                            AND cic_ID = cur_ScanCycle
                            AND eve_MAC = cur_MAC
                            AND eve_EventType = 'Disconnected'
                            AND eve_DateTime >=
                                DATETIME (?, '-' || cic_EveryXmin ||' minutes')
                          ) """,
                    (conf.cycle, startTime)   )

    # Void disconnect ghost events 
    print_log ('Void - 3 Disconnect ghost events')
    sql.execute ("""UPDATE Events SET eve_PairEventRowid = Null, 
                        eve_EventType = 'VOIDED - '|| eve_EventType
                    WHERE eve_MAC != 'Internet'
                      AND ROWID IN (
                          SELECT Events.RowID
                          FROM CurrentScan, Devices, ScanCycles, Events 
                          WHERE cur_ScanCycle = ?
                            AND dev_MAC = cur_MAC
                            AND dev_ScanCycle = cic_ID
                            AND cic_ID = cur_ScanCycle
                            AND eve_MAC = cur_MAC
                            AND eve_EventType = 'Disconnected'
                            AND eve_DateTime >=
                                DATETIME (?, '-' || cic_EveryXmin ||' minutes')
                          ) """,
                    (conf.cycle, startTime)   )
    print_log ('Void end')
    db.commitDB()

#-------------------------------------------------------------------------------
def pair_sessions_events (db):
    sql = db.sql #TO-DO

    # NOT NECESSARY FOR INCREMENTAL UPDATE
    # print_log ('Pair session - 1 Clean')
    # sql.execute ("""UPDATE Events
    #                 SET eve_PairEventRowid = NULL
    #                 WHERE eve_EventType IN ('New Device', 'Connected')
    #              """ )
    

    # Pair Connection / New Device events
    print_log ('Pair session - 1 Connections / New Devices')
    sql.execute ("""UPDATE Events
                    SET eve_PairEventRowid =
                       (SELECT ROWID
                        FROM Events AS EVE2
                        WHERE EVE2.eve_EventType IN ('New Device', 'Connected',
                            'Device Down', 'Disconnected')
                           AND EVE2.eve_MAC = Events.eve_MAC
                           AND EVE2.eve_Datetime > Events.eve_DateTime
                        ORDER BY EVE2.eve_DateTime ASC LIMIT 1)
                    WHERE eve_EventType IN ('New Device', 'Connected')
                    AND eve_PairEventRowid IS NULL
                 """ )

    # Pair Disconnection / Device Down
    print_log ('Pair session - 2 Disconnections')
    sql.execute ("""UPDATE Events
                    SET eve_PairEventRowid =
                        (SELECT ROWID
                         FROM Events AS EVE2
                         WHERE EVE2.eve_PairEventRowid = Events.ROWID)
                    WHERE eve_EventType IN ('Device Down', 'Disconnected')
                      AND eve_PairEventRowid IS NULL
                 """ )
    print_log ('Pair session end')

    db.commitDB()

#-------------------------------------------------------------------------------
def create_sessions_snapshot (db):
    sql = db.sql #TO-DO

    # Clean sessions snapshot
    print_log ('Sessions Snapshot - 1 Clean')
    sql.execute ("DELETE FROM SESSIONS" )

    # Insert sessions
    print_log ('Sessions Snapshot - 2 Insert')
    sql.execute ("""INSERT INTO Sessions
                    SELECT * FROM Convert_Events_to_Sessions""" )

    print_log ('Sessions end')
    db.commitDB()


#-------------------------------------------------------------------------------
def insert_events (db):
    sql = db.sql #TO-DO
    startTime = timeNow()    
    
    # Check device down
    print_log ('Events 1 - Devices down')
    sql.execute ("""INSERT INTO Events (eve_MAC, eve_IP, eve_DateTime,
                        eve_EventType, eve_AdditionalInfo,
                        eve_PendingAlertEmail)
                    SELECT dev_MAC, dev_LastIP, ?, 'Device Down', '', 1
                    FROM Devices
                    WHERE dev_AlertDeviceDown = 1
                      AND dev_PresentLastScan = 1
                      AND dev_ScanCycle = ?
                      AND NOT EXISTS (SELECT 1 FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC
                                        AND dev_ScanCycle = cur_ScanCycle) """,
                    (startTime, conf.cycle) )

    # Check new connections
    print_log ('Events 2 - New Connections')
    sql.execute ("""INSERT INTO Events (eve_MAC, eve_IP, eve_DateTime,
                        eve_EventType, eve_AdditionalInfo,
                        eve_PendingAlertEmail)
                    SELECT cur_MAC, cur_IP, ?, 'Connected', '', dev_AlertEvents
                    FROM Devices, CurrentScan
                    WHERE dev_MAC = cur_MAC AND dev_ScanCycle = cur_ScanCycle
                      AND dev_PresentLastScan = 0
                      AND dev_ScanCycle = ? """,
                    (startTime, conf.cycle) )

    # Check disconnections
    print_log ('Events 3 - Disconnections')
    sql.execute ("""INSERT INTO Events (eve_MAC, eve_IP, eve_DateTime,
                        eve_EventType, eve_AdditionalInfo,
                        eve_PendingAlertEmail)
                    SELECT dev_MAC, dev_LastIP, ?, 'Disconnected', '',
                        dev_AlertEvents
                    FROM Devices
                    WHERE dev_AlertDeviceDown = 0
                      AND dev_PresentLastScan = 1
                      AND dev_ScanCycle = ?
                      AND NOT EXISTS (SELECT 1 FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC
                                        AND dev_ScanCycle = cur_ScanCycle) """,
                    (startTime, conf.cycle) )

    # Check IP Changed
    print_log ('Events 4 - IP Changes')
    sql.execute ("""INSERT INTO Events (eve_MAC, eve_IP, eve_DateTime,
                        eve_EventType, eve_AdditionalInfo,
                        eve_PendingAlertEmail)
                    SELECT cur_MAC, cur_IP, ?, 'IP Changed',
                        'Previous IP: '|| dev_LastIP, dev_AlertEvents
                    FROM Devices, CurrentScan
                    WHERE dev_MAC = cur_MAC AND dev_ScanCycle = cur_ScanCycle
                      AND dev_ScanCycle = ?
                      AND dev_LastIP <> cur_IP """,
                    (startTime, conf.cycle) )
    print_log ('Events end')


