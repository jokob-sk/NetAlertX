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
import base64
import sqlite3
from io import StringIO
from datetime import datetime

sys.path.append("/home/pi/pialert/front/plugins")
sys.path.append('/home/pi/pialert/pialert') 

from plugin_helper import Plugin_Object, Plugin_Objects, decodeBase64
from logger import mylog, append_line_to_file
from helper import timeNowTZ, check_IP_format
from const import logPath, pialertPath, fullDbPath


CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
LOG_FILE = os.path.join(CUR_PATH, 'script.log')
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

def main():

    mylog('verbose', ['[INTRNT] In script'])     
    
    parser = argparse.ArgumentParser(description='Check internet connectivity and IP')
    
    parser.add_argument('prev_ip', action="store", help="Previous IP address to compare against the current IP")
    parser.add_argument('DDNS_ACTIVE', action="store", help="Indicates if Dynamic DNS (DDNS) is active (True/False)")
    parser.add_argument('DDNS_UPDATE_URL', action="store", help="URL for updating Dynamic DNS (DDNS)")
    parser.add_argument('DDNS_USER', action="store", help="Username for Dynamic DNS (DDNS) authentication")
    parser.add_argument('DDNS_PASSWORD', action="store", help="Password for Dynamic DNS (DDNS) authentication")
    parser.add_argument('DDNS_DOMAIN', action="store", help="Dynamic DNS (DDNS) domain name")
    parser.add_argument('DIG_GET_IP_ARG', action="store", help="Arguments for the 'dig' command to retrieve the IP address")

    values = parser.parse_args()

    PREV_IP         = values.prev_ip.split('=')[1]    
    DDNS_ACTIVE     = values.DDNS_ACTIVE.split('=')[1]    
    DDNS_UPDATE_URL = values.DDNS_UPDATE_URL.split('=')[1]
    DDNS_USER       = values.DDNS_USER.split('=')[1]
    DDNS_PASSWORD   = values.DDNS_PASSWORD.split('=')[1]
    DDNS_DOMAIN     = values.DDNS_DOMAIN.split('=')[1]   
    DIG_GET_IP_ARG  = values.DIG_GET_IP_ARG.split('=')[1]   

    mylog('verbose', ['[INTRNT] DIG_GET_IP_ARG: ', DIG_GET_IP_ARG]) 

    # Decode the base64-encoded value to get the actual value in ASCII format.
    DIG_GET_IP_ARG = base64.b64decode(DIG_GET_IP_ARG.split('b')[1]).decode('ascii')
    
    mylog('verbose', [f'[INTRNT] DIG_GET_IP_ARG resolved: {DIG_GET_IP_ARG} ']) 

    # if internet_IP != "" :
    #     sql.execute (f"""INSERT INTO CurrentScan (cur_MAC, cur_IP, cur_Vendor, cur_ScanMethod)
    #                 VALUES ( 'Internet', '{internet_IP}', Null, 'queryDNS') """)
   
    # # Save event
    # cursor.execute ("""INSERT INTO Events (eve_MAC, eve_IP, eve_DateTime,
    #                     eve_EventType, eve_AdditionalInfo,
    #                     eve_PendingAlertEmail)
    #                 VALUES ('Internet', ?, ?, 'Internet IP Changed',
    #                     'Previous Internet IP: '|| ?, 1) """,
    #                 (pNewIP, timeNowTZ(), prevIp) )


    # # Save new IP
    # cursor.execute ("""UPDATE Devices SET dev_LastIP = ?
    #                 WHERE dev_MAC = 'Internet' """,
    #                 (pNewIP,) )


    # Object_PrimaryID - cur_MAC
    # Watched_Value1 - cur_IP
    # Watched_Value2 - Extra / prev IP  

    
    new_internet_IP = check_internet_IP( DDNS_ACTIVE, DDNS_UPDATE_URL, DDNS_USER, DDNS_PASSWORD, DDNS_DOMAIN, PREV_IP, DIG_GET_IP_ARG)   

    plugin_objects = Plugin_Objects(RESULT_FILE)    
    
    plugin_objects.add_object(
        primaryId   = 'Internet',       # MAC (Device Name)
        secondaryId = '', 
        watched1    = new_internet_IP,  # IP Address  
        watched2    = f'Previous IP: {PREV_IP}',  
        watched3    = '',  
        watched4    = '',
        extra       = f'Previous IP: {PREV_IP}', 
        foreignKey  = 'Internet')

    plugin_objects.write_result_file() 

    mylog('verbose', ['[INTRNT] Finished '])   
    
    return 0

   
    
#===============================================================================
# INTERNET IP CHANGE
#===============================================================================
def check_internet_IP ( DDNS_ACTIVE, DDNS_UPDATE_URL, DDNS_USER, DDNS_PASSWORD, DDNS_DOMAIN, PREV_IP, DIG_GET_IP_ARG ):   
    
    # Get Internet IP
    mylog('verbose', ['[INTRNT] - Retrieving Internet IP'])
    internet_IP = get_internet_IP(DIG_GET_IP_ARG)

    # Check result = IP
    if internet_IP == "" :
        mylog('none', ['[INTRNT]    Error retrieving Internet IP'])                
    
    # Get previous stored IP    
    previous_IP = '0.0.0.0'

    if  PREV_IP is not None and len(PREV_IP) > 0 :
        previous_IP = PREV_IP

    mylog('verbose', ['[INTRNT]      ', previous_IP])

    #  logging
    append_line_to_file (logPath + '/IP_changes.log', '['+str(timeNowTZ()) +']\t'+ internet_IP +'\n')

    # Get Dynamic DNS IP
    if DDNS_ACTIVE :
        mylog('verbose', ['[DDNS]    Retrieving Dynamic DNS IP'])
        dns_IP = get_dynamic_DNS_IP(DDNS_DOMAIN)

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

    return internet_IP
    

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
        curl_output = subprocess.check_output (['curl', 
                                                '-s',
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


#-------------------------------------------------------------------------------
def get_internet_IP (DIG_GET_IP_ARG):
    # BUGFIX #46 - curl http://ipv4.icanhazip.com repeatedly is very slow
    # Using 'dig'
    dig_args = ['dig', '+short'] + DIG_GET_IP_ARG.strip().split()
    try:
        cmd_output = subprocess.check_output (dig_args, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        mylog('none', [e.output])
        cmd_output = '' # no internet

    # Check result is an IP
    IP = check_IP_format (cmd_output)

    # Handle invalid response
    if IP == '':
        IP = '0.0.0.0'

    return IP

#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    main()