#!/usr/bin/env python
#
#-------------------------------------------------------------------------------
#  Pi.Alert  v2.70  /  2021-02-01
#  Open Source Network Guard / WIFI & LAN intrusion detector 
#
#  pialert.py - Back module. Network scanner
#-------------------------------------------------------------------------------
#  Puche 2021 / 2022+ jokob             jokob@duck.com                GNU GPLv3
#-------------------------------------------------------------------------------


#===============================================================================
# IMPORTS
#===============================================================================
from __future__ import print_function
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import sys
from collections import namedtuple
import subprocess
import os
import re
import time
import decimal
import datetime
from datetime import timedelta
import sqlite3
import socket
import io
import smtplib
import csv
import json
import requests
from base64 import b64encode
from paho.mqtt import client as mqtt_client
import threading
from pathlib import Path
from cron_converter import Cron

from json2table import convert
import hashlib
import multiprocessing


# pialert modules
from const import *
from conf import *
# from config import DIG_GET_IP_ARG, ENABLE_PLUGINS
from logger import append_line_to_file, mylog, print_log, logResult
from helper import   bytes_to_string, checkIPV4, filePermissions,  importConfigs, timeNow, updateSubnets, write_file
from database import *
from internet import check_IP_format, check_internet_IP, get_internet_IP
from api import update_api
from files import get_file_content
from plugin import execute_plugin, get_plugin_setting, plugin_object_class, print_plugin_info 




# Global variables

debug_force_notification = False

userSubnets = []
changedPorts_json_struc = None
time_started = datetime.datetime.now()
cron_instance = Cron()
log_timestamp = time_started
lastTimeImported = 0
sql_connection = None




#===============================================================================
#===============================================================================
#                              MAIN
#===============================================================================
#===============================================================================
cycle = ""
check_report = [1, "internet_IP", "update_vendors_silent"]
plugins_once_run = False

# timestamps of last execution times
startTime = time_started
now_minus_24h = time_started - datetime.timedelta(hours = 24)

last_network_scan = now_minus_24h
last_internet_IP_scan = now_minus_24h
last_run = now_minus_24h
last_cleanup = now_minus_24h
last_update_vendors = time_started - datetime.timedelta(days = 6) # update vendors 24h after first run and then once a week

# indicates, if a new version is available
newVersionAvailable = False

def main ():
    # Initialize global variables
    global time_started, cycle, last_network_scan, last_internet_IP_scan, last_run, last_cleanup, last_update_vendors
    # second set of global variables
    global startTime, log_timestamp, plugins_once_run 

    # To-Do all these DB Globals need to be removed
    global db, sql, sql_connection

    # check file permissions and fix if required
    filePermissions()

    # Open DB once and keep open
    # Opening / closing DB frequently actually casues more issues
    db = DB()  # instance of class DB
    db.openDB()

    # To-Do replace the following to lines with the db class
    sql_connection = db.sql_connection
    sql = db.sql

    # Upgrade DB if needed
    upgradeDB(db)


    #===============================================================================
    # This is the main loop of Pi.Alert 
    #===============================================================================

    while True:

        # update time started
        time_started = datetime.datetime.now()
        mylog('debug', ['[', timeNow(), '] [MAIN] Stating loop'])

        # re-load user configuration and plugins
        importConfigs(db)       
        
        # Handle plugins executed ONCE
        if ENABLE_PLUGINS and plugins_once_run == False:
            run_plugin_scripts(db, 'once')  
            plugins_once_run = True

        # check if there is a front end initiated event which needs to be executed
        check_and_run_event(db)

        # Update API endpoints              
        update_api()
        
        # proceed if 1 minute passed
        if last_run + datetime.timedelta(minutes=1) < time_started :

             # last time any scan or maintenance/upkeep was run
            last_run = time_started

            # Header
            updateState(db,"Process: Start")      

            # Timestamp
            startTime = time_started
            startTime = startTime.replace (microsecond=0) 

            # Check if any plugins need to run on schedule
            if ENABLE_PLUGINS:
                run_plugin_scripts(db,'schedule') 

            # determine run/scan type based on passed time
            # --------------------------------------------

            # check for changes in Internet IP
            if last_internet_IP_scan + datetime.timedelta(minutes=3) < time_started:
                cycle = 'internet_IP'                
                last_internet_IP_scan = time_started
                check_internet_IP(db,DIG_GET_IP_ARG)

            # Update vendors once a week
            if last_update_vendors + datetime.timedelta(days = 7) < time_started:
                last_update_vendors = time_started
                cycle = 'update_vendors'
                mylog('verbose', ['[', timeNow(), '] cycle:',cycle])                  
                update_devices_MAC_vendors()

            # Execute scheduled or one-off Pholus scan if enabled and run conditions fulfilled
            if PHOLUS_RUN == "schedule" or PHOLUS_RUN == "once":

                pholusSchedule = [sch for sch in mySchedules if sch.service == "pholus"][0]
                run = False

                # run once after application starts
                if PHOLUS_RUN == "once" and pholusSchedule.last_run == 0:
                    run = True

                # run if overdue scheduled time
                if PHOLUS_RUN == "schedule":
                    run = pholusSchedule.runScheduleCheck()                    

                if run:
                    pholusSchedule.last_run = datetime.datetime.now(tz).replace(microsecond=0)
                    performPholusScan(db, PHOLUS_RUN_TIMEOUT)
            
            # Execute scheduled or one-off Nmap scan if enabled and run conditions fulfilled
            if NMAP_RUN == "schedule" or NMAP_RUN == "once":

                nmapSchedule = [sch for sch in mySchedules if sch.service == "nmap"][0]
                run = False

                # run once after application starts
                if NMAP_RUN == "once" and nmapSchedule.last_run == 0:
                    run = True

                # run if overdue scheduled time
                if NMAP_RUN == "schedule":
                    run = nmapSchedule.runScheduleCheck()                    

                if run:
                    nmapSchedule.last_run = datetime.datetime.now(tz).replace(microsecond=0)
                    performNmapScan(get_all_devices())
            
            # Perform a network scan via arp-scan or pihole
            if last_network_scan + datetime.timedelta(minutes=SCAN_CYCLE_MINUTES) < time_started:
                last_network_scan = time_started
                cycle = 1 # network scan
                mylog('verbose', ['[', timeNow(), '] cycle:',cycle])
    
                # scan_network() 

                #  DEBUG start ++++++++++++++++++++++++++++++++++++++++++++++++++++++
                # Start scan_network as a process                

                p = multiprocessing.Process(target=scan_network)
                p.start()

                # Wait for 3600 seconds (max 1h) or until process finishes
                p.join(3600)

                # If thread is still active
                if p.is_alive():
                    print("DEBUG scan_network running too long - let\'s kill it")
                    mylog('info', ['    DEBUG scan_network running too long - let\'s kill it'])

                    # Terminate - may not work if process is stuck for good
                    p.terminate()
                    # OR Kill - will work for sure, no chance for process to finish nicely however
                    # p.kill()

                    p.join()

                #  DEBUG end ++++++++++++++++++++++++++++++++++++++++++++++++++++++
                
            
            # Reporting   
            if cycle in check_report:
                # Check if new devices found
                sql.execute (sql_new_devices)
                newDevices = sql.fetchall()
                db.commitDB()
                
                #  new devices were found
                if len(newDevices) > 0:
                    #  run all plugins registered to be run when new devices are found
                    if ENABLE_PLUGINS:
                        run_plugin_scripts(db, 'on_new_device')

                    #  Scan newly found devices with Nmap if enabled
                    if NMAP_ACTIVE and len(newDevices) > 0:
                        performNmapScan( newDevices)

                # send all configured notifications
                send_notifications(db)

            # clean up the DB once a day
            if last_cleanup + datetime.timedelta(hours = 24) < time_started:
                last_cleanup = time_started
                cycle = 'cleanup'  
                mylog('verbose', ['[', timeNow(), '] cycle:',cycle])
                db.cleanup_database(startTime, DAYS_TO_KEEP_EVENTS, PHOLUS_DAYS_DATA)   

            # Commit SQL
            db.commitDB()          
            
            # Final message
            if cycle != "":
                action = str(cycle)
                if action == "1":
                    action = "network_scan"
                mylog('verbose', ['[', timeNow(), '] Last action: ', action])
                cycle = ""
                mylog('verbose', ['[', timeNow(), '] cycle:',cycle])
            
            # Footer
            updateState(db,"Process: Wait")
            mylog('verbose', ['[', timeNow(), '] Process: Wait'])            
        else:
            # do something
            cycle = "" 
            mylog('verbose', ['[', timeNow(), '] [MAIN] waiting to start next loop'])          

        #loop     
        time.sleep(5) # wait for N seconds      





#===============================================================================
# UPDATE DEVICE MAC VENDORS
#===============================================================================
def update_devices_MAC_vendors (db, pArg = ''):
    # Header    
    updateState(db,"Upkeep: Vendors")
    mylog('verbose', ['[', startTime, '] Upkeep - Update HW Vendors:' ])

    # Update vendors DB (iab oui)
    mylog('verbose', ['    Updating vendors DB (iab & oui)'])    
    update_args = ['sh', pialertPath + '/update_vendors.sh', pArg]

    try:
        # try runnning a subprocess
        update_output = subprocess.check_output (update_args)
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        mylog('none', ['    FAILED: Updating vendors DB, set LOG_LEVEL=debug for more info'])  
        mylog('none', [e.output])        

    # Initialize variables
    recordsToUpdate = []
    ignored = 0
    notFound = 0

    # All devices loop
    mylog('verbose', ['    Searching devices vendor'])    
    for device in sql.execute ("""SELECT * FROM Devices
                                  WHERE dev_Vendor = '(unknown)' 
                                     OR dev_Vendor =''
                                     OR dev_Vendor IS NULL""") :
        # Search vendor in HW Vendors DB
        vendor = query_MAC_vendor (device['dev_MAC'])
        if vendor == -1 :
            notFound += 1
        elif vendor == -2 :
            ignored += 1
        else :
            recordsToUpdate.append ([vendor, device['dev_MAC']])
            
    # Print log    
    mylog('verbose', ["    Devices Ignored:  ", ignored])
    mylog('verbose', ["    Vendors Not Found:", notFound])
    mylog('verbose', ["    Vendors updated:  ", len(recordsToUpdate) ])


    # update devices
    sql.executemany ("UPDATE Devices SET dev_Vendor = ? WHERE dev_MAC = ? ",
        recordsToUpdate )

    # Commit DB
    db.commitDB()

    if len(recordsToUpdate) > 0:
        return True
    else:
        return False

#-------------------------------------------------------------------------------
def query_MAC_vendor (pMAC):
    try :
        # BUGFIX #6 - Fix pMAC parameter as numbers
        pMACstr = str(pMAC)
        
        # Check MAC parameter
        mac = pMACstr.replace (':','')
        if len(pMACstr) != 17 or len(mac) != 12 :
            return -2

        # Search vendor in HW Vendors DB
        mac = mac[0:6]
        grep_args = ['grep', '-i', mac, vendorsDB]
        # Execute command
        try:
            # try runnning a subprocess
            grep_output = subprocess.check_output (grep_args)
        except subprocess.CalledProcessError as e:
            # An error occured, handle it
            mylog('none', [e.output])
            grep_output = "       There was an error, check logs for details"

        # Return Vendor
        vendor = grep_output[7:]
        vendor = vendor.rstrip()
        return vendor

    # not Found
    except subprocess.CalledProcessError :
        return -1
            
