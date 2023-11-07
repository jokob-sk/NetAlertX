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

pluginName = 'INTRNT'

def main():

    mylog('verbose', [f'[{pluginName}] In script'])     
    
    parser = argparse.ArgumentParser(description='Check internet connectivity and IP')
    
    parser.add_argument('prev_ip', action="store", help="Previous IP address to compare against the current IP")
    parser.add_argument('DIG_GET_IP_ARG', action="store", help="Arguments for the 'dig' command to retrieve the IP address")

    values = parser.parse_args()

    PREV_IP         = values.prev_ip.split('=')[1]        
    DIG_GET_IP_ARG  = values.DIG_GET_IP_ARG.split('=b')[1]   # byte64 encoded

    mylog('verbose', [f'[{pluginName}] DIG_GET_IP_ARG: ', DIG_GET_IP_ARG])     

    # Decode the base64-encoded value to get the actual value in ASCII format.
    DIG_GET_IP_ARG = base64.b64decode(DIG_GET_IP_ARG).decode('ascii')
    
    mylog('verbose', [f'[{pluginName}] DIG_GET_IP_ARG resolved: {DIG_GET_IP_ARG} ']) 

    # perform the new IP lookup
    new_internet_IP, cmd_output = check_internet_IP( PREV_IP, DIG_GET_IP_ARG)   

    plugin_objects = Plugin_Objects(RESULT_FILE)    
    
    plugin_objects.add_object(
        primaryId   = 'Internet',       # MAC (Device Name)
        secondaryId = new_internet_IP,  # IP Address 
        watched1    = f'Previous IP: {PREV_IP}',
        watched2    = cmd_output.replace('\n',''),
        watched3    = '',  
        watched4    = '',
        extra       = f'Previous IP: {PREV_IP}', 
        foreignKey  = 'Internet')

    plugin_objects.write_result_file() 

    mylog('verbose', [f'[{pluginName}] Finished '])   
    
    return 0
  
    
#===============================================================================
# INTERNET IP CHANGE
#===============================================================================
def check_internet_IP ( PREV_IP, DIG_GET_IP_ARG ):   
    
    # Get Internet IP
    mylog('verbose', [f'[{pluginName}] - Retrieving Internet IP'])
    internet_IP, cmd_output = get_internet_IP(DIG_GET_IP_ARG)

    mylog('verbose', [f'[{pluginName}]  Current internet_IP : {internet_IP}'])        
    
    # Check previously stored IP    
    previous_IP = '0.0.0.0'

    if  PREV_IP is not None and len(PREV_IP) > 0 :
        previous_IP = PREV_IP

    mylog('verbose', [f'[{pluginName}]          previous_IP : {previous_IP}']) 

    #  logging
    append_line_to_file (logPath + '/IP_changes.log', '['+str(timeNowTZ()) +']\t'+ internet_IP +'\n')          

    return internet_IP, cmd_output
    

#-------------------------------------------------------------------------------
def get_internet_IP (DIG_GET_IP_ARG):

    cmd_output = ''
    
    # Using 'dig'
    dig_args = ['dig', '+short'] + DIG_GET_IP_ARG.strip().split()
    try:
        cmd_output = subprocess.check_output (dig_args, universal_newlines=True)
        mylog('verbose', [f'[{pluginName}]  DIG result : {cmd_output}'])    
    except subprocess.CalledProcessError as e:
        mylog('verbose', [e.output])
        cmd_output = '' # no internet

    # Check result is an IP
    IP = check_IP_format (cmd_output)

    # Handle invalid response
    if IP == '':
        IP = '0.0.0.0'

    return IP, cmd_output

#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    main()