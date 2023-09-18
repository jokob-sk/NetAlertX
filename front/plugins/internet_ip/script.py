#!/usr/bin/env python
# test script by running:
# /home/pi/pialert/front/plugins/internet_ip/script.py TBD

import os
import pathlib
import argparse
import sys
import hashlib
import csv
import subprocess
import re
import sqlite3
from io import StringIO
from datetime import datetime

sys.path.append("/home/pi/pialert/front/plugins")
sys.path.append('/home/pi/pialert/pialert') 

from plugin_helper import Plugin_Object, Plugin_Objects, decodeBase64
from logger import mylog, append_line_to_file
from helper import timeNowTZ, get_internet_IP
from const import logPath, pialertPath, fullDbPath


CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
LOG_FILE = os.path.join(CUR_PATH, 'script.log')
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

def main():

    mylog('verbose', ['[INTRNT] In script'])     
    
    parser = argparse.ArgumentParser(description='Check internet connectivity and IP')
    parser.add_argument('pluginskeephistory', action="store", help="TBC")
    parser.add_argument('hourstokeepnewdevice', action="store", help="TBC")
    parser.add_argument('daystokeepevents', action="store", help="TBC")
    parser.add_argument('pholuskeepdays', action="store", help="TBC")
    
    values = parser.parse_args()

    DDNS_ACTIVE     = values.TBC.split('=')[1]    
    DDNS_UPDATE_URL = values.TBC.split('=')[1]
    DDNS_USER       = values.TBC.split('=')[1]
    DDNS_PASSWORD   = values.TBC.split('=')[1]
    DDNS_DOMAIN     = values.TBC.split('=')[1]   
    
    # Connect to the PiAlert SQLite database
    conn    = sqlite3.connect(fullDbPath)
    cursor  = conn.cursor()
    
    #  do stuff
    check_internet_IP(conn, cursor, DDNS_ACTIVE, DDNS_UPDATE_URL, DDNS_USER, DDNS_PASSWORD, DDNS_DOMAIN)

    cursor.execute ("""SELECT from Online_History""") # TODO delete

    conn.commit()
    # Close the database connection
    conn.close()

    mylog('verbose', ['[INTRNT] Finished '])   
    
    return 0

   
    
#===============================================================================
# INTERNET IP CHANGE
#===============================================================================
def check_internet_IP (conn, cursor, DDNS_ACTIVE, DDNS_UPDATE_URL, DDNS_USER, DDNS_PASSWORD, DDNS_DOMAIN ):   

    # Header
    updateState("Scan: Internet IP")
    mylog('verbose', ['[INTRNT] Check Internet IP started'])    

    # Get Internet IP
    mylog('verbose', ['[INTRNT] - Retrieving Internet IP'])
    internet_IP = get_internet_IP()
    # TESTING - Force IP
        # internet_IP = "1.2.3.4"

    # Check result = IP
    if internet_IP == "" :
        mylog('none', ['[INTRNT]    Error retrieving Internet IP'])
        mylog('none', ['[INTRNT]    Exiting...'])
        return False
    mylog('verbose', ['[INTRNT] IP:      ', internet_IP])

    # Get previous stored IP
    mylog('verbose', ['[INTRNT]    Retrieving previous IP:'])    
    previous_IP = get_previous_internet_IP (conn, cursor)
    mylog('verbose', ['[INTRNT]      ', previous_IP])

    # Check IP Change
    if internet_IP != previous_IP :
        mylog('minimal', ['[INTRNT]    New internet IP: ', internet_IP])
        save_new_internet_IP (conn, cursor, internet_IP)
        
    else :
        mylog('verbose', ['[INTRNT]    No changes to perform'])    

    # Get Dynamic DNS IP
    if DDNS_ACTIVE :
        mylog('verbose', ['[DDNS]    Retrieving Dynamic DNS IP'])
        dns_IP = get_dynamic_DNS_IP()

        # Check Dynamic DNS IP
        if dns_IP == "" or dns_IP == "0.0.0.0" :
            mylog('none', ['[DDNS]     Error retrieving Dynamic DNS IP'])            
        mylog('none', ['[DDNS]    ', dns_IP])

        # Check DNS Change
        if dns_IP != internet_IP :
            mylog('none', ['[DDNS]     Updating Dynamic DNS IP'])
            message = set_dynamic_DNS_IP (DDNS_UPDATE_URL, DDNS_USER, DDNS_PASSWORD, DDNS_DOMAIN)
            mylog('none', ['[DDNS]        ', message])            
        else :
            mylog('verbose', ['[DDNS]     No changes to perform'])
    else :
        mylog('verbose', ['[DDNS]     Skipping Dynamic DNS update'])



#-------------------------------------------------------------------------------
def save_new_internet_IP (conn, cursor, pNewIP):
    # Log new IP into logfile
    append_line_to_file (logPath + '/IP_changes.log',
        '['+str(timeNowTZ()) +']\t'+ pNewIP +'\n')

    prevIp = get_previous_internet_IP(conn, cursor)     
    # Save event
    cursor.execute ("""INSERT INTO Events (eve_MAC, eve_IP, eve_DateTime,
                        eve_EventType, eve_AdditionalInfo,
                        eve_PendingAlertEmail)
                    VALUES ('Internet', ?, ?, 'Internet IP Changed',
                        'Previous Internet IP: '|| ?, 1) """,
                    (pNewIP, timeNowTZ(), prevIp) )

    # Save new IP
    cursor.execute ("""UPDATE Devices SET dev_LastIP = ?
                    WHERE dev_MAC = 'Internet' """,
                    (pNewIP,) )

    # commit changes    
    conn.commit()

#-------------------------------------------------------------------------------
def get_previous_internet_IP (conn, cursor):
    
    previous_IP = '0.0.0.0'

    # get previous internet IP stored in DB
    cursor.execute ("SELECT dev_LastIP FROM Devices WHERE dev_MAC = 'Internet' ")
    result = db.sql.fetchone()

    conn.commit()

    if  result is not None and len(result) > 0 :
        previous_IP = result[0]

    # return previous IP
    return previous_IP


    

#-------------------------------------------------------------------------------
def get_dynamic_DNS_IP (DDNS_DOMAIN):
    # Using OpenDNS server
        # dig_args = ['dig', '+short', DDNS_DOMAIN, '@resolver1.opendns.com']

    # Using default DNS server
    dig_args = ['dig', '+short', DDNS_DOMAIN]

    try:
        # try runnning a subprocess
        dig_output = subprocess.check_output (dig_args, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        mylog('none', ['[DDNS] ERROR - ', e.output])
        dig_output = '' # probably no internet

    # Check result is an IP
    IP = check_IP_format (dig_output)

    # Handle invalid response
    if IP == '':
        IP = '0.0.0.0'

    return IP

#-------------------------------------------------------------------------------
def set_dynamic_DNS_IP (DDNS_UPDATE_URL, DDNS_USER, DDNS_PASSWORD, DDNS_DOMAIN):
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
        mylog('none', ['[DDNS] ERROR - ',e.output])
        curl_output = ""    
    
    return curl_output

#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    main()