#===============================================================================
# SCAN NETWORK
#===============================================================================
def scan_network ():
    reporting = False

    # Header
    updateState(db,"Scan: Network")
    mylog('verbose', ['[', startTime, '] Scan Devices:' ])       

    # Query ScanCycle properties    
    scanCycle_data = query_ScanCycle_Data (True)
    if scanCycle_data is None:
        mylog('none', ['\n*************** ERROR ***************'])
        mylog('none', ['ScanCycle %s not found' % cycle ])
        mylog('none', ['    Exiting...\n'])
        return False

    db.commitDB()

    # ScanCycle data        
    cycle_interval  = scanCycle_data['cic_EveryXmin']
    
    # arp-scan command
    arpscan_devices = []
    if ENABLE_ARPSCAN:    
        mylog('verbose', ['    arp-scan start'])    
        arpscan_devices = execute_arpscan ()
        print_log ('arp-scan ends')

    # Pi-hole method    
    if PIHOLE_ACTIVE :       
        mylog('verbose', ['    Pi-hole start'])        
        copy_pihole_network() 
        db.commitDB() 

    # DHCP Leases method    
    if DHCP_ACTIVE :        
        mylog('verbose', ['    DHCP Leases start'])        
        read_DHCP_leases () 
        db.commitDB()

    # Load current scan data
    mylog('verbose', ['  Processing scan results'])     
    save_scanned_devices (arpscan_devices, cycle_interval)    
    
    # Print stats
    print_log ('Print Stats')
    print_scan_stats()
    print_log ('Stats end')

    # Create Events
    mylog('verbose', ['  Updating DB Info'])
    mylog('verbose', ['    Sessions Events (connect / discconnect)'])
    insert_events()

    # Create New Devices
    # after create events -> avoid 'connection' event
    mylog('verbose', ['    Creating new devices'])
    create_new_devices ()

    # Update devices info
    mylog('verbose', ['    Updating Devices Info'])
    update_devices_data_from_scan ()

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
    insertOnlineHistory()
  
    # Skip repeated notifications
    mylog('verbose', ['    Skipping repeated notifications'])
    skip_repeated_notifications (db)
  
    # Commit changes    
    db.commitDB()

    # Run splugin scripts which are set to run every timne after a scan finished
    if ENABLE_PLUGINS:
        run_plugin_scripts(db,'always_after_scan')

    return reporting

#-------------------------------------------------------------------------------
def query_ScanCycle_Data (pOpenCloseDB = False, cycle = 1):
    # Query Data
    sql.execute ("""SELECT cic_arpscanCycles, cic_EveryXmin
                    FROM ScanCycles
                    WHERE cic_ID = ? """, (cycle,))
    sqlRow = sql.fetchone()

    # Return Row
    return sqlRow

#-------------------------------------------------------------------------------
def execute_arpscan ():

    # output of possible multiple interfaces
    arpscan_output = ""

    # scan each interface
    for interface in userSubnets :            
        arpscan_output += execute_arpscan_on_interface (interface)    
    
    # Search IP + MAC + Vendor as regular expresion
    re_ip = r'(?P<ip>((2[0-5]|1[0-9]|[0-9])?[0-9]\.){3}((2[0-5]|1[0-9]|[0-9])?[0-9]))'
    re_mac = r'(?P<mac>([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2}))'
    re_hw = r'(?P<hw>.*)'
    re_pattern = re.compile (re_ip + '\s+' + re_mac + '\s' + re_hw)

    # Create Userdict of devices
    devices_list = [device.groupdict()
        for device in re.finditer (re_pattern, arpscan_output)]
    
    # Delete duplicate MAC
    unique_mac = [] 
    unique_devices = [] 

    for device in devices_list :
        if device['mac'] not in unique_mac: 
            unique_mac.append(device['mac'])
            unique_devices.append(device)    

    # return list
    return unique_devices

