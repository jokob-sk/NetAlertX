#!/usr/bin/env python
#
#-------------------------------------------------------------------------------
#  Pi.Alert  v2.70  /  2021-02-01
#  Open Source Network Guard / WIFI & LAN intrusion detector 
#
#  pialert.py - Back module. Network scanner
#-------------------------------------------------------------------------------
#  Puche 2021        pi.alert.application@gmail.com        GNU GPLv3
#-------------------------------------------------------------------------------


#===============================================================================
# IMPORTS
#===============================================================================
from __future__ import print_function
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import sys
import subprocess
import os
import re
import time
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


# sys.stdout = open('pialert_new.log', 'w')
# sys.stderr = sys.stdout

#===============================================================================
# CONFIG CONSTANTS
#===============================================================================
PIALERT_BACK_PATH = os.path.dirname(os.path.abspath(__file__))
PIALERT_PATH = PIALERT_BACK_PATH + "/.."
STOPARPSCAN = PIALERT_PATH + "/db/setting_stoparpscan"

if (sys.version_info > (3,0)):
    exec(open(PIALERT_PATH + "/config/version.conf").read())
    exec(open(PIALERT_PATH + "/config/pialert.conf").read())
else:
    execfile (PIALERT_PATH + "/config/version.conf")
    execfile (PIALERT_PATH + "/config/pialert.conf")

# INITIALIZE ALL CONSTANTS from pialert.conf

# GENERAL
# keep 90 days of network activity if not specified how many days to keep
try:
    strdaystokeepEV = str(DAYS_TO_KEEP_EVENTS)
except NameError: # variable not defined, use a default
    strdaystokeepEV = str(90)

# Which sections to include in the reports. Include everything by default
try:
    includedSections = INCLUDED_SECTIONS
except NameError:
    includedSections = ['internet', 'new_devices', 'down_devices', 'events']


# WEBHOOKS
# HTTP request method for the webhook (GET, POST...)
try:
    webhookRequestMethod = WEBHOOK_REQUEST_METHOD
except NameError: 
    webhookRequestMethod = 'GET'

# payload type for the webhook request
try:
    webhookPayload = WEBHOOK_PAYLOAD
except NameError: 
    webhookPayload = 'json'


# NTFY
try:
    ntfyUser = NTFY_USER
except NameError: 
    ntfyUser = ''

try:
    ntfyPassword = NTFY_PASSWORD
except NameError:
    ntfyPassword = ''

try:
    ntfyTopic = NTFY_TOPIC
except NameError: 
    ntfyTopic = ''

try:
    ntfyHost = NTFY_HOST
except NameError: 
    ntfyHost = 'https://ntfy.sh'


# MQTT
try:
    reportMQTT = REPORT_MQTT
except NameError: 
    reportMQTT = False

try:
    mqttBroker = MQTT_BROKER
except NameError: 
    mqttBroker = ''

try:
    mqttPort = MQTT_PORT
except NameError: 
    mqttPort = ''

try:
    mqttTopic = MQTT_TOPIC
except NameError: 
    mqttTopic = ''

try:
    mqttClientId = MQTT_CLIENT_ID
except NameError: 
    mqttClientId = 'PiAlert'

try:
    mqttUser = MQTT_USER
except NameError: 
    mqttUser = ''

try:
    mqttPassword = MQTT_PASSWORD
except NameError: 
    mqttPassword = ''

try:
    mqttQoS = MQTT_QOS
except NameError: 
    mqttQoS = 0



#===============================================================================
# MAIN
#===============================================================================
cycle = ""
check_report = [1, "internet_IP", "update_vendors_silent"]
network_scan_minutes = 5
mqtt_thread_up = False

# timestamps of last execution times
time_now = datetime.datetime.now()
now_minus_24h = time_now - timedelta(hours = 24)

last_network_scan = now_minus_24h
last_internet_IP_scan = now_minus_24h
last_run = now_minus_24h
last_cleanup = now_minus_24h
last_update_vendors = time_now - timedelta(days = 7)

debug_once = False

def main ():
    # Initialize global variables
    global time_now, cycle, last_network_scan, last_internet_IP_scan, last_run, last_cleanup, last_update_vendors, network_scan_minutes, mqtt_thread_up
    # second set of global variables
    global startTime, log_timestamp, sql_connection, includedSections, sql
    
    while True:
        # update NOW time
        time_now = datetime.datetime.now()

        # proceed if 1 minute passed
        if last_run + timedelta(minutes=1) < time_now :

             # last time any scan or maintennace was run
            last_run = time_now

            reporting = False

            # Header
            print ('\nLoop start')
            print ('---------------------------------------------------------')
            
            log_timestamp  = time_now        

            # DB
            sql_connection = None
            sql            = None

            # Timestamp
            startTime = time_now
            startTime = startTime.replace (second=0, microsecond=0)

            # Upgrade DB if needed
            upgradeDB()

            # determine run/scan type based on passed time
            if last_internet_IP_scan + timedelta(minutes=3) < time_now:
                cycle = 'internet_IP'                
                last_internet_IP_scan = time_now
                reporting = check_internet_IP()

            # Update vendors once a week
            if last_update_vendors + timedelta(days = 7) < time_now:
                last_update_vendors = time_now
                cycle = 'update_vendors'
                update_devices_MAC_vendors()

            if last_network_scan + timedelta(minutes=network_scan_minutes) < time_now and os.path.exists(STOPARPSCAN) == False:
                last_network_scan = time_now
                cycle = 1 # network scan
                scan_network() 

            # clean up the DB once a day
            if last_cleanup + timedelta(hours = 24) < time_now:
                last_cleanup = time_now
                cycle = 'cleanup'  
                cleanup_database()       
            
            # Reporting   
            if cycle in check_report:         
                email_reporting()

            # Close SQL
            closeDB()            

            # Final menssage
            if cycle != "":
                print ('\nFinished cycle: ', cycle, '\n')
                cycle = ""

            # Footer
            print ('\nLoop end')
            print ('---------------------------------------------------------')     
        else:
            # do something
            cycle = ""
            print ('\n Wait 20s')

        #loop  - recursion    
        time.sleep(20) # wait for N seconds      

    
