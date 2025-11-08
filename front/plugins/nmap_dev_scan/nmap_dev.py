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
import nmap  
from io import StringIO
from datetime import datetime

# Register NetAlertX directories
INSTALL_PATH="/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from plugin_helper import Plugin_Object, Plugin_Objects, decodeBase64
from logger import mylog, Logger, append_line_to_file
from helper import get_setting_value, extract_between_strings, extract_ip_addresses, extract_mac_addresses
from const import logPath, applicationPath, fullDbPath
from database import DB
from models.device_instance import DeviceInstance
import conf
from pytz import timezone

# Make sure the TIMEZONE for logging is correct
conf.tz = timezone(get_setting_value('TIMEZONE'))

# Make sure log level is initialized correctly
Logger(get_setting_value('LOG_LEVEL'))

pluginName = 'NMAPDEV'


LOG_PATH = logPath + '/plugins'
LOG_FILE = os.path.join(LOG_PATH, f'script.{pluginName}.log')
RESULT_FILE = os.path.join(LOG_PATH, f'last_result.{pluginName}.log')


def main():

    mylog('verbose', [f'[{pluginName}] In script'])     

    timeout = get_setting_value('NMAPDEV_RUN_TIMEOUT')
    fakeMac = get_setting_value('NMAPDEV_FAKE_MAC')
    subnets = get_setting_value('SCAN_SUBNETS')
    args    = get_setting_value('NMAPDEV_ARGS')

    mylog('verbose', [f'[{pluginName}] subnets: ', subnets])    


    # Initialize the Plugin obj output file
    plugin_objects = Plugin_Objects(RESULT_FILE)

    unique_devices = execute_scan(subnets, timeout, fakeMac, args)

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
def execute_scan(subnets_list, timeout, fakeMac, args):
    devices_list = []

    for interface in subnets_list:
        nmap_output = execute_scan_on_interface(interface, timeout, args)

        # mylog('verbose', [f"[{pluginName}] nmap_output XML: ", nmap_output])

        if nmap_output:  # Proceed only if nmap output is not empty
            # Parse the XML output using python-nmap
            devices = parse_nmap_xml(nmap_output, interface, fakeMac)

            for device in devices:
                # Append to devices_list only if both IP and MAC addresses are present
                if device.get('ip') and device.get('mac'):
                    devices_list.append(device)
                else:
                    # Log an error if either IP or MAC address is missing
                    mylog('verbose', [f"[{pluginName}] Skipped (Not enough info in output): ", device])
        else:
            # Log an error if nmap output is empty
            mylog('verbose', [f"[{pluginName}] No output received for interface: ", interface])

    return devices_list



def execute_scan_on_interface (interface, timeout, args):
    # Remove unsupported VLAN flags 
    interface = re.sub(r'--vlan=\S+', '', interface).strip()

    # Prepare command arguments
    scan_args = args.split() + interface.replace('--interface=','-e ').split()

    mylog('verbose', [f'[{pluginName}] scan_args: ', scan_args])   
    
    try:
        result = subprocess.check_output(scan_args, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        error_type = type(e).__name__
        result = ""
        mylog('verbose', [f'[{pluginName}] ERROR: ', error_type])   

    return result


def parse_nmap_xml(xml_output, interface, fakeMac):
    devices_list = []

    try:
        nm = nmap.PortScanner()
        nm.analyse_nmap_xml_scan(xml_output)

        mylog('verbose', [f'[{pluginName}] Number of hosts: ', len(nm.all_hosts())])  

        for host in nm.all_hosts():
            hostname = nm[host].hostname() or '(unknown)' 

            ip = nm[host]['addresses']['ipv4'] if 'ipv4' in nm[host]['addresses'] else ''
            mac = nm[host]['addresses']['mac'] if 'mac' in nm[host]['addresses'] else ''


            mylog('verbose', [f'[{pluginName}] nm[host]: ', nm[host]]) 

            vendor = ''
            
            if nm[host]['vendor']:
                mylog('verbose', [f'[{pluginName}] entry: ', nm[host]['vendor']]) 
 
                for key, value in nm[host]['vendor'].items():
                    vendor = value
            
                    break

 
            # Log debug information
            mylog('verbose', [f"[{pluginName}] Hostname: {hostname}, IP: {ip}, MAC: {mac}, Vendor: {vendor}"])

            # Only include devices with both IP and MAC addresses
            if (ip != '' and mac != '') or (ip != '' and fakeMac):

                if mac == '' and fakeMac:
                    mac = string_to_mac_hash(ip)

                devices_list.append({
                    'name': hostname,
                    'ip': ip,
                    'mac': mac,
                    'vendor': vendor,
                    'interface': interface
                })
            else:
                # MAC or IP missing
                mylog('verbose', [f"[{pluginName}] Skipping: {hostname}, IP or MAC missing, or NMAPDEV_GENERATE_MAC setting not enabled"])


    except Exception as e:
        mylog('verbose', [f"[{pluginName}] Error parsing nmap XML: ", str(e)])

    return devices_list
          
    
def string_to_mac_hash(input_string):
    # Calculate a hash using SHA-256
    sha256_hash = hashlib.sha256(input_string.encode()).hexdigest()

    # Take the first 12 characters of the hash and format as a MAC address
    mac_hash = ':'.join(sha256_hash[i:i+2] for i in range(0, 12, 2))
    
    return mac_hash

#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    main()