#-------------------------------------------------------------------------------
def execute_arpscan_on_interface (interface):    
    # Prepare command arguments
    subnets = interface.strip().split()
    # Retry is 6 to avoid false offline devices
    arpscan_args = ['sudo', 'arp-scan', '--ignoredups', '--retry=6'] + subnets

    # Execute command
    try:
        # try runnning a subprocess
        result = subprocess.check_output (arpscan_args, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        mylog('none', [e.output])
        result = ""

    return result

#-------------------------------------------------------------------------------
def copy_pihole_network ():

    # Open Pi-hole DB
    sql.execute ("ATTACH DATABASE '"+ piholeDB +"' AS PH")

    # Copy Pi-hole Network table
    sql.execute ("DELETE FROM PiHole_Network")
    sql.execute ("""INSERT INTO PiHole_Network (PH_MAC, PH_Vendor, PH_LastQuery,
                        PH_Name, PH_IP)
                    SELECT hwaddr, macVendor, lastQuery,
                        (SELECT name FROM PH.network_addresses
                         WHERE network_id = id ORDER BY lastseen DESC, ip),
                        (SELECT ip FROM PH.network_addresses
                         WHERE network_id = id ORDER BY lastseen DESC, ip)
                    FROM PH.network
                    WHERE hwaddr NOT LIKE 'ip-%'
                      AND hwaddr <> '00:00:00:00:00:00' """)
    sql.execute ("""UPDATE PiHole_Network SET PH_Name = '(unknown)'
                    WHERE PH_Name IS NULL OR PH_Name = '' """)
    # Close Pi-hole DB
    sql.execute ("DETACH PH")

    return str(sql.rowcount) != "0"

#-------------------------------------------------------------------------------
def read_DHCP_leases ():
    # Read DHCP Leases
    # Bugfix #1 - dhcp.leases: lines with different number of columns (5 col)
    data = []
    with open(piholeDhcpleases, 'r') as f:
        for line in f:
            reporting = True
            row = line.rstrip().split()
            if len(row) == 5 :
                data.append (row)

    # Insert into PiAlert table    
    sql.executemany ("""INSERT INTO DHCP_Leases (DHCP_DateTime, DHCP_MAC,
                            DHCP_IP, DHCP_Name, DHCP_MAC2)
                        VALUES (?, ?, ?, ?, ?)
                     """, data)

    

#-------------------------------------------------------------------------------
def save_scanned_devices (p_arpscan_devices, p_cycle_interval):
    cycle = 1 # always 1, only one cycle supported

    # Delete previous scan data
    sql.execute ("DELETE FROM CurrentScan WHERE cur_ScanCycle = ?",
                (cycle,))

    if len(p_arpscan_devices) > 0:
        # Insert new arp-scan devices
        sql.executemany ("INSERT INTO CurrentScan (cur_ScanCycle, cur_MAC, "+
                        "    cur_IP, cur_Vendor, cur_ScanMethod) "+
                        "VALUES ("+ str(cycle) + ", :mac, :ip, :hw, 'arp-scan')",
                        p_arpscan_devices) 

    # Insert Pi-hole devices
    sql.execute ("""INSERT INTO CurrentScan (cur_ScanCycle, cur_MAC, 
                        cur_IP, cur_Vendor, cur_ScanMethod)
                    SELECT ?, PH_MAC, PH_IP, PH_Vendor, 'Pi-hole'
                    FROM PiHole_Network
                    WHERE PH_LastQuery >= ?
                      AND NOT EXISTS (SELECT 'X' FROM CurrentScan
                                      WHERE cur_MAC = PH_MAC
                                        AND cur_ScanCycle = ? )""",
                    (cycle,
                     (int(startTime.strftime('%s')) - 60 * p_cycle_interval),
                     cycle) )

    # Check Internet connectivity
    internet_IP = get_internet_IP(DIG_GET_IP_ARG)
        # TESTING - Force IP
        # internet_IP = ""
    if internet_IP != "" :
        sql.execute ("""INSERT INTO CurrentScan (cur_ScanCycle, cur_MAC, cur_IP, cur_Vendor, cur_ScanMethod)
                        VALUES (?, 'Internet', ?, Null, 'queryDNS') """, (cycle, internet_IP) )

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

    mylog('debug', ['    Saving this IP into the CurrentScan table:', local_ip])

    if check_IP_format(local_ip) == '':
        local_ip = '0.0.0.0'

    # Check if local mac has been detected with other methods
    sql.execute ("SELECT COUNT(*) FROM CurrentScan WHERE cur_ScanCycle = ? AND cur_MAC = ? ", (cycle, local_mac) )
    if sql.fetchone()[0] == 0 :
        sql.execute ("INSERT INTO CurrentScan (cur_ScanCycle, cur_MAC, cur_IP, cur_Vendor, cur_ScanMethod) "+
                     "VALUES ( ?, ?, ?, Null, 'local_MAC') ", (cycle, local_mac, local_ip) )

#-------------------------------------------------------------------------------
def print_scan_stats ():
    # Devices Detected
    sql.execute ("""SELECT COUNT(*) FROM CurrentScan
                    WHERE cur_ScanCycle = ? """,
                    (cycle,))
    mylog('verbose', ['    Devices Detected.......: ', str (sql.fetchone()[0]) ])

    # Devices arp-scan
    sql.execute ("""SELECT COUNT(*) FROM CurrentScan
                    WHERE cur_ScanMethod='arp-scan' AND cur_ScanCycle = ? """,
                    (cycle,))
    mylog('verbose', ['        arp-scan detected..: ', str (sql.fetchone()[0]) ])

    # Devices Pi-hole
    sql.execute ("""SELECT COUNT(*) FROM CurrentScan
                    WHERE cur_ScanMethod='PiHole' AND cur_ScanCycle = ? """,
                    (cycle,))
    mylog('verbose', ['        Pi-hole detected...: +' + str (sql.fetchone()[0]) ])

    # New Devices
    sql.execute ("""SELECT COUNT(*) FROM CurrentScan
                    WHERE cur_ScanCycle = ? 
                      AND NOT EXISTS (SELECT 1 FROM Devices
                                      WHERE dev_MAC = cur_MAC) """,
                    (cycle,))
    mylog('verbose', ['        New Devices........: ' + str (sql.fetchone()[0]) ])

    # Devices in this ScanCycle
    sql.execute ("""SELECT COUNT(*) FROM Devices, CurrentScan
                    WHERE dev_MAC = cur_MAC AND dev_ScanCycle = cur_ScanCycle
                      AND dev_ScanCycle = ? """,
                    (cycle,))
    
    mylog('verbose', ['    Devices in this cycle..: ' + str (sql.fetchone()[0]) ])

    # Down Alerts
    sql.execute ("""SELECT COUNT(*) FROM Devices
                    WHERE dev_AlertDeviceDown = 1
                      AND dev_ScanCycle = ?
                      AND NOT EXISTS (SELECT 1 FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC
                                        AND dev_ScanCycle = cur_ScanCycle) """,
                    (cycle,))
    mylog('verbose', ['        Down Alerts........: ' + str (sql.fetchone()[0]) ])

    # New Down Alerts
    sql.execute ("""SELECT COUNT(*) FROM Devices
                    WHERE dev_AlertDeviceDown = 1
                      AND dev_PresentLastScan = 1
                      AND dev_ScanCycle = ?
                      AND NOT EXISTS (SELECT 1 FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC
                                        AND dev_ScanCycle = cur_ScanCycle) """,
                    (cycle,))
    mylog('verbose', ['        New Down Alerts....: ' + str (sql.fetchone()[0]) ])

    # New Connections
    sql.execute ("""SELECT COUNT(*) FROM Devices, CurrentScan
                    WHERE dev_MAC = cur_MAC AND dev_ScanCycle = cur_ScanCycle
                      AND dev_PresentLastScan = 0
                      AND dev_ScanCycle = ? """,
                    (cycle,))
    mylog('verbose', ['        New Connections....: ' + str ( sql.fetchone()[0]) ])

    # Disconnections
    sql.execute ("""SELECT COUNT(*) FROM Devices
                    WHERE dev_PresentLastScan = 1
                      AND dev_ScanCycle = ?
                      AND NOT EXISTS (SELECT 1 FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC
                                        AND dev_ScanCycle = cur_ScanCycle) """,
                    (cycle,))
    mylog('verbose', ['        Disconnections.....: ' + str ( sql.fetchone()[0]) ])

    # IP Changes
    sql.execute ("""SELECT COUNT(*) FROM Devices, CurrentScan
                    WHERE dev_MAC = cur_MAC AND dev_ScanCycle = cur_ScanCycle
                      AND dev_ScanCycle = ?
                      AND dev_LastIP <> cur_IP """,
                    (cycle,))
    mylog('verbose', ['        IP Changes.........: ' + str ( sql.fetchone()[0]) ])

#-------------------------------------------------------------------------------
def insertOnlineHistory():
    # Add to History
    sql.execute("SELECT * FROM Devices")
    History_All = sql.fetchall()
    History_All_Devices  = len(History_All)

    sql.execute("SELECT * FROM Devices WHERE dev_Archived = 1")
    History_Archived = sql.fetchall()
    History_Archived_Devices  = len(History_Archived)

    sql.execute("""SELECT * FROM CurrentScan WHERE cur_ScanCycle = ? """, (cycle,))
    History_Online = sql.fetchall()
    History_Online_Devices  = len(History_Online)
    History_Offline_Devices = History_All_Devices - History_Archived_Devices - History_Online_Devices
    
    sql.execute ("INSERT INTO Online_History (Scan_Date, Online_Devices, Down_Devices, All_Devices, Archived_Devices) "+
                 "VALUES ( ?, ?, ?, ?, ?)", (startTime, History_Online_Devices, History_Offline_Devices, History_All_Devices, History_Archived_Devices ) )

#-------------------------------------------------------------------------------
def create_new_devices ():
    # arpscan - Insert events for new devices
    print_log ('New devices - 1 Events')
    sql.execute ("""INSERT INTO Events (eve_MAC, eve_IP, eve_DateTime,
                        eve_EventType, eve_AdditionalInfo,
                        eve_PendingAlertEmail)
                    SELECT cur_MAC, cur_IP, ?, 'New Device', cur_Vendor, 1
                    FROM CurrentScan
                    WHERE cur_ScanCycle = ? 
                      AND NOT EXISTS (SELECT 1 FROM Devices
                                      WHERE dev_MAC = cur_MAC) """,
                    (startTime, cycle) ) 

    print_log ('New devices - Insert Connection into session table')
    sql.execute ("""INSERT INTO Sessions (ses_MAC, ses_IP, ses_EventTypeConnection, ses_DateTimeConnection,
                        ses_EventTypeDisconnection, ses_DateTimeDisconnection, ses_StillConnected, ses_AdditionalInfo)
                    SELECT cur_MAC, cur_IP,'Connected',?, NULL , NULL ,1, cur_Vendor
                    FROM CurrentScan 
                    WHERE cur_ScanCycle = ? 
                      AND NOT EXISTS (SELECT 1 FROM Sessions
                                      WHERE ses_MAC = cur_MAC) """,
                    (startTime, cycle) ) 
                    
    # arpscan - Create new devices
    print_log ('New devices - 2 Create devices')
    sql.execute ("""INSERT INTO Devices (dev_MAC, dev_name, dev_Vendor,
                        dev_LastIP, dev_FirstConnection, dev_LastConnection,
                        dev_ScanCycle, dev_AlertEvents, dev_AlertDeviceDown,
                        dev_PresentLastScan)
                    SELECT cur_MAC, '(unknown)', cur_Vendor, cur_IP, ?, ?,
                        1, 1, 0, 1
                    FROM CurrentScan
                    WHERE cur_ScanCycle = ? 
                      AND NOT EXISTS (SELECT 1 FROM Devices
                                      WHERE dev_MAC = cur_MAC) """,
                    (startTime, startTime, cycle) ) 

    # Pi-hole - Insert events for new devices
    # NOT STRICYLY NECESARY (Devices can be created through Current_Scan)
    # Bugfix #2 - Pi-hole devices w/o IP
    print_log ('New devices - 3 Pi-hole Events')
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
    print_log ('New devices - 4 Pi-hole Create devices')
    sql.execute ("""INSERT INTO Devices (dev_MAC, dev_name, dev_Vendor,
                        dev_LastIP, dev_FirstConnection, dev_LastConnection,
                        dev_ScanCycle, dev_AlertEvents, dev_AlertDeviceDown,
                        dev_PresentLastScan)
                    SELECT PH_MAC, PH_Name, PH_Vendor, IFNULL (PH_IP,'-'),
                        ?, ?, 1, 1, 0, 1
                    FROM PiHole_Network
                    WHERE NOT EXISTS (SELECT 1 FROM Devices
                                      WHERE dev_MAC = PH_MAC) """,
                    (startTime, startTime) ) 

    # DHCP Leases - Insert events for new devices
    print_log ('New devices - 5 DHCP Leases Events')
    sql.execute ("""INSERT INTO Events (eve_MAC, eve_IP, eve_DateTime,
                        eve_EventType, eve_AdditionalInfo,
                        eve_PendingAlertEmail)
                    SELECT DHCP_MAC, DHCP_IP, ?, 'New Device', '(DHCP lease)',1
                    FROM DHCP_Leases
                    WHERE NOT EXISTS (SELECT 1 FROM Devices
                                      WHERE dev_MAC = DHCP_MAC) """,
                    (startTime, ) ) 

    # DHCP Leases - Create New Devices
    print_log ('New devices - 6 DHCP Leases Create devices')
    # BUGFIX #23 - Duplicated MAC in DHCP.Leases
    # TEST - Force Duplicated MAC
        # sql.execute ("""INSERT INTO DHCP_Leases VALUES
        #                 (1610700000, 'TEST1', '10.10.10.1', 'Test 1', '*')""")
        # sql.execute ("""INSERT INTO DHCP_Leases VALUES
        #                 (1610700000, 'TEST2', '10.10.10.2', 'Test 2', '*')""")
    sql.execute ("""INSERT INTO Devices (dev_MAC, dev_name, dev_LastIP, 
                        dev_Vendor, dev_FirstConnection, dev_LastConnection,
                        dev_ScanCycle, dev_AlertEvents, dev_AlertDeviceDown,
                        dev_PresentLastScan)
                    SELECT DISTINCT DHCP_MAC,
                        (SELECT DHCP_Name FROM DHCP_Leases AS D2
                         WHERE D2.DHCP_MAC = D1.DHCP_MAC
                         ORDER BY DHCP_DateTime DESC LIMIT 1),
                        (SELECT DHCP_IP FROM DHCP_Leases AS D2
                         WHERE D2.DHCP_MAC = D1.DHCP_MAC
                         ORDER BY DHCP_DateTime DESC LIMIT 1),
                        '(unknown)', ?, ?, 1, 1, 0, 1
                    FROM DHCP_Leases AS D1
                    WHERE NOT EXISTS (SELECT 1 FROM Devices
                                      WHERE dev_MAC = DHCP_MAC) """,
                    (startTime, startTime) ) 

    # sql.execute ("""INSERT INTO Devices (dev_MAC, dev_name, dev_Vendor,
    #                     dev_LastIP, dev_FirstConnection, dev_LastConnection,
    #                     dev_ScanCycle, dev_AlertEvents, dev_AlertDeviceDown,
    #                     dev_PresentLastScan)
    #                 SELECT DHCP_MAC, DHCP_Name, '(unknown)', DHCP_IP, ?, ?,
    #                     1, 1, 0, 1
    #                 FROM DHCP_Leases
    #                 WHERE NOT EXISTS (SELECT 1 FROM Devices
    #                                   WHERE dev_MAC = DHCP_MAC) """,
    #                 (startTime, startTime) ) 
    print_log ('New Devices end')

#-------------------------------------------------------------------------------
def insert_events ():
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
                    (startTime, cycle) )

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
                    (startTime, cycle) )

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
                    (startTime, cycle) )

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
                    (startTime, cycle) )
    print_log ('Events end')

#-------------------------------------------------------------------------------
def update_devices_data_from_scan ():
    # Update Last Connection
    print_log ('Update devices - 1 Last Connection')
    sql.execute ("""UPDATE Devices SET dev_LastConnection = ?,
                        dev_PresentLastScan = 1
                    WHERE dev_ScanCycle = ?
                      AND dev_PresentLastScan = 0
                      AND EXISTS (SELECT 1 FROM CurrentScan 
                                  WHERE dev_MAC = cur_MAC
                                    AND dev_ScanCycle = cur_ScanCycle) """,
                    (startTime, cycle))

    # Clean no active devices
    print_log ('Update devices - 2 Clean no active devices')
    sql.execute ("""UPDATE Devices SET dev_PresentLastScan = 0
                    WHERE dev_ScanCycle = ?
                      AND NOT EXISTS (SELECT 1 FROM CurrentScan 
                                      WHERE dev_MAC = cur_MAC
                                        AND dev_ScanCycle = cur_ScanCycle) """,
                    (cycle,))

    # Update IP & Vendor
    print_log ('Update devices - 3 LastIP & Vendor')
    sql.execute ("""UPDATE Devices
                    SET dev_LastIP = (SELECT cur_IP FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC
                                        AND dev_ScanCycle = cur_ScanCycle),
                        dev_Vendor = (SELECT cur_Vendor FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC
                                        AND dev_ScanCycle = cur_ScanCycle)
                    WHERE dev_ScanCycle = ?
                      AND EXISTS (SELECT 1 FROM CurrentScan
                                  WHERE dev_MAC = cur_MAC
                                    AND dev_ScanCycle = cur_ScanCycle) """,
                    (cycle,)) 

    # Pi-hole Network - Update (unknown) Name
    print_log ('Update devices - 4 Unknown Name')
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
    print_log ('Update devices - 5 Vendor')

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
    print_log ('Update devices end')