#===============================================================================
# INTERNET IP CHANGE
#===============================================================================
def check_internet_IP ():
    reporting = False

    # Header
    print ('Check Internet IP')
    print ('    Timestamp:', startTime )

    # Get Internet IP
    print ('\n    Retrieving Internet IP...')
    internet_IP = get_internet_IP()
    # TESTING - Force IP
        # internet_IP = "1.2.3.4"

    # Check result = IP
    if internet_IP == "" :
        print ('    Error retrieving Internet IP')
        print ('    Exiting...\n')
        return False
    print ('   ', internet_IP)

    # Get previous stored IP
    print ('\n    Retrieving previous IP...')
    openDB()
    previous_IP = get_previous_internet_IP ()
    print ('   ', previous_IP)

    # Check IP Change
    if internet_IP != previous_IP :
        print ('    Saving new IP')
        save_new_internet_IP (internet_IP)
        print ('        IP updated')
        reporting = True
    else :
        print ('    No changes to perform')
    closeDB()

    # Get Dynamic DNS IP
    if DDNS_ACTIVE :
        print ('\n    Retrieving Dynamic DNS IP...')
        dns_IP = get_dynamic_DNS_IP()

        # Check Dynamic DNS IP
        if dns_IP == "" :
            print ('    Error retrieving Dynamic DNS IP')
            print ('    Exiting...\n')
            return False
        print ('   ', dns_IP)

        # Check DNS Change
        if dns_IP != internet_IP :
            print ('    Updating Dynamic DNS IP...')
            message = set_dynamic_DNS_IP ()
            print ('       ', message)
            reporting = True
        else :
            print ('    No changes to perform')
    else :
        print ('\n    Skipping Dynamic DNS update...')
    
    return reporting


