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
import conf
from pytz import timezone
from librouteros import connect
from librouteros.exceptions import TrapError

# Make sure the TIMEZONE for logging is correct
conf.tz = timezone(get_setting_value('TIMEZONE'))

CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
LOG_FILE = os.path.join(CUR_PATH, 'script.log')
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

pluginName = 'MTSCAN'

def main():

    mylog('verbose', [f'[{pluginName}] In script'])     

    mt_host = get_setting_value('MTSCAN_MT_HOST')
    mt_port = get_setting_value('MTSCAN_MT_PORT')
    mt_user = get_setting_value('MTSCAN_MT_USER')
    mt_password = get_setting_value('MTSCAN_MT_PASS')

    #mylog('verbose', [f'[{pluginName}] Router: {mt_host}:{mt_port} user: {mt_user}, pass: {mt_password}'])   
    # Create a database connection
    db = DB()  # instance of class DB
    db.open()

    # Initialize the Plugin obj output file
    plugin_objects = Plugin_Objects(RESULT_FILE)

    # Create a Device_obj instance
    device_handler = Device_obj(db)

    # Retrieve devices
    #unknown_devices = device_handler.getUnknown()
    #mylog('verbose', [f'[{pluginName}] Unknown devices count: {len(unknown_devices)}'])   

    all_devices = device_handler.getAll()

    mylog('verbose', [f'[{pluginName}] all devices count: {len(all_devices)}'])   

    device_map = {d['dev_MAC']:d['dev_LastIP'] for d in all_devices}

    try:
        # connect router
        api = connect(username=mt_user, password=mt_password, host=mt_host, port=mt_port)
    
        # get dhcp leases
        leases = api('/ip/dhcp-server/lease/print')


    
        for lease in leases:
            lease_id = lease.get('.id')
            address = lease.get('address')
            mac_address = lease.get('mac-address').lower()
            host_name = lease.get('host-name')
            comment = lease.get('comment')
            last_seen = lease.get('last-seen')
    
            mylog('verbose', [f"ID: {lease_id}, Address: {address}, MAC Address: {mac_address}, Host Name: {host_name}, Comment: {comment}, Last Seen: {last_seen}"])
            if mac_address in device_map.keys():
                device_name = host_name
                if comment != '':
                    device_name = comment
            
                plugin_objects.add_object(
                # "Name-MAC", "LastIP", "IP", "Name","Host","LastSeen","Comment"
                    primaryId   = mac_address,
                    secondaryId = device_map[mac_address],
                    watched1    = address,
                    watched2    = device_name,
                    watched3    = host_name,
                    watched4    = last_seen,
                    extra       = '',
                    helpVal1    = comment, 
                    foreignKey  = mac_address)
    
        plugin_objects.write_result_file()
    except TrapError as e:
        mylog('error', [f"An error occurred: {e}"])
    except Exception as e:
        mylog('error', [f"Failed to connect to MikroTik API: {e}"])


    #for device in unknown_devices:
    #    domain_name, dns_server = execute_nslookup(device['dev_LastIP'], timeout)

    #    if domain_name != '':
    #        plugin_objects.add_object(
    #        # "MAC", "IP", "Server", "Name"
    #        primaryId   = device['dev_MAC'],
    #        secondaryId = device['dev_LastIP'],
    #        watched1    = dns_server,
    #        watched2    = domain_name,
    #        watched3    = '',
    #        watched4    = '',
    #        extra       = '',
    #        foreignKey  = device['dev_MAC'])

    #plugin_objects.write_result_file()
    
    
    mylog('verbose', [f'[{pluginName}] Script finished'])   
    
    return 0

    
    

#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    main()