#-------------------------------------------------------------------------------
def update_devices_names (db):
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

    # perform Pholus scan if (unknown) devices found
    if PHOLUS_ACTIVE and (len(unknownDevices) > 0 or PHOLUS_FORCE):        
        performPholusScan(PHOLUS_TIMEOUT)

    # skip checks if no unknown devices
    if len(unknownDevices) == 0 and PHOLUS_FORCE == False:
        return

    # Devices without name
    mylog('verbose', ['        Trying to resolve devices without name'])

    # get names from Pholus scan 
    sql.execute ('SELECT * FROM Pholus_Scan where "Record_Type"="Answer"')    
    pholusResults = list(sql.fetchall())        
    db.commitDB()

    # Number of entries from previous Pholus scans
    mylog('verbose', ["          Pholus entries from prev scans: ", len(pholusResults)])

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
            recordsNotFound.append (["(name not found)", device['dev_MAC']])          
        else:
            # name wa sfound with DiG or Pholus
            recordsToUpdate.append ([newName, device['dev_MAC']])

    # Print log            
    mylog('verbose', ["        Names Found (DiG/Pholus): ", len(recordsToUpdate), " (",foundDig,"/",foundPholus ,")" ])                 
    mylog('verbose', ["        Names Not Found         : ", len(recordsNotFound) ])    
     
    # update not found devices with (name not found) 
    sql.executemany ("UPDATE Devices SET dev_Name = ? WHERE dev_MAC = ? ", recordsNotFound )
    # update names of devices which we were bale to resolve
    sql.executemany ("UPDATE Devices SET dev_Name = ? WHERE dev_MAC = ? ", recordsToUpdate )
    db.commitDB()


#-------------------------------------------------------------------------------
def performNmapScan( devicesToScan):

    global changedPorts_json_struc     

    changedPortsTmp = []

    if len(devicesToScan) > 0:

        timeoutSec = NMAP_TIMEOUT

        devTotal = len(devicesToScan)

        updateState(db,"Scan: Nmap")

        mylog('verbose', ['[', timeNow(), '] Scan: Nmap for max ', str(timeoutSec), 's ('+ str(round(int(timeoutSec) / 60, 1)) +'min) per device'])  

        mylog('verbose', ["        Estimated max delay: ", (devTotal * int(timeoutSec)), 's ', '(', round((devTotal * int(timeoutSec))/60,1) , 'min)' ])

        devIndex = 0
        for device in devicesToScan:
            # Execute command
            output = ""
            # prepare arguments from user supplied ones
            nmapArgs = ['nmap'] + NMAP_ARGS.split() + [device["dev_LastIP"]]

            progress = ' (' + str(devIndex+1) + '/' + str(devTotal) + ')'

            try:
                # try runnning a subprocess with a forced (timeout + 30 seconds)  in case the subprocess hangs
                output = subprocess.check_output (nmapArgs, universal_newlines=True,  stderr=subprocess.STDOUT, timeout=(timeoutSec + 30))
            except subprocess.CalledProcessError as e:
                # An error occured, handle it
                mylog('none', [e.output])
                mylog('none', ["        Error - Nmap Scan - check logs", progress])            
            except subprocess.TimeoutExpired as timeErr:
                mylog('verbose', ['        Nmap TIMEOUT - the process forcefully terminated as timeout reached for ', device["dev_LastIP"], progress]) 

            if output == "": # check if the subprocess failed                    
                mylog('info', ['[', timeNow(), '] Scan: Nmap FAIL for ', device["dev_LastIP"], progress ,' check logs for details']) 
            else: 
                mylog('verbose', ['[', timeNow(), '] Scan: Nmap SUCCESS for ', device["dev_LastIP"], progress])

            devIndex += 1
            
            #  check the last run output        
            newLines = output.split('\n')

            # regular logging
            for line in newLines:
                append_line_to_file (logPath + '/pialert_nmap.log', line +'\n')                
            
            # collect ports / new Nmap Entries
            newEntriesTmp = []

            index = 0
            startCollecting = False
            duration = "" 
            for line in newLines:            
                if 'Starting Nmap' in line:
                    if len(newLines) > index+1 and 'Note: Host seems down' in newLines[index+1]:
                        break # this entry is empty
                elif 'PORT' in line and 'STATE' in line and 'SERVICE' in line:
                    startCollecting = True
                elif 'PORT' in line and 'STATE' in line and 'SERVICE' in line:    
                    startCollecting = False # end reached
                elif startCollecting and len(line.split()) == 3:                                    
                    newEntriesTmp.append(nmap_entry(device["dev_MAC"], timeNow(), line.split()[0], line.split()[1], line.split()[2], device["dev_Name"]))
                elif 'Nmap done' in line:
                    duration = line.split('scanned in ')[1]            
            index += 1

            # previous Nmap Entries
            oldEntries = []

            mylog('verbose', ['[', timeNow(), '] Scan: Ports found by NMAP: ', len(newEntriesTmp)])
            
            if len(newEntriesTmp) > 0:   

                #  get all current NMAP ports from the DB
                sql.execute(sql_nmap_scan_all) 

                rows = sql.fetchall()

                for row in rows: 
                    # only collect entries matching the current MAC address
                    if row["MAC"] == device["dev_MAC"]:
                        oldEntries.append(nmap_entry(row["MAC"], row["Time"], row["Port"], row["State"], row["Service"], device["dev_Name"], row["Extra"], row["Index"]))


                newEntries = []

                # Collect all entries that don't match the ones in the DB               
                for newTmpEntry in newEntriesTmp:

                    found = False
                    
                    #  Check the new entry is already available in oldEntries and remove from processing if yes
                    for oldEntry in oldEntries: 
                        if newTmpEntry.hash == oldEntry.hash:
                            found = True

                    if not found:
                        newEntries.append(newTmpEntry)


                mylog('verbose', ['[', timeNow(), '] Scan: Nmap newly discovered or changed ports: ', len(newEntries)])                

                # collect new ports, find the corresponding old entry and return for notification purposes
                # also update the DB with the new values after deleting the old ones
                if len(newEntries) > 0:
                    
                    # params to build the SQL query
                    params = []
                    indexesToDelete = ""

                    # Find old entry matching the new entry hash
                    for newEntry in newEntries:                   

                        foundEntry = None

                        for oldEntry in oldEntries:
                            if oldEntry.hash == newEntry.hash:
                                indexesToDelete = indexesToDelete + str(oldEntry.index) + ','
                                foundEntry = oldEntry                        

                        columnNames = ["Name", "MAC", "Port", "State", "Service", "Extra", "NewOrOld"  ]

                        # Old entry found
                        if foundEntry is not None:
                            # Build params for sql query
                            params.append((newEntry.mac, newEntry.time, newEntry.port, newEntry.state, newEntry.service, oldEntry.extra))
                            # Build JSON for API and notifications
                            changedPortsTmp.append({       
                                                    "Name"      : foundEntry.name, 
                                                    "MAC"       : newEntry.mac, 
                                                    "Port"      : newEntry.port, 
                                                    "State"     : newEntry.state, 
                                                    "Service"   : newEntry.service, 
                                                    "Extra"     : foundEntry.extra,
                                                    "NewOrOld"  : "New values"
                                                })
                            changedPortsTmp.append({ 
                                                    "Name"      : foundEntry.name, 
                                                    "MAC"       : foundEntry.mac, 
                                                    "Port"      : foundEntry.port, 
                                                    "State"     : foundEntry.state, 
                                                    "Service"   : foundEntry.service, 
                                                    "Extra"     : foundEntry.extra,
                                                    "NewOrOld"  : "Old values"
                                                })                            
                        # New entry - no matching Old entry found
                        else:
                            # Build params for sql query
                            params.append((newEntry.mac, newEntry.time, newEntry.port, newEntry.state, newEntry.service, ''))
                            # Build JSON for API and notifications
                            changedPortsTmp.append({
                                                    "Name"      : "New device", 
                                                    "MAC"       : newEntry.mac, 
                                                    "Port"      : newEntry.port, 
                                                    "State"     : newEntry.state, 
                                                    "Service"   : newEntry.service, 
                                                    "Extra"     : "",
                                                    "NewOrOld"  : "New device"                                       
                                                })

                    changedPorts_json_struc = json_struc({ "data" : changedPortsTmp}, columnNames)

                    #  Delete old entries if available
                    if len(indexesToDelete) > 0:
                        sql.execute ("DELETE FROM Nmap_Scan where \"Index\" in (" + indexesToDelete[:-1] +")")
                        db.commitDB()

                    # Insert new values into the DB 
                    sql.executemany ("""INSERT INTO Nmap_Scan ("MAC", "Time", "Port", "State", "Service", "Extra") VALUES (?, ?, ?, ?, ?, ?)""", params) 
                    db.commitDB()

#-------------------------------------------------------------------------------
class nmap_entry:
    def __init__(self, mac, time, port, state, service, name = '', extra = '', index = 0):
        self.mac = mac
        self.time = time
        self.port = port
        self.state = state
        self.service = service
        self.name = name
        self.extra = extra
        self.index = index
        self.hash = str(mac) + str(port)+ str(state)+ str(service)

#-------------------------------------------------------------------------------
def performPholusScan (db, timeoutSec):

    # scan every interface
    for subnet in userSubnets:

        temp = subnet.split("--interface=")

        if len(temp) != 2:
            mylog('none', ["        Skip scan (need subnet in format '192.168.1.0/24 --inteface=eth0'), got: ", subnet])
            return

        mask = temp[0].strip()
        interface = temp[1].strip()

        # logging & updating app state        
        updateState(db,"Scan: Pholus")        
        mylog('info', ['[', timeNow(), '] Scan: Pholus for ', str(timeoutSec), 's ('+ str(round(int(timeoutSec) / 60, 1)) +'min)'])  
        mylog('verbose', ["        Pholus scan on [interface] ", interface, " [mask] " , mask])
        
        # the scan always lasts 2x as long, so the desired user time from settings needs to be halved
        adjustedTimeout = str(round(int(timeoutSec) / 2, 0)) 

        #  python3 -m trace --trace /home/pi/pialert/pholus/pholus3.py eth1 -rdns_scanning  192.168.1.0/24 -stimeout 600
        pholus_args = ['python3', fullPholusPath, interface, "-rdns_scanning", mask, "-stimeout", adjustedTimeout]

        # Execute command
        output = ""

        try:
            # try runnning a subprocess with a forced (timeout + 30 seconds)  in case the subprocess hangs
            output = subprocess.check_output (pholus_args, universal_newlines=True,  stderr=subprocess.STDOUT, timeout=(timeoutSec + 30))
        except subprocess.CalledProcessError as e:
            # An error occured, handle it
            mylog('none', [e.output])
            mylog('none', ["        Error - Pholus Scan - check logs"])            
        except subprocess.TimeoutExpired as timeErr:
            mylog('none', ['        Pholus TIMEOUT - the process forcefully terminated as timeout reached']) 

        if output == "": # check if the subprocess failed                    
            mylog('none', ['[', timeNow(), '] Scan: Pholus FAIL - check logs']) 
        else: 
            mylog('verbose', ['[', timeNow(), '] Scan: Pholus SUCCESS'])
        
        #  check the last run output
        f = open(logPath + '/pialert_pholus_lastrun.log', 'r+')
        newLines = f.read().split('\n')
        f.close()        

        # cleanup - select only lines containing a separator to filter out unnecessary data
        newLines = list(filter(lambda x: '|' in x, newLines))        
        
        # build SQL query parameters to insert into the DB
        params = []

        for line in newLines:
            columns = line.split("|")
            if len(columns) == 4:
                params.append(( interface + " " + mask, timeNow() , columns[0].replace(" ", ""), columns[1].replace(" ", ""), columns[2].replace(" ", ""), columns[3], ''))

        if len(params) > 0:                
            sql.executemany ("""INSERT INTO Pholus_Scan ("Info", "Time", "MAC", "IP_v4_or_v6", "Record_Type", "Value", "Extra") VALUES (?, ?, ?, ?, ?, ?, ?)""", params) 
            db.commitDB()

