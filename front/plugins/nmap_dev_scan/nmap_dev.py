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
from logger import mylog, append_line_to_file
from helper import timeNowTZ, get_setting_value
from const import logPath, applicationPath, fullDbPath
from database import DB
from device import Device_obj


CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
LOG_FILE = os.path.join(CUR_PATH, 'script.log')
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

pluginName = 'NMAPDEV'

def main():

    mylog('verbose', [f'[{pluginName}] In script'])     

    # Create a database connection
    db = DB()  # instance of class DB
    db.open()


    timeout = get_setting_value('NMAPDEV_RUN_TIMEOUT')
    subnets = get_setting_value('SCAN_SUBNETS')

    mylog('verbose', [f'[{pluginName}] subnets: ', subnets])    


    # Initialize the Plugin obj output file
    plugin_objects = Plugin_Objects(RESULT_FILE)

    unique_devices = execute_scan(subnets, timeout)

    mylog('verbose', [f'[{pluginName}] Unknown devices count: {len(unique_devices)}'])   

    for device in unique_devices:

        plugin_objects.add_object(
        # "MAC", "IP", "Name", "Vendor", "Interface"
        primaryId   = device[0],
        secondaryId = device[1],
        watched1    = device[2],
        watched2    = device[3],
        watched3    = device[4],
        watched4    = '',
        extra       = '',
        foreignKey  = device[0])

    plugin_objects.write_result_file()
    
    
    mylog('verbose', [f'[{pluginName}] Script finished'])   
    
    return 0

#===============================================================================
# Execute scan
#===============================================================================
def execute_scan (subnets_list, timeout):
    # output of possible multiple interfaces
    scan_output = ""
    devices_list = []

    # scan each interface
    
    for interface in subnets_list :   

        scan_output = execute_scan_on_interface (interface, timeout) 

        mylog('verbose', [f'[{pluginName}] scan_output: ', scan_output])   


        # Regular expression patterns
        entry_pattern = r'Nmap scan report for (.*?) \((\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\)'
        mac_pattern = r'MAC Address: ([0-9A-Fa-f:]+)'
        vendor_pattern = r'\((.*?)\)'

        # Compile regular expression patterns
        entry_regex = re.compile(entry_pattern)
        mac_regex = re.compile(mac_pattern)
        vendor_regex = re.compile(vendor_pattern)

        # Find all matches
        entries = entry_regex.findall(scan_output)
        mac_addresses = mac_regex.findall(scan_output)
        vendors = vendor_regex.findall(scan_output)

        for i in range(len(entries)):
            name, ip_address = entries[i]


            devices_list.append([mac_addresses[i], ip_address, name, vendors[i], interface])


    return devices_list



def execute_scan_on_interface (interface, timeout):
    # Prepare command arguments
    scan_args = get_setting_value('NMAPDEV_ARGS').split() + [interface.split()[0]] 

    mylog('verbose', [f'[{pluginName}] scan_args: ', scan_args])   

    # Execute command
    try:
        # try running a subprocess safely
        result = subprocess.check_output(scan_args, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        # An error occurred, handle it
        error_type = type(e).__name__  # Capture the error type
        result = ""

    return result
          
    
    

#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    main()