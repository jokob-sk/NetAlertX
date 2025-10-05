#!/usr/bin/env python

import os
import time
import pathlib
import argparse
import sys
import re
import base64
import subprocess
from time import strftime

# Register NetAlertX directories
INSTALL_PATH="/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from database import DB
from plugin_helper import Plugin_Object, Plugin_Objects, handleEmpty
from logger import mylog, Logger, append_line_to_file
from helper import timeNowTZ, get_setting_value
from const import logPath, applicationPath
import conf
from pytz import timezone

# Make sure the TIMEZONE for logging is correct
conf.tz = timezone(get_setting_value('TIMEZONE'))

# Make sure log level is initialized correctly
Logger(get_setting_value('LOG_LEVEL'))

pluginName = 'ARPSCAN'

LOG_PATH = logPath + '/plugins'
LOG_FILE = os.path.join(LOG_PATH, f'script.{pluginName}.log')
RESULT_FILE = os.path.join(LOG_PATH, f'last_result.{pluginName}.log')



def main():
   
    parser = argparse.ArgumentParser(description='Import devices from settings')
    parser.add_argument('userSubnets', nargs='+', help="list of subnets with options")
    values = parser.parse_args()    

    # Assuming Plugin_Objects is a class or function that reads data from the RESULT_FILE
    # and returns a list of objects called 'devices'.
    plugin_objects = Plugin_Objects(RESULT_FILE)

    # Print a message to indicate that the script is starting.
    mylog('verbose', ['[ARP Scan] In script ']) 

    #  holds a list of user-submitted subnets.    
    # mylog('verbose', ['[ARP Scan] values.userSubnets: ', values.userSubnets]) 
    

    # Extract the base64-encoded subnet information from the first element of the userSubnets list.
    # The format of the element is assumed to be like 'userSubnets=b<base64-encoded-data>'.
    userSubnetsParamBase64 = values.userSubnets[0].split('userSubnets=b')[1]

    # Printing the extracted base64-encoded subnet information.
    # mylog('verbose', ['[ARP Scan] userSubnetsParamBase64: ', userSubnetsParamBase64]) 
    

    # Decode the base64-encoded subnet information to get the actual subnet information in ASCII format.
    userSubnetsParam = base64.b64decode(userSubnetsParamBase64).decode('ascii')

    # Print the decoded subnet information.
    mylog('verbose', [f'[{pluginName}] userSubnetsParam: ', userSubnetsParam]) 

    # Check if the decoded subnet information contains multiple subnets separated by commas.
    # If it does, split the string into a list of individual subnets.
    # Otherwise, create a list with a single element containing the subnet information.
    if ',' in userSubnetsParam:
        subnets_list = userSubnetsParam.split(',')
    else:
        subnets_list = [userSubnetsParam]


    # Create a database connection
    db = DB()  # instance of class DB
    db.open()
    
    # Execute the ARP scanning process on the list of subnets (whether it's one or multiple subnets).
    # The function 'execute_arpscan' is assumed to be defined elsewhere in the code.
    unique_devices = execute_arpscan(subnets_list)


    for device in unique_devices:
        plugin_objects.add_object(
            primaryId   = handleEmpty(device['mac']),  # MAC (Device Name)
            secondaryId = handleEmpty(device['ip']),  # IP Address            
            watched1    = handleEmpty(device['ip']),    # Device Name
            watched2    = handleEmpty(device.get('hw', '')),  # Vendor (assuming it's in the 'hw' field)
            watched3    = handleEmpty(device.get('interface', '')),  # Add the interface             
            watched4    = '',
            extra       = pluginName, 
            foreignKey  = "")

    plugin_objects.write_result_file()

    return 0


def execute_arpscan(userSubnets):
    # output of possible multiple interfaces
    arpscan_output = ""
    devices_list = []

    # scan each interface
    
    for interface in userSubnets :   

        arpscan_output = execute_arpscan_on_interface (interface)        

        mylog('verbose', [f'[{pluginName}] arpscan_output: ', arpscan_output])         
    
        # Search IP + MAC + Vendor as regular expresion
        re_ip = r'(?P<ip>((2[0-5]|1[0-9]|[0-9])?[0-9]\.){3}((2[0-5]|1[0-9]|[0-9])?[0-9]))'
        re_mac = r'(?P<mac>([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2}))'
        re_hw = r'(?P<hw>.*)'
        re_pattern = re.compile(rf"{re_ip}\s+{re_mac}\s{re_hw}")

        devices_list_tmp = [
            {**device.groupdict(), "interface": interface}
            for device in re.finditer(re_pattern, arpscan_output)
        ]

        devices_list += devices_list_tmp

    # mylog('debug', ['[ARP Scan] Found: Devices including duplicates ', len(devices_list) ]) 
    
    # Delete duplicate MAC
    unique_mac = [] 
    unique_devices = [] 

    for device in devices_list :
        if device['mac'] not in unique_mac: 
            unique_mac.append(device['mac'])
            unique_devices.append(device)    

    # return list
    mylog('verbose', [f'[{pluginName}] Found: Devices without duplicates ', len(unique_devices)  ]) 

    mylog('verbose', [f'[{pluginName}] Devices List len:', len(devices_list)])    
    mylog('verbose', [f'[{pluginName}] Devices List:', devices_list])              

    return devices_list


def execute_arpscan_on_interface(interface):
    # Prepare command arguments
    arpscan_args = get_setting_value('ARPSCAN_ARGS').split() + interface.split()

    # Optional duration in seconds (0 = run once)
    try:
        scan_duration = int(get_setting_value('ARPSCAN_DURATION'))
    except Exception:
        scan_duration = 0  # default: single run

    results = []
    start_time = time.time()

    while True:
        try:
            result = subprocess.check_output(arpscan_args, universal_newlines=True)
            results.append(result)
        except subprocess.CalledProcessError as e:
            result = ""
        # stop looping if duration not set or expired
        if scan_duration == 0 or (time.time() - start_time) > scan_duration:
            break
        time.sleep(2)  # short delay between scans

    # concatenate all outputs (for regex parsing)
    return "\n".join(results)




#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    main()