#-------------------------------------------------------------------------------
def cleanResult(str):
    # alternative str.split('.')[0]
    str = str.replace("._airplay", "")
    str = str.replace("._tcp", "")
    str = str.replace(".local", "")
    str = str.replace("._esphomelib", "")
    str = str.replace("._googlecast", "")
    str = str.replace(".lan", "")
    str = str.replace(".home", "")
    str = re.sub(r'-[a-fA-F0-9]{32}', '', str)    # removing last part of e.g. Nest-Audio-ff77ff77ff77ff77ff77ff77ff77ff77
    # remove trailing dots
    if str.endswith('.'):
        str = str[:-1]

    return str


# Disclaimer - I'm interfacing with a script I didn't write (pholus3.py) so it's possible I'm missing types of answers
# it's also possible the pholus3.py script can be adjusted to provide a better output to interface with it
# Hit me with a PR if you know how! :)
def resolve_device_name_pholus (pMAC, pIP, allRes):
    
    pholusMatchesIndexes = []

    index = 0
    for result in allRes:
        #  limiting entries used for name resolution to the ones containing the current IP (v4 only)
        if result["MAC"] == pMAC and result["Record_Type"] == "Answer" and result["IP_v4_or_v6"] == pIP and '._googlezone' not in result["Value"]:
            # found entries with a matching MAC address, let's collect indexes             
            pholusMatchesIndexes.append(index)

        index += 1

    # return if nothing found
    if len(pholusMatchesIndexes) == 0:
        return -1

    # we have some entries let's try to select the most useful one

    # airplay matches contain a lot of information
    # Matches for example: 
    # Brand Tv (50)._airplay._tcp.local. TXT Class:32769 "acl=0 deviceid=66:66:66:66:66:66 features=0x77777,0x38BCB46 rsf=0x3 fv=p20.T-FFFFFF-03.1 flags=0x204 model=XXXX manufacturer=Brand serialNumber=XXXXXXXXXXX protovers=1.1 srcvers=777.77.77 pi=FF:FF:FF:FF:FF:FF psi=00000000-0000-0000-0000-FFFFFFFFFF gid=00000000-0000-0000-0000-FFFFFFFFFF gcgl=0 pk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    for i in pholusMatchesIndexes:
        if checkIPV4(allRes[i]['IP_v4_or_v6']) and '._airplay._tcp.local. TXT Class:32769' in str(allRes[i]["Value"]) :
            return allRes[i]["Value"].split('._airplay._tcp.local. TXT Class:32769')[0]
    
    # second best - contains airplay
    # Matches for example: 
    # _airplay._tcp.local. PTR Class:IN "Brand Tv (50)._airplay._tcp.local."
    for i in pholusMatchesIndexes:
        if checkIPV4(allRes[i]['IP_v4_or_v6']) and '_airplay._tcp.local. PTR Class:IN' in allRes[i]["Value"] and ('._googlecast') not in allRes[i]["Value"]:
            return cleanResult(allRes[i]["Value"].split('"')[1])    

    # Contains PTR Class:32769
    # Matches for example: 
    # 3.1.168.192.in-addr.arpa. PTR Class:32769 "MyPc.local."
    for i in pholusMatchesIndexes:
        if checkIPV4(allRes[i]['IP_v4_or_v6']) and 'PTR Class:32769' in allRes[i]["Value"]:
            return cleanResult(allRes[i]["Value"].split('"')[1])

    # Contains AAAA Class:IN
    # Matches for example: 
    # DESKTOP-SOMEID.local. AAAA Class:IN "fe80::fe80:fe80:fe80:fe80"
    for i in pholusMatchesIndexes:
        if checkIPV4(allRes[i]['IP_v4_or_v6']) and 'AAAA Class:IN' in allRes[i]["Value"]:
            return cleanResult(allRes[i]["Value"].split('.local.')[0])

    # Contains _googlecast._tcp.local. PTR Class:IN
    # Matches for example: 
    # _googlecast._tcp.local. PTR Class:IN "Nest-Audio-ff77ff77ff77ff77ff77ff77ff77ff77._googlecast._tcp.local."
    for i in pholusMatchesIndexes:
        if checkIPV4(allRes[i]['IP_v4_or_v6']) and '_googlecast._tcp.local. PTR Class:IN' in allRes[i]["Value"] and ('Google-Cast-Group') not in allRes[i]["Value"]:
            return cleanResult(allRes[i]["Value"].split('"')[1])

    # Contains A Class:32769
    # Matches for example: 
    # Android.local. A Class:32769 "192.168.1.6"
    for i in pholusMatchesIndexes:
        if checkIPV4(allRes[i]['IP_v4_or_v6']) and ' A Class:32769' in allRes[i]["Value"]:
            return cleanResult(allRes[i]["Value"].split(' A Class:32769')[0])

    # # Contains PTR Class:IN
    # Matches for example: 
    # _esphomelib._tcp.local. PTR Class:IN "ceiling-light-1._esphomelib._tcp.local."
    for i in pholusMatchesIndexes:
        if checkIPV4(allRes[i]['IP_v4_or_v6']) and 'PTR Class:IN' in allRes[i]["Value"]:
            return cleanResult(allRes[i]["Value"].split('"')[1])

    return -1
    
#-------------------------------------------------------------------------------

def resolve_device_name_dig (pMAC, pIP):
    
    newName = ""

    try :
        dig_args = ['dig', '+short', '-x', pIP]

        # Execute command
        try:
            # try runnning a subprocess
            newName = subprocess.check_output (dig_args, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            # An error occured, handle it
            mylog('none', [e.output])            
            # newName = "Error - check logs"
            return -1

        # Check returns
        newName = newName.strip()

        if len(newName) == 0 :
            return -1
            
        # Cleanup
        newName = cleanResult(newName)

        if newName == "" or  len(newName) == 0: 
            return -1

        # Return newName
        return newName

    # not Found
    except subprocess.CalledProcessError :
        return -1            

#-------------------------------------------------------------------------------
def void_ghost_disconnections (db):
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
                    (startTime, cycle, startTime)   )

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
                    (cycle, startTime)   )

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
                    (cycle, startTime)   )
    print_log ('Void end')
    db.commitDB()

#-------------------------------------------------------------------------------
def pair_sessions_events (db):
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
def skip_repeated_notifications (db):    

    # Skip repeated notifications
    # due strfime : Overflow --> use  "strftime / 60"
    print_log ('Skip Repeated')
    sql.execute ("""UPDATE Events SET eve_PendingAlertEmail = 0
                    WHERE eve_PendingAlertEmail = 1 AND eve_MAC IN
                        (
                        SELECT dev_MAC FROM Devices
                        WHERE dev_LastNotification IS NOT NULL
                          AND dev_LastNotification <>""
                          AND (strftime("%s", dev_LastNotification)/60 +
                                dev_SkipRepeated * 60) >
                              (strftime('%s','now','localtime')/60 )
                        )
                 """ )
    print_log ('Skip Repeated end')

    db.commitDB()


#===============================================================================
# REPORTING
#===============================================================================
# create a json for webhook and mqtt notifications to provide further integration options  
json_final = []

