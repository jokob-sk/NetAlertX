#!/usr/bin/env python
# test script by running:
# tbc

import os
import pathlib
import argparse
import subprocess
import sys
import hashlib
import csv
import sqlite3
import re
from io import StringIO
from datetime import datetime

# Register NetAlertX directories
INSTALL_PATH="/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from plugin_helper import Plugin_Object, Plugin_Objects, decodeBase64
from logger import mylog, Logger, append_line_to_file
from helper import timeNowTZ, get_setting_value
from const import logPath, applicationPath, fullDbPath
from database import DB
from models.device_instance import DeviceInstance
import conf
from pytz import timezone

# Make sure the TIMEZONE for logging is correct
conf.tz = timezone(get_setting_value('TIMEZONE'))

# Make sure log level is initialized correctly
Logger(get_setting_value('LOG_LEVEL'))

pluginName = 'NSLOOKUP'

LOG_PATH = logPath + '/plugins'
LOG_FILE = os.path.join(LOG_PATH, f'script.{pluginName}.log')
RESULT_FILE = os.path.join(LOG_PATH, f'last_result.{pluginName}.log')



def main():

    mylog('verbose', [f'[{pluginName}] In script'])     


    timeout = get_setting_value('NSLOOKUP_RUN_TIMEOUT')

    # Create a database connection
    db = DB()  # instance of class DB
    db.open()

    # Initialize the Plugin obj output file
    plugin_objects = Plugin_Objects(RESULT_FILE)

    # Create a DeviceInstance instance
    device_handler = DeviceInstance(db)

    # Retrieve devices
    if get_setting_value("REFRESH_FQDN"): 
        devices = device_handler.getAll()
    else:        
        devices = device_handler.getUnknown()

    mylog('verbose', [f'[{pluginName}] Devices count: {len(devices)}'])   
    
    # TEST - below is a WINDOWS host IP
    # execute_name_lookup('192.168.1.121', timeout)

    for device in devices:
        domain_name, dns_server = execute_nslookup(device['devLastIP'], timeout)

        if domain_name != '':
            plugin_objects.add_object(
            # "MAC", "IP", "Server", "Name"
            primaryId   = device['devMac'],
            secondaryId = device['devLastIP'],
            watched1    = dns_server,
            watched2    = domain_name,
            watched3    = '',
            watched4    = '',
            extra       = '',
            foreignKey  = device['devMac'])

    plugin_objects.write_result_file()
    
    
    mylog('verbose', [f'[{pluginName}] Script finished'])   
    
    return 0

#===============================================================================
# Execute scan
#===============================================================================
def execute_nslookup (ip, timeout):
    """
    Execute the NSLOOKUP command on IP.
    """
    
    nslookup_args = ['nslookup', ip]

    # Execute command
    output = ""

    try:
        # try runnning a subprocess with a forced (timeout)  in case the subprocess hangs
        output = subprocess.check_output (nslookup_args, universal_newlines=True,  stderr=subprocess.STDOUT, timeout=(timeout), text=True)

        domain_name = ''
        dns_server = ''

        # mylog('verbose', [f'[{pluginName}] DEBUG OUTPUT : {output}'])

        # Parse output using case-insensitive regular expressions
        domain_pattern = re.compile(r'name\s*=\s*([^\s]+)', re.IGNORECASE)
        server_pattern = re.compile(r'Server:\s+(.+)', re.IGNORECASE)


        domain_match = domain_pattern.search(output)        
        server_match = server_pattern.search(output)

        if domain_match:
            domain_name = domain_match.group(1)
            mylog('verbose', [f'[{pluginName}] Domain Name: {domain_name}'])

        if server_match:
            dns_server = server_match.group(1)
            mylog('verbose', [f'[{pluginName}] DNS Server: {dns_server}'])

        return domain_name, dns_server

    except subprocess.CalledProcessError as e:
        # An error occurred, handle it
        if "NXDOMAIN" in e.output:
            mylog('verbose', [f'[{pluginName}]', f"No PTR record found for IP: {ip}"])
        else:
            mylog('verbose', [f'[{pluginName}]', e.output])
            # Handle other errors here
        # mylog('verbose', [f'[{pluginName}] ⚠ ERROR - check logs'])            
        
    except subprocess.TimeoutExpired as timeErr:
        mylog('verbose', [f'[{pluginName}] TIMEOUT - the process forcefully terminated as timeout reached']) 

    if output == "": # check if the subprocess failed      
        tmp = 1   # can't have empty            
        # mylog('verbose', [f'[{pluginName}] Scan: FAIL - check logs']) 
    else: 
        mylog('verbose', [f'[{pluginName}] Scan: SUCCESS'])

    return '', ''   
          
    
    

#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    main()