#-------------------------------------------------------------------------------
def get_internet_IP ():
    # BUGFIX #46 - curl http://ipv4.icanhazip.com repeatedly is very slow
    # Using 'dig'
    dig_args = ['dig', '+short', '-4', 'myip.opendns.com', '@resolver1.opendns.com']
    try:
        cmd_output = subprocess.check_output (dig_args, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        print(e.output)
        cmd_output = '' # no internet
    

    ## BUGFIX #12 - Query IPv4 address (not IPv6)
    ## Using 'curl' instead of 'dig'
    ## curl_args = ['curl', '-s', 'https://diagnostic.opendns.com/myip']
    #curl_args = ['curl', '-s', QUERY_MYIP_SERVER]
    #cmd_output = subprocess.check_output (curl_args, universal_newlines=True)

    # Check result is an IP
    IP = check_IP_format (cmd_output)
    return IP

#-------------------------------------------------------------------------------
def get_dynamic_DNS_IP ():
    # Using OpenDNS server
        # dig_args = ['dig', '+short', DDNS_DOMAIN, '@resolver1.opendns.com']

    # Using default DNS server
    dig_args = ['dig', '+short', DDNS_DOMAIN]

    try:
        # try runnning a subprocess
        dig_output = subprocess.check_output (dig_args, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        print(e.output)
        dig_output = '' # probably no internet

    # Check result is an IP
    IP = check_IP_format (dig_output)
    return IP

#-------------------------------------------------------------------------------
def set_dynamic_DNS_IP ():
    try:
        # try runnning a subprocess
        # Update Dynamic IP
        curl_output = subprocess.check_output (['curl', '-s',
            DDNS_UPDATE_URL +
            'username='  + DDNS_USER +
            '&password=' + DDNS_PASSWORD +
            '&hostname=' + DDNS_DOMAIN],
            universal_newlines=True)
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        print(e.output)
        curl_output = ""    
    
    return curl_output
    
#-------------------------------------------------------------------------------
def get_previous_internet_IP ():
    # get previos internet IP stored in DB
    sql.execute ("SELECT dev_LastIP FROM Devices WHERE dev_MAC = 'Internet' ")
    previous_IP = sql.fetchone()[0]

    # return previous IP
    return previous_IP

#-------------------------------------------------------------------------------
def save_new_internet_IP (pNewIP):
    # Log new IP into logfile
    append_line_to_file (LOG_PATH + '/IP_changes.log',
        str(startTime) +'\t'+ pNewIP +'\n')

    # Save event
    sql.execute ("""INSERT INTO Events (eve_MAC, eve_IP, eve_DateTime,
                        eve_EventType, eve_AdditionalInfo,
                        eve_PendingAlertEmail)
                    VALUES ('Internet', ?, ?, 'Internet IP Changed',
                        'Previous Internet IP: '|| ?, 1) """,
                    (pNewIP, startTime, get_previous_internet_IP() ) )

    # Save new IP
    sql.execute ("""UPDATE Devices SET dev_LastIP = ?
                    WHERE dev_MAC = 'Internet' """,
                    (pNewIP,) )

    # commit changes
    sql_connection.commit()
    
#-------------------------------------------------------------------------------
def check_IP_format (pIP):
    # Check IP format
    IPv4SEG  = r'(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])'
    IPv4ADDR = r'(?:(?:' + IPv4SEG + r'\.){3,3}' + IPv4SEG + r')'
    IP = re.search(IPv4ADDR, pIP)

    # Return error if not IP
    if IP is None :
        return ""

    # Return IP
    return IP.group(0)


#===============================================================================
# Cleanup Online History chart
#===============================================================================
def cleanup_database ():
    # Header
    print ('Cleanup Database')
    print ('    Timestamp:', startTime )

    openDB()    
   
    # Cleanup Online History
    print ('    Cleanup Online_History...')
    sql.execute ("DELETE FROM Online_History WHERE Scan_Date <= date('now', '-1 day')")
    print ('    Optimize Database...')

    # Cleanup Events
    print ('    Cleanup Events, up to the lastest '+strdaystokeepEV+' days...')
    sql.execute ("DELETE FROM Events WHERE eve_DateTime <= date('now', '-"+strdaystokeepEV+" day')")

    # Shrink DB
    print ('    Shrink Database...')
    sql.execute ("VACUUM;")

    closeDB()

#===============================================================================
# UPDATE DEVICE MAC VENDORS
#===============================================================================
def update_devices_MAC_vendors (pArg = ''):
    # Header
    print ('Update HW Vendors')
    print ('    Timestamp:', startTime )

    # Update vendors DB (iab oui)
    print ('\nUpdating vendors DB (iab & oui)...')
    # update_args = ['sh', PIALERT_BACK_PATH + '/update_vendors.sh', ' > ', LOG_PATH +  '/update_vendors.log',    '2>&1']
    update_args = ['sh', PIALERT_BACK_PATH + '/update_vendors.sh', pArg]

    try:
        # try runnning a subprocess
        update_output = subprocess.check_output (update_args)
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        print(e.output)        
    
    # DEBUG
        # update_args = ['./vendors_db_update.sh']
        # subprocess.call (update_args, shell=True)

    # Initialize variables
    recordsToUpdate = []
    ignored = 0
    notFound = 0

    # All devices loop
    print ('\nSearching devices vendor', end='')
    openDB()
    for device in sql.execute ("SELECT * FROM Devices") :
        # Search vendor in HW Vendors DB
        vendor = query_MAC_vendor (device['dev_MAC'])
        if vendor == -1 :
            notFound += 1
        elif vendor == -2 :
            ignored += 1
        else :
            recordsToUpdate.append ([vendor, device['dev_MAC']])
        # progress bar
        print ('.', end='')
        sys.stdout.flush()
            
    # Print log
    print ('')
    print ("    Devices Ignored:  ", ignored)
    print ("    Vendors Not Found:", notFound)
    print ("    Vendors updated:  ", len(recordsToUpdate) )
    # DEBUG - print list of record to update
        # print (recordsToUpdate)

    # update devices
    sql.executemany ("UPDATE Devices SET dev_Vendor = ? WHERE dev_MAC = ? ",
        recordsToUpdate )

    # DEBUG - print number of rows updated
        # print (sql.rowcount)

    # Close DB
    closeDB()

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
        grep_args = ['grep', '-i', mac, VENDORS_DB]
        # Execute command
        try:
            # try runnning a subprocess
            grep_output = subprocess.check_output (grep_args)
        except subprocess.CalledProcessError as e:
            # An error occured, handle it
            print(e.output)
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
    print ('Scan Devices')
    print ('    ScanCycle:', cycle)
    print ('    Timestamp:', startTime )

    # # Query ScanCycle properties
    print_log ('Query ScanCycle confinguration...')
    scanCycle_data = query_ScanCycle_Data (True)
    if scanCycle_data is None:
        print ('\n*************** ERROR ***************')
        print ('ScanCycle %s not found' % cycle )
        print ('    Exiting...\n')
        return False

    # ScanCycle data        
    cycle_interval  = scanCycle_data['cic_EveryXmin']
    
    # arp-scan command
    print ('\nScanning...')
    print ('    arp-scan Method...')
    print_log ('arp-scan starts...')
    arpscan_devices = execute_arpscan ()
    print_log ('arp-scan ends')
    
    # DEBUG - print number of rows updated    
    # print ('aspr-scan result:', len(arpscan_devices))

    # Pi-hole method
    print ('    Pi-hole Method...')
    openDB()
    print_log ('Pi-hole copy starts...')
    reporting = copy_pihole_network() or reporting

    # DHCP Leases method
    print ('    DHCP Leases Method...')
    reporting = read_DHCP_leases () or reporting

    # Load current scan data
    print ('\nProcessing scan results...')
    print_log ('Save scanned devices')
    save_scanned_devices (arpscan_devices, cycle_interval)
    
    # Print stats
    print_log ('Print Stats')
    print_scan_stats()
    print_log ('Stats end')

    # Create Events
    print ('\nUpdating DB Info...')
    print ('    Sessions Events (connect / discconnect) ...')
    insert_events()

    # Create New Devices
    # after create events -> avoid 'connection' event
    print ('    Creating new devices...')
    create_new_devices ()

    # Update devices info
    print ('    Updating Devices Info...')
    update_devices_data_from_scan ()

    # Resolve devices names
    print_log ('   Resolve devices names...')
    update_devices_names()

    # Void false connection - disconnections
    print ('    Voiding false (ghost) disconnections...')
    void_ghost_disconnections ()
  
    # Pair session events (Connection / Disconnection)
    print ('    Pairing session events (connection / disconnection) ...')
    pair_sessions_events()  
  
    # Sessions snapshot
    print ('    Creating sessions snapshot...')
    create_sessions_snapshot ()
  
    # Skip repeated notifications
    print ('    Skipping repeated notifications...')
    skip_repeated_notifications ()
  
    # Commit changes
    sql_connection.commit()
    closeDB()

    return reporting

#-------------------------------------------------------------------------------
def query_ScanCycle_Data (pOpenCloseDB = False):
    # Check if is necesary open DB
    if pOpenCloseDB :
        openDB()

    # Query Data
    sql.execute ("""SELECT cic_arpscanCycles, cic_EveryXmin
                    FROM ScanCycles
                    WHERE cic_ID = ? """, (cycle,))
    sqlRow = sql.fetchone()

    # Check if is necesary close DB
    if pOpenCloseDB :
        closeDB()

    # Return Row
    return sqlRow

#-------------------------------------------------------------------------------
def execute_arpscan ():

    # output of possible multiple interfaces
    arpscan_output = ""

    # multiple interfaces
    if type(SCAN_SUBNETS) is list:
        print("    arp-scan: Multiple interfaces")        
        for interface in SCAN_SUBNETS :            
            arpscan_output += execute_arpscan_on_interface (interface)
    # one interface only
    else:
        print("    arp-scan: One interface")
        arpscan_output += execute_arpscan_on_interface (SCAN_SUBNETS)

    
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
    

    # DEBUG
        # print (devices_list)
        # print (unique_mac)
        # print (unique_devices)
        # print (len(devices_list))
        # print (len(unique_mac))
        # print (len(unique_devices))

    # return list
    return unique_devices

#-------------------------------------------------------------------------------
def execute_arpscan_on_interface (SCAN_SUBNETS):
    # #101 - arp-scan subnet configuration
    # Prepare command arguments
    subnets = SCAN_SUBNETS.strip().split()
    # Retry is 6 to avoid false offline devices
    arpscan_args = ['sudo', 'arp-scan', '--ignoredups', '--retry=6'] + subnets

    # Execute command
    try:
        # try runnning a subprocess
        result = subprocess.check_output (arpscan_args, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        print(e.output)
        result = ""

    return result

#-------------------------------------------------------------------------------
def copy_pihole_network ():
    # check if Pi-hole is active
    if not PIHOLE_ACTIVE :
        return    

    # Open Pi-hole DB
    sql.execute ("ATTACH DATABASE '"+ PIHOLE_DB +"' AS PH")

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
    reporting = False

    # check DHCP Leases is active
    if not DHCP_ACTIVE :
        return False   
            
    # Read DHCP Leases
    # Bugfix #1 - dhcp.leases: lines with different number of columns (5 col)
    data = []
    with open(DHCP_LEASES, 'r') as f:
        for line in f:
            reporting = True
            row = line.rstrip().split()
            if len(row) == 5 :
                data.append (row)
    # with open(DHCP_LEASES) as f:
    #    reader = csv.reader(f, delimiter=' ')
    #    data = [(col1, col2, col3, col4, col5)
    #            for col1, col2, col3, col4, col5 in reader]

    # Insert into PiAlert table
    sql.execute ("DELETE FROM DHCP_Leases")
    sql.executemany ("""INSERT INTO DHCP_Leases (DHCP_DateTime, DHCP_MAC,
                            DHCP_IP, DHCP_Name, DHCP_MAC2)
                        VALUES (?, ?, ?, ?, ?)
                     """, data)
    # DEBUG
        # print (sql.rowcount)
    return reporting

#-------------------------------------------------------------------------------
def save_scanned_devices (p_arpscan_devices, p_cycle_interval):
    cycle = 1 # always 1, only one cycle supported
    # Delete previous scan data
    sql.execute ("DELETE FROM CurrentScan WHERE cur_ScanCycle = ?",
                (cycle,))

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
    internet_IP = get_internet_IP()
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
    print ('    Devices Detected.......:', str (sql.fetchone()[0]) )

    # Devices arp-scan
    sql.execute ("""SELECT COUNT(*) FROM CurrentScan
                    WHERE cur_ScanMethod='arp-scan' AND cur_ScanCycle = ? """,
                    (cycle,))
    print ('        arp-scan Method....:', str (sql.fetchone()[0]) )

    # Devices Pi-hole
    sql.execute ("""SELECT COUNT(*) FROM CurrentScan
                    WHERE cur_ScanMethod='PiHole' AND cur_ScanCycle = ? """,
                    (cycle,))
    print ('        Pi-hole Method.....: +' + str (sql.fetchone()[0]) )

    # New Devices
    sql.execute ("""SELECT COUNT(*) FROM CurrentScan
                    WHERE cur_ScanCycle = ? 
                      AND NOT EXISTS (SELECT 1 FROM Devices
                                      WHERE dev_MAC = cur_MAC) """,
                    (cycle,))
    print ('        New Devices........: ' + str (sql.fetchone()[0]) )

    # Devices in this ScanCycle
    sql.execute ("""SELECT COUNT(*) FROM Devices, CurrentScan
                    WHERE dev_MAC = cur_MAC AND dev_ScanCycle = cur_ScanCycle
                      AND dev_ScanCycle = ? """,
                    (cycle,))
    print ('')
    print ('    Devices in this cycle..: ' + str (sql.fetchone()[0]) )

    # Down Alerts
    sql.execute ("""SELECT COUNT(*) FROM Devices
                    WHERE dev_AlertDeviceDown = 1
                      AND dev_ScanCycle = ?
                      AND NOT EXISTS (SELECT 1 FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC
                                        AND dev_ScanCycle = cur_ScanCycle) """,
                    (cycle,))
    print ('        Down Alerts........: ' + str (sql.fetchone()[0]) )

    # New Down Alerts
    sql.execute ("""SELECT COUNT(*) FROM Devices
                    WHERE dev_AlertDeviceDown = 1
                      AND dev_PresentLastScan = 1
                      AND dev_ScanCycle = ?
                      AND NOT EXISTS (SELECT 1 FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC
                                        AND dev_ScanCycle = cur_ScanCycle) """,
                    (cycle,))
    print ('        New Down Alerts....: ' + str (sql.fetchone()[0]) )

    # New Connections
    sql.execute ("""SELECT COUNT(*) FROM Devices, CurrentScan
                    WHERE dev_MAC = cur_MAC AND dev_ScanCycle = cur_ScanCycle
                      AND dev_PresentLastScan = 0
                      AND dev_ScanCycle = ? """,
                    (cycle,))
    print ('        New Connections....: ' + str ( sql.fetchone()[0]) )

    # Disconnections
    sql.execute ("""SELECT COUNT(*) FROM Devices
                    WHERE dev_PresentLastScan = 1
                      AND dev_ScanCycle = ?
                      AND NOT EXISTS (SELECT 1 FROM CurrentScan
                                      WHERE dev_MAC = cur_MAC
                                        AND dev_ScanCycle = cur_ScanCycle) """,
                    (cycle,))
    print ('        Disconnections.....: ' + str ( sql.fetchone()[0]) )

    # IP Changes
    sql.execute ("""SELECT COUNT(*) FROM Devices, CurrentScan
                    WHERE dev_MAC = cur_MAC AND dev_ScanCycle = cur_ScanCycle
                      AND dev_ScanCycle = ?
                      AND dev_LastIP <> cur_IP """,
                    (cycle,))
    print ('        IP Changes.........: ' + str ( sql.fetchone()[0]) )

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
                    WHERE (dev_Name = "(unknown)"
                           OR dev_Name = ""
                           OR dev_Name IS NULL)
                      AND EXISTS (SELECT 1 FROM PiHole_Network
                                  WHERE PH_MAC = dev_MAC
                                    AND PH_NAME IS NOT NULL
                                    AND PH_NAME <> '') """)

    # DHCP Leases - Update (unknown) Name
    sql.execute ("""UPDATE Devices
                    SET dev_NAME = (SELECT DHCP_Name FROM DHCP_Leases
                                    WHERE DHCP_MAC = dev_MAC)
                    WHERE (dev_Name = "(unknown)"
                           OR dev_Name = ""
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

    # DEBUG - print list of record to update
        # print (recordsToUpdate)
    sql.executemany ("UPDATE Devices SET dev_Vendor = ? WHERE dev_MAC = ? ",
        recordsToUpdate )

    print_log ('Update devices end')

#-------------------------------------------------------------------------------
# Feature #43 - Resolve name for unknown devices
def update_devices_names ():
    # Initialize variables
    recordsToUpdate = []
    ignored = 0
    notFound = 0

    # Devices without name
    print ('        Trying to resolve devices without name...', end='')
    # BUGFIX #97 - Updating name of Devices w/o IP
    for device in sql.execute ("SELECT * FROM Devices WHERE dev_Name IN ('(unknown)','') AND dev_LastIP <> '-'") :
        # Resolve device name
        newName = resolve_device_name (device['dev_MAC'], device['dev_LastIP'])
       
        if newName == -1 :
            notFound += 1
        elif newName == -2 :
            ignored += 1
        else :
            recordsToUpdate.append ([newName, device['dev_MAC']])
        # progress bar
        print ('.', end='')
        sys.stdout.flush()
            
    # Print log
    print ('')
    print ("        Names updated:  ", len(recordsToUpdate) )
    # DEBUG - print list of record to update
        # print (recordsToUpdate)

    # update devices
    sql.executemany ("UPDATE Devices SET dev_Name = ? WHERE dev_MAC = ? ", recordsToUpdate )

    # DEBUG - print number of rows updated
        # print (sql.rowcount)

#-------------------------------------------------------------------------------
def resolve_device_name (pMAC, pIP):
    try :
        pMACstr = str(pMAC)
        
        # Check MAC parameter
        mac = pMACstr.replace (':','')
        if len(pMACstr) != 17 or len(mac) != 12 :
            return -2

        # DEBUG
        # print (pMAC, pIP)

        # Resolve name with DIG
        dig_args = ['dig', '+short', '-x', pIP]

        # Execute command
        try:
            # try runnning a subprocess
            newName = subprocess.check_output (dig_args, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            # An error occured, handle it
            print(e.output)
            newName = "Error - check logs"

        # Check returns
        newName = newName.strip()
        if len(newName) == 0 :
            return -2
            
        # Eliminate local domain
        if newName.endswith('.') :
            newName = newName[:-1]
        if newName.endswith('.lan') :
            newName = newName[:-4]
        if newName.endswith('.local') :
            newName = newName[:-6]
        if newName.endswith('.home') :
            newName = newName[:-5]

        # Return newName
        return newName

    # not Found
    except subprocess.CalledProcessError :
        return -1            

#-------------------------------------------------------------------------------
def void_ghost_disconnections ():
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

#-------------------------------------------------------------------------------
def pair_sessions_events ():
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

#-------------------------------------------------------------------------------
def create_sessions_snapshot ():
    # Clean sessions snapshot
    print_log ('Sessions Snapshot - 1 Clean')
    sql.execute ("DELETE FROM SESSIONS" )

    # Insert sessions
    print_log ('Sessions Snapshot - 2 Insert')
    sql.execute ("""INSERT INTO Sessions
                    SELECT * FROM Convert_Events_to_Sessions""" )

#    OLD FORMAT INSERT IN TWO PHASES
#    PERFORMACE BETTER THAN SELECT WITH UNION
#
#    # Insert sessions from first query
#    print_log ('Sessions Snapshot - 2 Query 1')
#    sql.execute ("""INSERT INTO Sessions
#                    SELECT * FROM Convert_Events_to_Sessions_Phase1""" )
#
#    # Insert sessions from first query
#    print_log ('Sessions Snapshot - 3 Query 2')
#    sql.execute ("""INSERT INTO Sessions
#                    SELECT * FROM Convert_Events_to_Sessions_Phase2""" )

    print_log ('Sessions end')

#-------------------------------------------------------------------------------
def skip_repeated_notifications ():
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


#===============================================================================
# REPORTING
#===============================================================================
# create a json for webhook and mqtt notifications to provide further integration options  
json_final = []

def email_reporting ():
    global mail_text
    global mail_html
    # Reporting section
    print ('\nCheck if something to report...')
    openDB()

    # prepare variables for JSON construction
    json_internet = []
    json_new_devices = []
    json_down_devices = []
    json_events = []



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
    template_file = open(PIALERT_BACK_PATH + '/report_template.txt', 'r') 
    mail_text = template_file.read() 
    template_file.close() 

    # Open html Template
    template_file = open(PIALERT_BACK_PATH + '/report_template.html', 'r') 
    mail_html = template_file.read() 
    template_file.close() 

    # Report Header & footer
    timeFormated = startTime.strftime ('%Y-%m-%d %H:%M')
    mail_text = mail_text.replace ('<REPORT_DATE>', timeFormated)
    mail_html = mail_html.replace ('<REPORT_DATE>', timeFormated)

    # mail_text = mail_text.replace ('<SCAN_CYCLE>', cycle )
    # mail_html = mail_html.replace ('<SCAN_CYCLE>', cycle )

    mail_text = mail_text.replace ('<SERVER_NAME>', socket.gethostname() )
    mail_html = mail_html.replace ('<SERVER_NAME>', socket.gethostname() )
    
    # mail_text = mail_text.replace ('<PIALERT_VERSION>', VERSION )
    # mail_html = mail_html.replace ('<PIALERT_VERSION>', VERSION )

    # mail_text = mail_text.replace ('<PIALERT_VERSION_DATE>', VERSION_DATE )
    # mail_html = mail_html.replace ('<PIALERT_VERSION_DATE>', VERSION_DATE )

    # mail_text = mail_text.replace ('<PIALERT_YEAR>', VERSION_YEAR )
    # mail_html = mail_html.replace ('<PIALERT_YEAR>', VERSION_YEAR )

    # Compose Internet Section
    
    mail_section_Internet = False
    mail_text_Internet = ''
    mail_html_Internet = ''
    text_line_template = '{} \t{}\t{}\t{}\n'
    html_line_template = '<tr>\n'+ \
        '  <td> <a href="{}{}"> {} </a> </td>\n  <td> {} </td>\n'+ \
        '  <td style="font-size: 24px; color:#D02020"> {} </td>\n'+ \
        '  <td> {} </td>\n</tr>\n'

    sql.execute ("""SELECT * FROM Events
                    WHERE eve_PendingAlertEmail = 1 AND eve_MAC = 'Internet'
                    ORDER BY eve_DateTime""")

    
    for eventAlert in sql :
        mail_section_Internet = 'internet' in includedSections
        # collect "internet" (IP changes) for the webhook json   
        json_internet = add_json_list (eventAlert, json_internet)

        mail_text_Internet += text_line_template.format (
            'Event:', eventAlert['eve_EventType'], 'Time:', eventAlert['eve_DateTime'],
            'IP:', eventAlert['eve_IP'], 'More Info:', eventAlert['eve_AdditionalInfo'])
        mail_html_Internet += html_line_template.format (
            REPORT_DEVICE_URL, eventAlert['eve_MAC'],
            eventAlert['eve_EventType'], eventAlert['eve_DateTime'],
            eventAlert['eve_IP'], eventAlert['eve_AdditionalInfo'])


    format_report_section (mail_section_Internet, 'SECTION_INTERNET',
        'TABLE_INTERNET', mail_text_Internet, mail_html_Internet)


    # Compose New Devices Section
    mail_section_new_devices = False
    mail_text_new_devices = ''
    mail_html_new_devices = ''
    text_line_template = '{}\t{}\n\t{}\t{}\n\t{}\t{}\n\t{}\t{}\n\t{}\t{}\n\n'
    html_line_template    = '<tr>\n'+ \
        '  <td> <a href="{}{}"> {} </a> </td>\n  <td> {} </td>\n'+\
        '  <td> {} </td>\n  <td> {} </td>\n  <td> {} </td>\n</tr>\n'
    
    sql.execute ("""SELECT * FROM Events_Devices
                    WHERE eve_PendingAlertEmail = 1
                      AND eve_EventType = 'New Device'
                    ORDER BY eve_DateTime""")

    for eventAlert in sql :
        mail_section_new_devices = 'new_devices' in includedSections
        # collect "new_devices" for the webhook json  
        json_new_devices = add_json_list (eventAlert, json_new_devices)

        mail_text_new_devices += text_line_template.format (
            'Name: ', eventAlert['dev_Name'], 'MAC: ', eventAlert['eve_MAC'], 'IP: ', eventAlert['eve_IP'],
            'Time: ', eventAlert['eve_DateTime'], 'More Info: ', eventAlert['eve_AdditionalInfo'])
        mail_html_new_devices += html_line_template.format (
            REPORT_DEVICE_URL, eventAlert['eve_MAC'], eventAlert['eve_MAC'],
            eventAlert['eve_DateTime'], eventAlert['eve_IP'],
            eventAlert['dev_Name'], eventAlert['eve_AdditionalInfo'])
 
    format_report_section (mail_section_new_devices, 'SECTION_NEW_DEVICES',
        'TABLE_NEW_DEVICES', mail_text_new_devices, mail_html_new_devices)


    # Compose Devices Down Section
    mail_section_devices_down = False
    mail_text_devices_down = ''
    mail_html_devices_down = ''
    text_line_template = '{}\t{}\n\t{}\t{}\n\t{}\t{}\n\t{}\t{}\n\n'
    html_line_template     = '<tr>\n'+ \
        '  <td> <a href="{}{}"> {} </a>  </td>\n  <td> {} </td>\n'+ \
        '  <td> {} </td>\n  <td> {} </td>\n</tr>\n'

    sql.execute ("""SELECT * FROM Events_Devices
                    WHERE eve_PendingAlertEmail = 1
                      AND eve_EventType = 'Device Down'
                    ORDER BY eve_DateTime""")

    for eventAlert in sql :
        mail_section_devices_down = 'down_devices' in includedSections
        # collect "down_devices" for the webhook json
        json_down_devices = add_json_list (eventAlert, json_down_devices)

        mail_text_devices_down += text_line_template.format (
            'Name: ', eventAlert['dev_Name'], 'MAC: ', eventAlert['eve_MAC'],
            'Time: ', eventAlert['eve_DateTime'],'IP: ', eventAlert['eve_IP'])
        mail_html_devices_down += html_line_template.format (
            REPORT_DEVICE_URL, eventAlert['eve_MAC'], eventAlert['eve_MAC'],
            eventAlert['eve_DateTime'], eventAlert['eve_IP'],
            eventAlert['dev_Name'])

    format_report_section (mail_section_devices_down, 'SECTION_DEVICES_DOWN',
        'TABLE_DEVICES_DOWN', mail_text_devices_down, mail_html_devices_down)


    # Compose Events Section
    mail_section_events = False
    mail_text_events   = ''
    mail_html_events   = ''
    text_line_template = '{}\t{}\n\t{}\t{}\n\t{}\t{}\n\t{}\t{}\n\t{}\t{}\n\t{}\t{}\n\n'
    html_line_template = '<tr>\n  <td>'+ \
            ' <a href="{}{}"> {} </a> </td>\n  <td> {} </td>\n'+ \
            '  <td> {} </td>\n  <td> {} </td>\n  <td> {} </td>\n'+ \
            '  <td> {} </td>\n</tr>\n'

    sql.execute ("""SELECT * FROM Events_Devices
                    WHERE eve_PendingAlertEmail = 1
                      AND eve_EventType IN ('Connected','Disconnected',
                          'IP Changed')
                    ORDER BY eve_DateTime""")

    for eventAlert in sql :
        mail_section_events = 'events' in includedSections
        # collect "events" for the webhook json
        json_events = add_json_list (eventAlert, json_events)
          
        mail_text_events += text_line_template.format (
            'Name: ', eventAlert['dev_Name'], 'MAC: ', eventAlert['eve_MAC'], 
            'IP: ', eventAlert['eve_IP'],'Time: ', eventAlert['eve_DateTime'],
            'Event: ', eventAlert['eve_EventType'],'More Info: ', eventAlert['eve_AdditionalInfo'])
        mail_html_events += html_line_template.format (
            REPORT_DEVICE_URL, eventAlert['eve_MAC'], eventAlert['eve_MAC'],
            eventAlert['eve_DateTime'], eventAlert['eve_IP'],
            eventAlert['eve_EventType'], eventAlert['dev_Name'],
            eventAlert['eve_AdditionalInfo'])

    format_report_section (mail_section_events, 'SECTION_EVENTS',
        'TABLE_EVENTS', mail_text_events, mail_html_events)


    json_final = {
                    "internet": json_internet,                        
                    "new_devices": json_new_devices,
                    "down_devices": json_down_devices,                        
                    "events": json_events
                    }    

    # DEBUG - Write output emails for testing
    #if True :
    #    write_file (LOG_PATH + '/report_output.txt', mail_text) 
    #    write_file (LOG_PATH + '/report_output.html', mail_html) 


    # Send Mail
    if mail_section_Internet == True or mail_section_new_devices == True \
    or mail_section_devices_down == True or mail_section_events == True :
        print ('\nChanges detected, sending reports...')

        if REPORT_MAIL :
            print ('    Sending report by email...')
            send_email (mail_text, mail_html)
        else :
            print ('    Skip mail...')
        if REPORT_APPRISE :
            print ('    Sending report by Apprise...')
            send_apprise (mail_html)
        else :
            print ('    Skip Apprise...')
        if REPORT_WEBHOOK :
            print ('    Sending report by webhook...')
            send_webhook (json_final, mail_text)
        else :
            print ('    Skip webhook...')
        if REPORT_NTFY :
            print ('    Sending report by NTFY...')
            send_ntfy (mail_text)
        else :
            print ('    Skip NTFY...')
        if REPORT_PUSHSAFER :
            print ('    Sending report by PUSHSAFER...')
            send_pushsafer (mail_text)
        else :
            print ('    Skip PUSHSAFER...')
        # Update MQTT entities
        if reportMQTT:
            print ('    Establishing MQTT thread...')                
            # mqtt_thread_up = True # prevent this code to be run multiple times concurrently
            # start_mqtt_thread ()                
            mqtt_start()        
        else :
            print ('    Skip MQTT...')
    else :
        print ('    No changes to report...')

    openDB()

    # Clean Pending Alert Events
    sql.execute ("""UPDATE Devices SET dev_LastNotification = ?
                    WHERE dev_MAC IN (SELECT eve_MAC FROM Events
                                      WHERE eve_PendingAlertEmail = 1)
                 """, (datetime.datetime.now(),) )
    sql.execute ("""UPDATE Events SET eve_PendingAlertEmail = 0
                    WHERE eve_PendingAlertEmail = 1""")

    # DEBUG - print number of rows updated
    print ('    Notifications:', sql.rowcount)

    # Commit changes
    sql_connection.commit()
    closeDB()
#-------------------------------------------------------------------------------
def send_ntfy (_Text):
    headers = {
        "Title": "Pi.Alert Notification",
        "Actions": "view, Open Dashboard, "+ REPORT_DASHBOARD_URL,
        "Priority": "urgent",
        "Tags": "warning"
    }
    # if username and password are set generate hash and update header
    if ntfyUser != "" and ntfyPassword != "":
	# Generate hash for basic auth
        usernamepassword = "{}:{}".format(ntfyUser,ntfyPassword)
        basichash = b64encode(bytes(ntfyUser + ':' + ntfyPassword, "utf-8")).decode("ascii")

	# add authorization header with hash
        headers["Authorization"] = "Basic {}".format(basichash)

    requests.post("{}/{}".format( ntfyHost, ntfyTopic),
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
def write_file (pPath, pText):
    # Write the text depending using the correct python version
    if sys.version_info < (3, 0):
        file = io.open (pPath , mode='w', encoding='utf-8')
        file.write ( pText.decode('unicode_escape') ) 
        file.close() 
    else:
        file = open (pPath, 'w', encoding='utf-8') 
        file.write (pText) 
        file.close() 

#-------------------------------------------------------------------------------
def append_file_binary (pPath, input):    
    file = open (pPath, 'ab') 
    file.write (input) 
    file.close() 

#-------------------------------------------------------------------------------
def append_line_to_file (pPath, pText):
    # append the line depending using the correct python version
    if sys.version_info < (3, 0):
        file = io.open (pPath , mode='a', encoding='utf-8')
        file.write ( pText.decode('unicode_escape') ) 
        file.close() 
    else:
        file = open (pPath, 'a', encoding='utf-8') 
        file.write (pText) 
        file.close() 

#-------------------------------------------------------------------------------
def send_email (pText, pHTML):
    # Compose email
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Pi.Alert Report'
    msg['From'] = REPORT_FROM
    msg['To'] = REPORT_TO
    msg.attach (MIMEText (pText, 'plain'))
    msg.attach (MIMEText (pHTML, 'html'))

    # Send mail
    smtp_connection = smtplib.SMTP (SMTP_SERVER, SMTP_PORT)
    smtp_connection.ehlo()
#    smtp_connection.starttls()
#    smtp_connection.ehlo()
#    smtp_connection.login (SMTP_USER, SMTP_PASS)
    if not SafeParseGlobalBool("SMTP_SKIP_TLS"):
        smtp_connection.starttls()
        smtp_connection.ehlo()
    if not SafeParseGlobalBool("SMTP_SKIP_LOGIN"):
        smtp_connection.login (SMTP_USER, SMTP_PASS)
    smtp_connection.sendmail (REPORT_FROM, REPORT_TO, msg.as_string())
    smtp_connection.quit()

#-------------------------------------------------------------------------------
def SafeParseGlobalBool(boolVariable):
    if boolVariable in globals():
        return eval(boolVariable)
    return False

#-------------------------------------------------------------------------------
def send_webhook (_json, _html):

    # use data type based on specified payload type
    if webhookPayload == 'json':
        payloadData = _json        
    if webhookPayload == 'html':
        payloadData = _html
    if webhookPayload == 'text':
        payloadData = to_text(_json)

    #Define slack-compatible payload
    _json_payload = { "text": payloadData } if webhookPayload == 'text' else {
    "username": "Pi.Alert",
    "text": "There are new notifications",
    "attachments": [{
      "title": "Pi.Alert Notifications",
      "title_link": REPORT_DASHBOARD_URL,
      "text": payloadData
    }]
    } 

    # DEBUG - Write the json payload into a log file for debugging
    write_file (LOG_PATH + '/webhook_payload.json', json.dumps(_json_payload))    

    # Using the Slack-Compatible Webhook endpoint for Discord so that the same payload can be used for both
    if(WEBHOOK_URL.startswith('https://discord.com/api/webhooks/') and not WEBHOOK_URL.endswith("/slack")):
        _WEBHOOK_URL = f"{WEBHOOK_URL}/slack"
        curlParams = ["curl","-i","-H", "Content-Type:application/json" ,"-d", json.dumps(_json_payload), _WEBHOOK_URL]
    else:
        _WEBHOOK_URL = WEBHOOK_URL
        curlParams = ["curl","-i","-X", webhookRequestMethod ,"-H", "Content-Type:application/json" ,"-d", json.dumps(_json_payload), _WEBHOOK_URL]

    # execute CURL call
    try:
        # try runnning a subprocess
        p = subprocess.Popen(curlParams, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        stdout, stderr = p.communicate()

        # write stdout and stderr into .log files for debugging if needed
        logResult (stdout, stderr)    
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        print(e.output)

#-------------------------------------------------------------------------------
def send_apprise (html):
    #Define Apprise compatible payload (https://github.com/caronc/apprise-api#stateless-solution)
    _json_payload={
    "urls": APPRISE_URL,
    "title": "Pi.Alert Notifications",
    "format": "html",
    "body": html
    }

    try:
        # try runnning a subprocess
        p = subprocess.Popen(["curl","-i","-X", "POST" ,"-H", "Content-Type:application/json" ,"-d", json.dumps(_json_payload), APPRISE_HOST], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = p.communicate()
        # write stdout and stderr into .log files for debugging if needed
        logResult (stdout, stderr)      
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        print(e.output)    

#-------------------------------------------------------------------------------
mqtt_connected_to_broker = 0
mqtt_sensors = []

def publish_mqtt(client, topic, message):
    status = 1
    while status != 0:
        result = client.publish(
                topic=topic,
                payload=message,
                qos=mqttQoS,
                retain=True,
            )

        status = result[0]

        if status != 0:            
            print("Waiting to reconnect to MQTT broker")
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
        

# #-------------------------------------------------------------------------------
def create_sensor(client, deviceId, deviceName, sensorType, sensorName, icon):    

    new_sensor_config = sensor_config(deviceId, deviceName, sensorType, sensorName, icon)

    # check if config already in list and if not, add it, otherwise skip
    global mqtt_sensors

    is_unique = True

    for sensor in mqtt_sensors:
        if sensor.hash == new_sensor_config.hash:
            is_unique = False
            break
           
    # save if unique
    if is_unique:
        mqtt_sensors.append(new_sensor_config)
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

    publish_mqtt(client, topic, message)


#-------------------------------------------------------------------------------
def mqtt_start():    
    def on_disconnect(client, userdata, rc):
        global mqtt_connected_to_broker
        mqtt_connected_to_broker = 0

    def on_connect(client, userdata, flags, rc):
        global mqtt_connected_to_broker
        
        if rc == 0: 
            # print("Connected to broker")         
            mqtt_connected_to_broker = True                #Signal connection 
    
        else: 
            print("Connection failed")


    client = mqtt_client.Client(mqttClientId)   # Set Connecting Client ID    
    client.username_pw_set(mqttUser, mqttPassword)    
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.connect(mqttBroker, mqttPort)
    client.loop_start()  
    
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
    # client.loop()    



# #-------------------------------------------------------------------------------
def start_mqtt_thread ():
    # start a MQTT thread loop which will continuously report on devices to the broker
        # daemon=True - makes sure the thread dies with the process if interrupted
    global mqtt_thread_up

    # flag to check if thread is running
    mqtt_thread_up = True

    print("    Starting MQTT sending")
    x = threading.Thread(target=mqtt_start, args=(1,), daemon=True) 
    # start_sending_mqtt(client)

    print("    Threading: Starting MQTT thread")

    x.start()


#===============================================================================
# DB
#===============================================================================
def upgradeDB (): 

    openDB()

    # indicates, if Online_History table is available 
    onlineHistoryAvailable = sql.execute("""
    SELECT name FROM sqlite_master WHERE type='table'
    AND name='Online_History'; 
    """).fetchall() != []

    # Check if it is incompatible (Check if table has all required columns)
    isIncompatible = False
    
    if onlineHistoryAvailable :
      isIncompatible = sql.execute ("""
      SELECT COUNT(*) AS CNTREC FROM pragma_table_info('Online_History') WHERE name='Archived_Devices'
      """).fetchone()[0] == 0
    
    # Drop table if available, but incompatible
    if onlineHistoryAvailable and isIncompatible:
      print_log ('Table is incompatible, Dropping the Online_History table)')
      sql.execute("DROP TABLE Online_History;")
      onlineHistoryAvailable = False

    if onlineHistoryAvailable == False :
      sql.execute("""      
      CREATE TABLE "Online_History" (
        "Index"	INTEGER,
        "Scan_Date"	TEXT,
        "Online_Devices"	INTEGER,
        "Down_Devices"	INTEGER,
        "All_Devices"	INTEGER,
        "Archived_Devices" INTEGER,
        PRIMARY KEY("Index" AUTOINCREMENT)
      );      
      """)

    # Alter Devices table
    # dev_Network_Node_MAC_ADDR column
    dev_Network_Node_MAC_ADDR_missing = sql.execute ("""
      SELECT COUNT(*) AS CNTREC FROM pragma_table_info('Devices') WHERE name='dev_Network_Node_MAC_ADDR'
      """).fetchone()[0] == 0

    if dev_Network_Node_MAC_ADDR_missing :
      sql.execute("""      
      ALTER TABLE "Devices" ADD "dev_Network_Node_MAC_ADDR" TEXT      
      """)

    # dev_Network_Node_port column
    dev_Network_Node_port_missing = sql.execute ("""
      SELECT COUNT(*) AS CNTREC FROM pragma_table_info('Devices') WHERE name='dev_Network_Node_port'
      """).fetchone()[0] == 0

    if dev_Network_Node_port_missing :
      sql.execute("""      
      ALTER TABLE "Devices" ADD "dev_Network_Node_port" INTEGER 
      """)

    # don't hog DB access  
    closeDB ()

#-------------------------------------------------------------------------------

def openDB ():
    global sql_connection
    global sql

    # Check if DB is open
    if sql_connection != None :
        return

    # Log    
    print_log ('Opening DB...')    

    # Open DB and Cursor
    sql_connection = sqlite3.connect (DB_PATH, isolation_level=None)
    sql_connection.execute('pragma journal_mode=wal') #
    sql_connection.text_factory = str
    sql_connection.row_factory = sqlite3.Row
    sql = sql_connection.cursor()

#-------------------------------------------------------------------------------
def closeDB ():
    global sql_connection
    global sql

    # Check if DB is open
    if sql_connection == None :
        return

    # Log    
    print_log ('Closing DB...')

    # Close DB
    sql_connection.commit()
    sql_connection.close()
    sql_connection = None    
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
def print_log (pText):
    global log_timestamp

    # Check LOG actived
    if not PRINT_LOG :
        return

    # Current Time    
    log_timestamp2 = datetime.datetime.now()

    # Print line + time + elapsed time + text
    print ('--------------------> ',
        log_timestamp2, ' ',
        log_timestamp2 - log_timestamp, ' ',
        pText)

    # Save current time to calculate elapsed time until next log
    log_timestamp = log_timestamp2

#-------------------------------------------------------------------------------

def sanitize_string(input):
    if isinstance(input, bytes):
        input = input.decode('utf-8')
    value = bytes_to_string(re.sub('[^a-zA-Z0-9-_\s]', '', str(input)))
    return value

#-------------------------------------------------------------------------------

def bytes_to_string(value):
    # if value is of type bytes, convert to string
    if isinstance(value, bytes):
        value = value.decode('utf-8')
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

def logResult (stdout, stderr):
    if stderr != None:
        append_file_binary (LOG_PATH + '/stderr.log', stderr)
    if stdout != None:
        append_file_binary (LOG_PATH + '/stdout.log', stdout)   

#-------------------------------------------------------------------------------

def to_text(_json):
    payloadData = ""
    if len(_json['internet']) > 0 and 'internet' in includedSections:
        payloadData += "INTERNET\n"
        for event in _json['internet']:
            payloadData += event[3] + ' on ' + event[2] + '. ' + event[4] + '. New address:' + event[1] + '\n'

    if len(_json['new_devices']) > 0 and 'new_devices' in includedSections:
        payloadData += "NEW DEVICES:\n"
        for event in _json['new_devices']:
            if event[4] is None:
                event[4] = event[11]
            payloadData += event[1] + ' - ' + event[4] + '\n'

    if len(_json['down_devices']) > 0 and 'down_devices' in includedSections:
        write_file (LOG_PATH + '/down_devices_example.log', _json['down_devices'])
        payloadData += 'DOWN DEVICES:\n'
        for event in _json['down_devices']:
            if event[4] is None:
                event[4] = event[11]
            payloadData += event[1] + ' - ' + event[4] + '\n'
    
    if len(_json['events']) > 0 and 'events' in includedSections:
        payloadData += "EVENTS:\n"
        for event in _json['events']:
            if event[8] != "Internet":
                payloadData += event[8] + " on " + event[1] + " " + event[3] + " at " + event[2] + "\n"

    return payloadData

#-------------------------------------------------------------------------------
def get_device_stats():

    openDB()

    # columns = ["online","down","all","archived","new","unknown"]
    sql.execute("""      
      SELECT Online_Devices as online, Down_Devices as down, All_Devices as 'all', Archived_Devices as archived, (select count(*) from Devices a where dev_NewDevice = 1 ) as new, (select count(*) from Devices a where dev_Name = '(unknown)' ) as unknown from Online_History limit  1 
      """)

    row = sql.fetchone()

    closeDB()
    return row
#-------------------------------------------------------------------------------
def get_all_devices():

    openDB()

    sql.execute("""      
        select dev_MAC, dev_Name, dev_DeviceType, dev_Vendor, dev_Group, dev_FirstConnection, dev_LastConnection, dev_LastIP, dev_StaticIP, dev_PresentLastScan, dev_LastNotification, dev_NewDevice, dev_Network_Node_MAC_ADDR from Devices 
      """)

    row = sql.fetchall()

    closeDB()
    return row

#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    sys.exit(main())       