def send_notifications (db):
    global mail_text, mail_html, json_final, changedPorts_json_struc, partial_html, partial_txt, partial_json

    deviceUrl              = REPORT_DASHBOARD_URL + '/deviceDetails.php?mac='
    plugins_report         = False

    # Reporting section
    mylog('verbose', ['  Check if something to report'])    

    # prepare variables for JSON construction
    json_internet = []
    json_new_devices = []
    json_down_devices = []
    json_events = []
    json_ports = []
    json_plugins = []

    # Disable reporting on events for devices where reporting is disabled based on the MAC address
    sql.execute ("""UPDATE Events SET eve_PendingAlertEmail = 0
                    WHERE eve_PendingAlertEmail = 1 AND eve_EventType != 'Device Down' AND eve_MAC IN
                        (
                            SELECT dev_MAC FROM Devices WHERE dev_AlertEvents = 0 
						)""")
    sql.execute ("""UPDATE Events SET eve_PendingAlertEmail = 0
                    WHERE eve_PendingAlertEmail = 1 AND eve_EventType = 'Device Down' AND eve_MAC IN
                        (
                            SELECT dev_MAC FROM Devices WHERE dev_AlertDeviceDown = 0 
						)""")

    # Open text Template
    template_file = open(pialertPath + '/back/report_template.txt', 'r') 
    mail_text = template_file.read() 
    template_file.close() 

    # Open html Template
    template_file = open(pialertPath + '/back/report_template.html', 'r') 
    if isNewVersion(db):
        template_file = open(pialertPath + '/back/report_template_new_version.html', 'r') 

    mail_html = template_file.read() 
    template_file.close() 

    # Report Header & footer
    timeFormated = startTime.strftime ('%Y-%m-%d %H:%M')
    mail_text = mail_text.replace ('<REPORT_DATE>', timeFormated)
    mail_html = mail_html.replace ('<REPORT_DATE>', timeFormated)

    mail_text = mail_text.replace ('<SERVER_NAME>', socket.gethostname() )
    mail_html = mail_html.replace ('<SERVER_NAME>', socket.gethostname() )

    if 'internet' in INCLUDED_SECTIONS:
        # Compose Internet Section
        sqlQuery = """SELECT eve_MAC as MAC,  eve_IP as IP, eve_DateTime as Datetime, eve_EventType as "Event Type", eve_AdditionalInfo as "More info" FROM Events
                        WHERE eve_PendingAlertEmail = 1 AND eve_MAC = 'Internet'
                        ORDER BY eve_DateTime"""

        notiStruc = construct_notifications(sqlQuery, "Internet IP change")

        # collect "internet" (IP changes) for the webhook json          
        json_internet = notiStruc.json["data"]

        mail_text = mail_text.replace ('<SECTION_INTERNET>', notiStruc.text + '\n')
        mail_html = mail_html.replace ('<INTERNET_TABLE>', notiStruc.html)

    if 'new_devices' in INCLUDED_SECTIONS:
        # Compose New Devices Section 
        sqlQuery = """SELECT eve_MAC as MAC, eve_DateTime as Datetime, dev_LastIP as IP, eve_EventType as "Event Type", dev_Name as "Device name", dev_Comments as Comments  FROM Events_Devices
                        WHERE eve_PendingAlertEmail = 1
                        AND eve_EventType = 'New Device'
                        ORDER BY eve_DateTime"""

        notiStruc = construct_notifications(sqlQuery, "New devices")

        # collect "new_devices" for the webhook json         
        json_new_devices = notiStruc.json["data"]

        mail_text = mail_text.replace ('<SECTION_NEW_DEVICES>', notiStruc.text + '\n')
        mail_html = mail_html.replace ('<NEW_DEVICES_TABLE>', notiStruc.html)

    if 'down_devices' in INCLUDED_SECTIONS:
        # Compose Devices Down Section   
        sqlQuery = """SELECT eve_MAC as MAC, eve_DateTime as Datetime, dev_LastIP as IP, eve_EventType as "Event Type", dev_Name as "Device name", dev_Comments as Comments  FROM Events_Devices
                        WHERE eve_PendingAlertEmail = 1
                        AND eve_EventType = 'Device Down'
                        ORDER BY eve_DateTime"""

        notiStruc = construct_notifications(sqlQuery, "Down devices")

        # collect "new_devices" for the webhook json         
        json_down_devices = notiStruc.json["data"]

        mail_text = mail_text.replace ('<SECTION_DEVICES_DOWN>', notiStruc.text + '\n')
        mail_html = mail_html.replace ('<DOWN_DEVICES_TABLE>', notiStruc.html)

    if 'events' in INCLUDED_SECTIONS:
        # Compose Events Section   
        sqlQuery = """SELECT eve_MAC as MAC, eve_DateTime as Datetime, dev_LastIP as IP, eve_EventType as "Event Type", dev_Name as "Device name", dev_Comments as Comments  FROM Events_Devices
                        WHERE eve_PendingAlertEmail = 1
                        AND eve_EventType IN ('Connected','Disconnected',
                            'IP Changed')
                        ORDER BY eve_DateTime"""

        notiStruc = construct_notifications(sqlQuery, "Events")

        # collect "events" for the webhook json         
        json_events = notiStruc.json["data"]

        mail_text = mail_text.replace ('<SECTION_EVENTS>', notiStruc.text + '\n')
        mail_html = mail_html.replace ('<EVENTS_TABLE>', notiStruc.html)
    
    if 'ports' in INCLUDED_SECTIONS:  
        # collect "ports" for the webhook json 
        if changedPorts_json_struc is not None:          
            json_ports =  changedPorts_json_struc.json["data"]       

        notiStruc = construct_notifications("", "Ports", True, changedPorts_json_struc)

        mail_html = mail_html.replace ('<PORTS_TABLE>', notiStruc.html)

        portsTxt = ""
        if changedPorts_json_struc is not None:
            portsTxt = "Ports \n---------\n Ports changed! Check PiAlert for details!\n"        

        mail_text = mail_text.replace ('<PORTS_TABLE>', portsTxt )

    if 'plugins' in INCLUDED_SECTIONS and ENABLE_PLUGINS:  
        # Compose Plugins Section           
        sqlQuery = """SELECT Plugin, Object_PrimaryId, Object_SecondaryId, DateTimeChanged, Watched_Value1, Watched_Value2, Watched_Value3, Watched_Value4, Status from Plugins_Events"""

        notiStruc = construct_notifications(sqlQuery, "Plugins")

        # collect "plugins" for the webhook json 
        json_plugins = notiStruc.json["data"]

        mail_text = mail_text.replace ('<PLUGINS_TABLE>', notiStruc.text + '\n')
        mail_html = mail_html.replace ('<PLUGINS_TABLE>', notiStruc.html)

        # check if we need to report something
        plugins_report = len(json_plugins) > 0


    json_final = {
                    "internet": json_internet,                        
                    "new_devices": json_new_devices,
                    "down_devices": json_down_devices,                        
                    "events": json_events,
                    "ports": json_ports,
                    "plugins": json_plugins,
                    }    

    mail_text = removeDuplicateNewLines(mail_text)
    
    # Create clickable MAC links 
    mail_html = generate_mac_links (mail_html, deviceUrl)

    #  Write output emails for debug    
    write_file (logPath + '/report_output.json', json.dumps(json_final)) 
    write_file (logPath + '/report_output.txt', mail_text) 
    write_file (logPath + '/report_output.html', mail_html) 

    # Send Mail
    if json_internet != [] or json_new_devices != [] or json_down_devices != [] or json_events != [] or json_ports != [] or debug_force_notification or plugins_report:        

        update_api(True)

        mylog('none', ['    Changes detected, sending reports'])

        if REPORT_MAIL and check_config('email'):  
            updateState(db,"Send: Email")
            mylog('info', ['      Sending report by Email'])
            send_email (mail_text, mail_html)
        else :
            mylog('verbose', ['      Skip email'])
        if REPORT_APPRISE and check_config('apprise'):
            updateState(db,"Send: Apprise")
            mylog('info', ['      Sending report by Apprise'])
            send_apprise (mail_html, mail_text)
        else :
            mylog('verbose', ['      Skip Apprise'])
        if REPORT_WEBHOOK and check_config('webhook'):
            updateState(db,"Send: Webhook")
            mylog('info', ['      Sending report by Webhook'])
            send_webhook (json_final, mail_text)
        else :
            mylog('verbose', ['      Skip webhook'])
        if REPORT_NTFY and check_config('ntfy'):
            updateState(db,"Send: NTFY")
            mylog('info', ['      Sending report by NTFY'])
            send_ntfy (mail_text)
        else :
            mylog('verbose', ['      Skip NTFY'])
        if REPORT_PUSHSAFER and check_config('pushsafer'):
            updateState(db,"Send: PUSHSAFER")
            mylog('info', ['      Sending report by PUSHSAFER'])
            send_pushsafer (mail_text)
        else :
            mylog('verbose', ['      Skip PUSHSAFER'])
        # Update MQTT entities
        if REPORT_MQTT and check_config('mqtt'):
            updateState(db,"Send: MQTT")
            mylog('info', ['      Establishing MQTT thread'])                          
            mqtt_start()        
        else :
            mylog('verbose', ['      Skip MQTT'])
    else :
        mylog('verbose', ['    No changes to report'])

    # Clean Pending Alert Events
    sql.execute ("""UPDATE Devices SET dev_LastNotification = ?
                    WHERE dev_MAC IN (SELECT eve_MAC FROM Events
                                      WHERE eve_PendingAlertEmail = 1)
                 """, (datetime.datetime.now(),) )
    sql.execute ("""UPDATE Events SET eve_PendingAlertEmail = 0
                    WHERE eve_PendingAlertEmail = 1""")

    # clear plugin events
    sql.execute ("DELETE FROM Plugins_Events")
    
    changedPorts_json_struc = None

    # DEBUG - print number of rows updated    
    mylog('info', ['[', timeNow(), '] Notifications: ', sql.rowcount])

    # Commit changes    
    db.commitDB()

#-------------------------------------------------------------------------------
def construct_notifications(sqlQuery, tableTitle, skipText = False, suppliedJsonStruct = None):

    if suppliedJsonStruct is None and sqlQuery == "":
        return noti_struc("", "", "")

    table_attributes = {"style" : "border-collapse: collapse; font-size: 12px; color:#70707", "width" : "100%", "cellspacing" : 0, "cellpadding" : "3px", "bordercolor" : "#C0C0C0", "border":"1"}
    headerProps = "width='120px' style='color:blue; font-size: 16px;' bgcolor='#909090' "
    thProps = "width='120px' style='color:#F0F0F0' bgcolor='#909090' "

    build_direction = "TOP_TO_BOTTOM"
    text_line = '{}\t{}\n'

    if suppliedJsonStruct is None:
        json_struc = get_table_as_json(sqlQuery)
    else:
        json_struc = suppliedJsonStruct

    jsn  = json_struc.json
    html = ""    
    text = ""

    if len(jsn["data"]) > 0:
        text = tableTitle + "\n---------\n"

        html = convert(jsn, build_direction=build_direction, table_attributes=table_attributes)
        html = format_table(html, "data", headerProps, tableTitle).replace('<ul>','<ul style="list-style:none;padding-left:0">')

        headers = json_struc.columnNames

        # prepare text-only message
        if skipText == False:
            
            for device in jsn["data"]:
                for header in headers:
                    padding = ""
                    if len(header) < 4:
                        padding = "\t"
                    text += text_line.format ( header + ': ' + padding, device[header]) 
                text += '\n'

        #  Format HTML table headers
        for header in headers:
            html = format_table(html, header, thProps)

    return noti_struc(jsn, text, html)

#-------------------------------------------------------------------------------
class noti_struc:
    def __init__(self, json, text, html):
        self.json = json
        self.text = text
        self.html = html
       
#-------------------------------------------------------------------------------
def check_config(service):

    if service == 'email':
        if SMTP_SERVER == '' or REPORT_FROM == '' or REPORT_TO == '':
            mylog('none', ['    Error: Email service not set up correctly. Check your pialert.conf SMTP_*, REPORT_FROM and REPORT_TO variables.'])
            return False
        else:
            return True   

    if service == 'apprise':
        if APPRISE_URL == '' or APPRISE_HOST == '':
            mylog('none', ['    Error: Apprise service not set up correctly. Check your pialert.conf APPRISE_* variables.'])
            return False
        else:
            return True  

    if service == 'webhook':
        if WEBHOOK_URL == '':
            mylog('none', ['    Error: Webhook service not set up correctly. Check your pialert.conf WEBHOOK_* variables.'])
            return False
        else:
            return True 

    if service == 'ntfy':
        if NTFY_HOST == '' or NTFY_TOPIC == '':
            mylog('none', ['    Error: NTFY service not set up correctly. Check your pialert.conf NTFY_* variables.'])
            return False
        else:
            return True 

    if service == 'pushsafer':
        if PUSHSAFER_TOKEN == 'ApiKey':
            mylog('none', ['    Error: Pushsafer service not set up correctly. Check your pialert.conf PUSHSAFER_TOKEN variable.'])
            return False
        else:
            return True 

    if service == 'mqtt':
        if MQTT_BROKER == '' or MQTT_PORT == '' or MQTT_USER == '' or MQTT_PASSWORD == '':
            mylog('none', ['    Error: MQTT service not set up correctly. Check your pialert.conf MQTT_* variables.'])
            return False
        else:
            return True 


   
#-------------------------------------------------------------------------------
def format_table (html, thValue, props, newThValue = ''):

    if newThValue == '':
        newThValue = thValue
        
    return html.replace("<th>"+thValue+"</th>", "<th "+props+" >"+newThValue+"</th>" )

#-------------------------------------------------------------------------------
def generate_mac_links (html, deviceUrl):

    p = re.compile(r'(?:[0-9a-fA-F]:?){12}')

    MACs = re.findall(p, html)

    for mac in MACs:        
        html = html.replace('<td>' + mac + '</td>','<td><a href="' + deviceUrl + mac + '">' + mac + '</a></td>')

    return html

#-------------------------------------------------------------------------------
def format_report_section (pActive, pSection, pTable, pText, pHTML):
    global mail_text
    global mail_html

    # Replace section text
    if pActive :
        mail_text = mail_text.replace ('<'+ pTable +'>', pText)
        mail_html = mail_html.replace ('<'+ pTable +'>', pHTML)       

        mail_text = remove_tag (mail_text, pSection)       
        mail_html = remove_tag (mail_html, pSection)
    else:
        mail_text = remove_section (mail_text, pSection)
        mail_html = remove_section (mail_html, pSection)

#-------------------------------------------------------------------------------
def remove_section (pText, pSection):
    # Search section into the text
    if pText.find ('<'+ pSection +'>') >=0 \
    and pText.find ('</'+ pSection +'>') >=0 : 
        # return text without the section
        return pText[:pText.find ('<'+ pSection+'>')] + \
               pText[pText.find ('</'+ pSection +'>') + len (pSection) +3:]
    else :
        # return all text
        return pText

#-------------------------------------------------------------------------------
def remove_tag (pText, pTag):
    # return text without the tag
    return pText.replace ('<'+ pTag +'>','').replace ('</'+ pTag +'>','')


