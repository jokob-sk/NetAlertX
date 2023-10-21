#!/usr/bin/env python

import os
import pathlib
import argparse
import sys
import re
import base64
import subprocess
from time import strftime

sys.path.append("/home/pi/pialert/front/plugins")
sys.path.append('/home/pi/pialert/pialert') 

# pialert modules
from database import DB
from plugin_helper import Plugin_Object, Plugin_Objects, handleEmpty
from logger import mylog, append_line_to_file
from helper import timeNowTZ, get_setting_value
from const import logPath, pialertPath

CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
LOG_FILE = os.path.join(CUR_PATH, 'script.log')
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')


def main():
    # sample
    # /home/pi/pialert/front/plugins/arp_scan/script.py userSubnets=b'MTkyLjE2OC4xLjAvMjQgLS1pbnRlcmZhY2U9ZXRoMQ=='
    # the script expects a parameter in the format of userSubnets=subnet1,subnet2,...
    parser = argparse.ArgumentParser(description='Import devices from settings')
    parser.add_argument('userSubnets', nargs='+', help="list of subnets with options")
    values = parser.parse_args()    

    # Assuming Plugin_Objects is a class or function that reads data from the RESULT_FILE
    # and returns a list of objects called 'devices'.
    plugin_objects = Plugin_Objects(RESULT_FILE)

    # Print a message to indicate that the script is starting.
    mylog('verbose', ['[ARP Scan] In script ']) 

    #  holds a list of user-submitted subnets.    
    mylog('verbose', ['[ARP Scan] values.userSubnets: ', values.userSubnets]) 
    

    # Extract the base64-encoded subnet information from the first element of the userSubnets list.
    # The format of the element is assumed to be like 'userSubnets=b<base64-encoded-data>'.
    userSubnetsParamBase64 = values.userSubnets[0].split('userSubnets=b')[1]

    # Printing the extracted base64-encoded subnet information.
    mylog('verbose', ['[ARP Scan] userSubnetsParamBase64: ', userSubnetsParamBase64]) 
    

    # Decode the base64-encoded subnet information to get the actual subnet information in ASCII format.
    userSubnetsParam = base64.b64decode(userSubnetsParamBase64).decode('ascii')

    # Print the decoded subnet information.
    mylog('verbose', ['[ARP Scan] userSubnetsParam: ', userSubnetsParam]) 

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
            extra       = 'arp-scan', 
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

        mylog('verbose', ['[ARP Scan] arpscan_output: ', arpscan_output])         
    
        # Search IP + MAC + Vendor as regular expresion
        re_ip = r'(?P<ip>((2[0-5]|1[0-9]|[0-9])?[0-9]\.){3}((2[0-5]|1[0-9]|[0-9])?[0-9]))'
        re_mac = r'(?P<mac>([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2}))'
        re_hw = r'(?P<hw>.*)'
        re_pattern = re.compile (re_ip + '\s+' + re_mac + '\s' + re_hw)

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
    mylog('verbose', ['[ARP Scan] Found: Devices without duplicates ', len(unique_devices)  ]) 

    mylog('verbose', ["Devices List len:", len(devices_list)])    # Add this line to print devices_list
    mylog('verbose',["Devices List:", devices_list])              # Add this line to print devices_list

    return devices_list


def execute_arpscan_on_interface(interface):
    # Prepare command arguments
    arpscan_args = get_setting_value('ARPSCAN_ARGS').split() + interface.split()

    # Execute command
    try:
        # try running a subprocess safely
        result = subprocess.check_output(arpscan_args, universal_newlines=True)
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
