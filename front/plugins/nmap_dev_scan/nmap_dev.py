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
from helper import timeNowTZ, get_setting_value, extract_between_strings, extract_ip_addresses, extract_mac_addresses
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

    mylog('verbose', [f'[{pluginName}] Devices found: {len(unique_devices)}'])   

    for device in unique_devices:

        plugin_objects.add_object(
        # "MAC", "IP", "Name", "Vendor", "Interface"
        primaryId   = device['mac'].lower(),
        secondaryId = device['ip'],
        watched1    = device['name'],
        watched2    = device['vendor'],
        watched3    = device['interface'],
        watched4    = '',
        extra       = '',
        foreignKey  = device['mac'])

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

    for interface in subnets_list:
        nmap_output = execute_scan_on_interface(interface, timeout)
        mylog('verbose', [f'[{pluginName}] nmap_output: ', nmap_output])

        if nmap_output is not None:
            nmap_output_ent = nmap_output.split('Nmap scan report for')
            # loop thru entries for individual devices
            for ent in nmap_output_ent:

                lines = ent.split('\n')

                if len(lines) >= 3: 
                    # lines[0]  can be DESKTOP-DIHOG0E.localdomain (192.168.1.121)      or       192.168.1.255
                    # lines[1]  can be Host is up (0.21s latency).
                    # lines[2]  can be MAC Address: 6C:4A:4A:7B:4A:43 (Motorola Mobility, a Lenovo Company)

                    ip_addresses  = extract_ip_addresses(lines[0])
                    host_name     = extract_between_strings(lines[0], ' ', ' ')
                    vendor        = extract_between_strings(lines[2], '(', ')')
                    mac_addresses = extract_mac_addresses(lines[2])

                    # only include results with a MAC address and IPs as it's used as a unique ID 
                    if len(mac_addresses) == 1 and len(ip_addresses) == 1:              

                        devices_list.append({'name'     : host_name, 
                                             'ip'       : ip_addresses[0], 
                                             'mac'      : mac_addresses[0], 
                                             'vendor'   : vendor, 
                                             'interface': interface})
                    else:
                        mylog('verbose', [f"[{pluginName}] Skipped (Couldn't parse MAC or IP): ", lines])
                else:
                    mylog('verbose', [f"[{pluginName}] Skipped (Not enough info in output): ", lines])
    
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