#-------------------------------------------------------------------------------
# Reporting 
#-------------------------------------------------------------------------------
def send_email (pText, pHTML):

    # Print more info for debugging if LOG_LEVEL == 'debug' 
    if LOG_LEVEL == 'debug':
        print_log ('REPORT_TO: ' + hide_email(str(REPORT_TO)) + '  SMTP_USER: ' + hide_email(str(SMTP_USER))) 

    # Compose email
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Pi.Alert Report'
    msg['From'] = REPORT_FROM
    msg['To'] = REPORT_TO
    msg.attach (MIMEText (pText, 'plain'))
    msg.attach (MIMEText (pHTML, 'html'))

    failedAt = ''

    failedAt = print_log ('SMTP try')

    try:
        # Send mail
        failedAt = print_log('Trying to open connection to ' + str(SMTP_SERVER) + ':' + str(SMTP_PORT))

        if SMTP_FORCE_SSL:
            failedAt = print_log('SMTP_FORCE_SSL == True so using .SMTP_SSL()')
            if SMTP_PORT == 0:            
                failedAt = print_log('SMTP_PORT == 0 so sending .SMTP_SSL(SMTP_SERVER)')
                smtp_connection = smtplib.SMTP_SSL(SMTP_SERVER)
            else:
                failedAt = print_log('SMTP_PORT == 0 so sending .SMTP_SSL(SMTP_SERVER, SMTP_PORT)')
                smtp_connection = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
            
        else:
            failedAt = print_log('SMTP_FORCE_SSL == False so using .SMTP()')
            if SMTP_PORT == 0:
                failedAt = print_log('SMTP_PORT == 0 so sending .SMTP(SMTP_SERVER)')
                smtp_connection = smtplib.SMTP (SMTP_SERVER)
            else:
                failedAt = print_log('SMTP_PORT == 0 so sending .SMTP(SMTP_SERVER, SMTP_PORT)')
                smtp_connection = smtplib.SMTP (SMTP_SERVER, SMTP_PORT)

        failedAt = print_log('Setting SMTP debug level')

        # Log level set to debug of the communication between SMTP server and client
        if LOG_LEVEL == 'debug':
            smtp_connection.set_debuglevel(1) 
        
        failedAt = print_log( 'Sending .ehlo()')
        smtp_connection.ehlo()

        if not SMTP_SKIP_TLS:       
            failedAt = print_log('SMTP_SKIP_TLS == False so sending .starttls()')
            smtp_connection.starttls()
            failedAt = print_log('SMTP_SKIP_TLS == False so sending .ehlo()')
            smtp_connection.ehlo()
        if not SMTP_SKIP_LOGIN:
            failedAt = print_log('SMTP_SKIP_LOGIN == False so sending .login()')
            smtp_connection.login (SMTP_USER, SMTP_PASS)
            
        failedAt = print_log('Sending .sendmail()')
        smtp_connection.sendmail (REPORT_FROM, REPORT_TO, msg.as_string())
        smtp_connection.quit()
    except smtplib.SMTPAuthenticationError as e: 
        mylog('none', ['      ERROR: Failed at - ', failedAt])
        mylog('none', ['      ERROR: Couldn\'t connect to the SMTP server (SMTPAuthenticationError), skipping Email (enable LOG_LEVEL=debug for more logging)'])
    except smtplib.SMTPServerDisconnected as e: 
        mylog('none', ['      ERROR: Failed at - ', failedAt])
        mylog('none', ['      ERROR: Couldn\'t connect to the SMTP server (SMTPServerDisconnected), skipping Email (enable LOG_LEVEL=debug for more logging)'])

    print_log('      DEBUG: Last executed - ' + str(failedAt))

#-------------------------------------------------------------------------------
def send_ntfy (_Text):
    headers = {
        "Title": "Pi.Alert Notification",
        "Actions": "view, Open Dashboard, "+ REPORT_DASHBOARD_URL,
        "Priority": "urgent",
        "Tags": "warning"
    }
    # if username and password are set generate hash and update header
    if NTFY_USER != "" and NTFY_PASSWORD != "":
	# Generate hash for basic auth
        usernamepassword = "{}:{}".format(NTFY_USER,NTFY_PASSWORD)
        basichash = b64encode(bytes(NTFY_USER + ':' + NTFY_PASSWORD, "utf-8")).decode("ascii")

	# add authorization header with hash
        headers["Authorization"] = "Basic {}".format(basichash)

    requests.post("{}/{}".format( NTFY_HOST, NTFY_TOPIC),
    data=_Text,
    headers=headers)

def send_pushsafer (_Text):
    url = 'https://www.pushsafer.com/api'
    post_fields = {
        "t" : 'Pi.Alert Message',
        "m" : _Text,
        "s" : 11,
        "v" : 3,
        "i" : 148,
        "c" : '#ef7f7f',
        "d" : 'a',
        "u" : REPORT_DASHBOARD_URL,
        "ut" : 'Open Pi.Alert',
        "k" : PUSHSAFER_TOKEN,
        }
    requests.post(url, data=post_fields)

#-------------------------------------------------------------------------------
def send_webhook (_json, _html):

    # use data type based on specified payload type
    if WEBHOOK_PAYLOAD == 'json':
        payloadData = _json        
    if WEBHOOK_PAYLOAD == 'html':
        payloadData = _html
    if WEBHOOK_PAYLOAD == 'text':
        payloadData = to_text(_json)

    # Define slack-compatible payload
    _json_payload = { "text": payloadData } if WEBHOOK_PAYLOAD == 'text' else {
    "username": "Pi.Alert",
    "text": "There are new notifications",
    "attachments": [{
      "title": "Pi.Alert Notifications",
      "title_link": REPORT_DASHBOARD_URL,
      "text": payloadData
    }]
    } 

    # DEBUG - Write the json payload into a log file for debugging
    write_file (logPath + '/webhook_payload.json', json.dumps(_json_payload))    

    # Using the Slack-Compatible Webhook endpoint for Discord so that the same payload can be used for both
    if(WEBHOOK_URL.startswith('https://discord.com/api/webhooks/') and not WEBHOOK_URL.endswith("/slack")):
        _WEBHOOK_URL = f"{WEBHOOK_URL}/slack"
        curlParams = ["curl","-i","-H", "Content-Type:application/json" ,"-d", json.dumps(_json_payload), _WEBHOOK_URL]
    else:
        _WEBHOOK_URL = WEBHOOK_URL
        curlParams = ["curl","-i","-X", WEBHOOK_REQUEST_METHOD ,"-H", "Content-Type:application/json" ,"-d", json.dumps(_json_payload), _WEBHOOK_URL]

    # execute CURL call
    try:
        # try runnning a subprocess
        mylog('debug', curlParams) 
        p = subprocess.Popen(curlParams, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        stdout, stderr = p.communicate()

        # write stdout and stderr into .log files for debugging if needed
        logResult (stdout, stderr)     # TO-DO should be changed to mylog
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        mylog('none', [e.output])

#-------------------------------------------------------------------------------
def send_apprise (html, text):
    #Define Apprise compatible payload (https://github.com/caronc/apprise-api#stateless-solution)
    payload = html

    if APPRISE_PAYLOAD == 'text':
        payload = text

    _json_payload={
    "urls": APPRISE_URL,
    "title": "Pi.Alert Notifications",    
    "format": APPRISE_PAYLOAD,
    "body": payload    
    }

    try:
        # try runnning a subprocess        
        p = subprocess.Popen(["curl","-i","-X", "POST" ,"-H", "Content-Type:application/json" ,"-d", json.dumps(_json_payload), APPRISE_HOST], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = p.communicate()
        # write stdout and stderr into .log files for debugging if needed
        logResult (stdout, stderr)      # TO-DO should be changed to mylog
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        mylog('none', [e.output])    

#-------------------------------------------------------------------------------
# MQTT
#-------------------------------------------------------------------------------
mqtt_connected_to_broker = False
mqtt_sensors = []

def publish_mqtt(client, topic, message):
    status = 1
    while status != 0:
        result = client.publish(
                topic=topic,
                payload=message,
                qos=MQTT_QOS,
                retain=True,
            )

        status = result[0]

        if status != 0:            
            mylog('info', ["Waiting to reconnect to MQTT broker"])
            time.sleep(0.1) 
    return True

#-------------------------------------------------------------------------------
def create_generic_device(client):  
    
    deviceName = 'PiAlert'
    deviceId = 'pialert'    
    
    create_sensor(client, deviceId, deviceName, 'sensor', 'online', 'wifi-check')    
    create_sensor(client, deviceId, deviceName, 'sensor', 'down', 'wifi-cancel')        
    create_sensor(client, deviceId, deviceName, 'sensor', 'all', 'wifi')
    create_sensor(client, deviceId, deviceName, 'sensor', 'archived', 'wifi-lock')
    create_sensor(client, deviceId, deviceName, 'sensor', 'new', 'wifi-plus')
    create_sensor(client, deviceId, deviceName, 'sensor', 'unknown', 'wifi-alert')
        

#-------------------------------------------------------------------------------
def create_sensor(client, deviceId, deviceName, sensorType, sensorName, icon):    

    new_sensor_config = sensor_config(deviceId, deviceName, sensorType, sensorName, icon)

    # check if config already in list and if not, add it, otherwise skip
    global mqtt_sensors, uniqueSensorCount

    is_unique = True

    for sensor in mqtt_sensors:
        if sensor.hash == new_sensor_config.hash:
            is_unique = False
            break
           
    # save if unique
    if is_unique:             
        publish_sensor(client, new_sensor_config)        


#-------------------------------------------------------------------------------
class sensor_config:
    def __init__(self, deviceId, deviceName, sensorType, sensorName, icon):
        self.deviceId = deviceId
        self.deviceName = deviceName
        self.sensorType = sensorType
        self.sensorName = sensorName
        self.icon = icon 
        self.hash = str(hash(str(deviceId) + str(deviceName)+ str(sensorType)+ str(sensorName)+ str(icon)))

#-------------------------------------------------------------------------------
def publish_sensor(client, sensorConf): 

    global mqtt_sensors             

    message = '{ \
                "name":"'+ sensorConf.deviceName +' '+sensorConf.sensorName+'", \
                "state_topic":"system-sensors/'+sensorConf.sensorType+'/'+sensorConf.deviceId+'/state", \
                "value_template":"{{value_json.'+sensorConf.sensorName+'}}", \
                "unique_id":"'+sensorConf.deviceId+'_sensor_'+sensorConf.sensorName+'", \
                "device": \
                    { \
                        "identifiers": ["'+sensorConf.deviceId+'_sensor"], \
                        "manufacturer": "PiAlert", \
                        "name":"'+sensorConf.deviceName+'" \
                    }, \
                "icon":"mdi:'+sensorConf.icon+'" \
                }'

    topic='homeassistant/'+sensorConf.sensorType+'/'+sensorConf.deviceId+'/'+sensorConf.sensorName+'/config'

    # add the sensor to the global list to keep track of succesfully added sensors
    if publish_mqtt(client, topic, message):        
                                     # hack - delay adding to the queue in case the process is 
        time.sleep(MQTT_DELAY_SEC)   # restarted and previous publish processes aborted 
                                     # (it takes ~2s to update a sensor config on the broker)
        mqtt_sensors.append(sensorConf)

#-------------------------------------------------------------------------------
def mqtt_create_client():
    def on_disconnect(client, userdata, rc):
        global mqtt_connected_to_broker
        mqtt_connected_to_broker = False
        
        # not sure is below line is correct / necessary        
        # client = mqtt_create_client() 

    def on_connect(client, userdata, flags, rc):
        global mqtt_connected_to_broker
        
        if rc == 0: 
            mylog('verbose', ["        Connected to broker"])            
            mqtt_connected_to_broker = True     # Signal connection 
        else: 
            mylog('none', ["        Connection failed"])
            mqtt_connected_to_broker = False


    client = mqtt_client.Client('PiAlert')   # Set Connecting Client ID    
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)    
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_start() 

    return client

#-------------------------------------------------------------------------------
def mqtt_start():    

    global client, mqtt_connected_to_broker

    if mqtt_connected_to_broker == False:
        mqtt_connected_to_broker = True           
        client = mqtt_create_client() 
    
    # General stats    

    # Create a generic device for overal stats
    create_generic_device(client)

    # Get the data
    row = get_device_stats()   

    columns = ["online","down","all","archived","new","unknown"]

    payload = ""

    # Update the values 
    for column in columns:       
        payload += '"'+column+'": ' + str(row[column]) +','       

    # Publish (warap into {} and remove last ',' from above)
    publish_mqtt(client, "system-sensors/sensor/pialert/state",              
            '{ \
                '+ payload[:-1] +'\
            }'
        )


    # Specific devices

    # Get all devices
    devices = get_all_devices()

    sec_delay = len(devices) * int(MQTT_DELAY_SEC)*5

    mylog('info', ["        Estimated delay: ", (sec_delay), 's ', '(', round(sec_delay/60,1) , 'min)' ])

    for device in devices:        

        # Create devices in Home Assistant - send config messages
        deviceId = 'mac_' + device["dev_MAC"].replace(" ", "").replace(":", "_").lower()
        deviceNameDisplay = re.sub('[^a-zA-Z0-9-_\s]', '', device["dev_Name"]) 

        create_sensor(client, deviceId, deviceNameDisplay, 'sensor', 'last_ip', 'ip-network')
        create_sensor(client, deviceId, deviceNameDisplay, 'binary_sensor', 'is_present', 'wifi')
        create_sensor(client, deviceId, deviceNameDisplay, 'sensor', 'mac_address', 'folder-key-network')
        create_sensor(client, deviceId, deviceNameDisplay, 'sensor', 'is_new', 'bell-alert-outline')
        create_sensor(client, deviceId, deviceNameDisplay, 'sensor', 'vendor', 'cog')
    
        # update device sensors in home assistant              

        publish_mqtt(client, 'system-sensors/sensor/'+deviceId+'/state', 
            '{ \
                "last_ip": "' + device["dev_LastIP"] +'", \
                "is_new": "' + str(device["dev_NewDevice"]) +'", \
                "vendor": "' + sanitize_string(device["dev_Vendor"]) +'", \
                "mac_address": "' + str(device["dev_MAC"]) +'" \
            }'
        ) 

        publish_mqtt(client, 'system-sensors/binary_sensor/'+deviceId+'/state', 
            '{ \
                "is_present": "' + to_binary_sensor(str(device["dev_PresentLastScan"])) +'"\
            }'
        ) 

        # delete device / topic
        #  homeassistant/sensor/mac_44_ef_bf_c4_b1_af/is_present/config
        # client.publish(
        #     topic="homeassistant/sensor/"+deviceId+"/is_present/config",
        #     payload="",
        #     qos=1,
        #     retain=True,
        # )        
    # time.sleep(10)



 
#===============================================================================
# Home Assistant UTILs
#===============================================================================
def to_binary_sensor(input):
    # In HA a binary sensor returns ON or OFF    
    result = "OFF"

    # bytestring
    if isinstance(input, str):
        if input == "1":
            result = "ON"
    elif isinstance(input, int):
        if input == 1:
            result = "ON"
    elif isinstance(input, bool):
        if input == True:
            result = "ON"
    elif isinstance(input, bytes):
        if bytes_to_string(input) == "1":
            result = "ON"
    return result
        






#===============================================================================
# UTIL
#===============================================================================









#-------------------------------------------------------------------------------


    

#-------------------------------------------------------------------------------

def sanitize_string(input):
    if isinstance(input, bytes):
        input = input.decode('utf-8')
    value = bytes_to_string(re.sub('[^a-zA-Z0-9-_\s]', '', str(input)))
    return value





#-------------------------------------------------------------------------------

def add_json_list (row, list):
    new_row = []
    for column in row :        
        column = bytes_to_string(column)

        new_row.append(column)

    list.append(new_row)    

    return list

#-------------------------------------------------------------------------------

def to_text(_json):
    payloadData = ""
    if len(_json['internet']) > 0 and 'internet' in INCLUDED_SECTIONS:
        payloadData += "INTERNET\n"
        for event in _json['internet']:
            payloadData += event[3] + ' on ' + event[2] + '. ' + event[4] + '. New address:' + event[1] + '\n'

    if len(_json['new_devices']) > 0 and 'new_devices' in INCLUDED_SECTIONS:
        payloadData += "NEW DEVICES:\n"
        for event in _json['new_devices']:
            if event[4] is None:
                event[4] = event[11]
            payloadData += event[1] + ' - ' + event[4] + '\n'

    if len(_json['down_devices']) > 0 and 'down_devices' in INCLUDED_SECTIONS:
        write_file (logPath + '/down_devices_example.log', _json['down_devices'])
        payloadData += 'DOWN DEVICES:\n'
        for event in _json['down_devices']:
            if event[4] is None:
                event[4] = event[11]
            payloadData += event[1] + ' - ' + event[4] + '\n'
    
    if len(_json['events']) > 0 and 'events' in INCLUDED_SECTIONS:
        payloadData += "EVENTS:\n"
        for event in _json['events']:
            if event[8] != "Internet":
                payloadData += event[8] + " on " + event[1] + " " + event[3] + " at " + event[2] + "\n"

    return payloadData

#-------------------------------------------------------------------------------
def get_device_stats(db):

    # columns = ["online","down","all","archived","new","unknown"]
    sql.execute(sql_devices_stats)

    row = sql.fetchone()
    db.commitDB()

    return row
#-------------------------------------------------------------------------------
def get_all_devices(db):    

    sql.execute(sql_devices_all)

    row = sql.fetchall()

    db.commitDB()
    return row

#-------------------------------------------------------------------------------



#-------------------------------------------------------------------------------
def removeDuplicateNewLines(text):
    if "\n\n\n" in text:
        return removeDuplicateNewLines(text.replace("\n\n\n", "\n\n"))
    else:
        return text

    
#-------------------------------------------------------------------------------
def hide_email(email):
    m = email.split('@')

    if len(m) == 2:
        return f'{m[0][0]}{"*"*(len(m[0])-2)}{m[0][-1] if len(m[0]) > 1 else ""}@{m[1]}'

    return email    

#-------------------------------------------------------------------------------
def check_and_run_event(db):
    sql.execute(""" select * from Parameters where par_ID = "Front_Event" """)
    rows = sql.fetchall()    

    event, param = ['','']
    if len(rows) > 0 and rows[0]['par_Value'] != 'finished':        
        event = rows[0]['par_Value'].split('|')[0]
        param = rows[0]['par_Value'].split('|')[1]
    else:
        return

    if event == 'test':
        handle_test(param)
    if event == 'run':
        handle_run(param)

    # clear event execution flag
    sql.execute ("UPDATE Parameters SET par_Value='finished' WHERE par_ID='Front_Event'")        

    # commit to DB  
    db.commitDB()

#-------------------------------------------------------------------------------
def handle_run(runType):
    global last_network_scan

    mylog('info', ['[', timeNow(), '] START Run: ', runType])  

    if runType == 'ENABLE_ARPSCAN':
        last_network_scan = now_minus_24h        

    mylog('info', ['[', timeNow(), '] END Run: ', runType])

#-------------------------------------------------------------------------------
def handle_test(testType):

    mylog('info', ['[', timeNow(), '] START Test: ', testType])    

    # Open text sample    
    sample_txt = get_file_content(pialertPath + '/back/report_sample.txt')

    # Open html sample     
    sample_html = get_file_content(pialertPath + '/back/report_sample.html')

    # Open json sample and get only the payload part      
    sample_json_payload = json.loads(get_file_content(pialertPath + '/back/webhook_json_sample.json'))[0]["body"]["attachments"][0]["text"]      
    
    if testType == 'REPORT_MAIL':
        send_email(sample_txt, sample_html)
    if testType == 'REPORT_WEBHOOK':
        send_webhook (sample_json_payload, sample_txt)
    if testType == 'REPORT_APPRISE':
        send_apprise (sample_html, sample_txt) 
    if testType == 'REPORT_NTFY':
        send_ntfy (sample_txt)
    if testType == 'REPORT_PUSHSAFER':
        send_pushsafer (sample_txt)

    mylog('info', ['[', timeNow(), '] END Test: ', testType])






#-------------------------------------------------------------------------------
def isNewVersion(db):   
    global newVersionAvailable

    if newVersionAvailable == False:    

        f = open(pialertPath + '/front/buildtimestamp.txt', 'r') 
        buildTimestamp = int(f.read().strip())
        f.close() 

        data = ""

        try:
            url = requests.get("https://api.github.com/repos/jokob-sk/Pi.Alert/releases")
            text = url.text
            data = json.loads(text)
        except requests.exceptions.ConnectionError as e:
            mylog('info', ["    Couldn't check for new release."]) 
            data = ""
        
        # make sure we received a valid response and not an API rate limit exceeded message
        if data != "" and len(data) > 0 and isinstance(data, list) and "published_at" in data[0]:        

            dateTimeStr = data[0]["published_at"]            

            realeaseTimestamp = int(datetime.datetime.strptime(dateTimeStr, '%Y-%m-%dT%H:%M:%SZ').strftime('%s'))            

            if realeaseTimestamp > buildTimestamp + 600:        
                mylog('none', ["    New version of the container available!"])
                newVersionAvailable = True 
                updateState(db, 'Back_New_Version_Available', str(newVersionAvailable))                

    return newVersionAvailable


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# Plugins
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
def run_plugin_scripts(db, runType):
    
    global plugins, tz, mySchedules

    # Header
    updateState(db,"Run: Plugins")

    mylog('debug', ['     [Plugins] Check if any plugins need to be executed on run type: ', runType])

    for plugin in plugins:

        shouldRun = False

        set = get_plugin_setting(plugin, "RUN")
        if set != None and set['value'] == runType:
            if runType != "schedule":
                shouldRun = True
            elif  runType == "schedule":
                # run if overdue scheduled time   
                prefix = plugin["unique_prefix"]

                #  check scheduels if any contains a unique plugin prefix matching the current plugin
                for schd in mySchedules:
                    if schd.service == prefix:          
                        # Check if schedule overdue
                        shouldRun = schd.runScheduleCheck()  
                        if shouldRun:
                            # note the last time the scheduled plugin run was executed
                            schd.last_run = datetime.datetime.now(tz).replace(microsecond=0)

        if shouldRun:            
                        
            print_plugin_info(plugin, ['display_name'])
            mylog('debug', ['     [Plugins] CMD: ', get_plugin_setting(plugin, "CMD")["value"]])
            execute_plugin(plugin) 

#-------------------------------------------------------------------------------
# Cron-like Scheduling


#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    sys.exit(main())       
