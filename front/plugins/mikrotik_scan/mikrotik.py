#!/usr/bin/env python

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

    # init global variables
    global MT_HOST, MT_PORT, MT_USER, MT_PASS

    # Initialize the Plugin obj output file
    plugin_objects = Plugin_Objects(RESULT_FILE)

    # Mikrotik settings
    MT_HOST = get_setting_value('MTSCAN_MT_HOST')
    MT_PORT = get_setting_value('MTSCAN_MT_PORT')
    MT_USER = get_setting_value('MTSCAN_MT_USER')
    MT_PASS = get_setting_value('MTSCAN_MT_PASS')

    plugin_objects = get_entries(plugin_objects)

    plugin_objects.write_result_file()
    
    mylog('verbose', [f'[{pluginName}] Scan finished, found {len(plugin_objects)} devices'])


def get_entries(plugin_objects: Plugin_Objects) -> Plugin_Objects:

    try:
        # connect router
        api = connect(username=MT_USER, password=MT_PASS, host=MT_HOST, port=MT_PORT)
    
        # get dhcp leases
        leases = api('/ip/dhcp-server/lease/print')
    
        for lease in leases:
            lease_id = lease.get('.id')
            address = lease.get('address')
            mac_address = lease.get('mac-address').lower()
            host_name = lease.get('host-name')
            comment = lease.get('comment')
            last_seen = lease.get('last-seen')
            status = lease.get('status')
    
            mylog('verbose', [f"ID: {lease_id}, Address: {address}, MAC Address: {mac_address}, Host Name: {host_name}, Comment: {comment}, Last Seen: {last_seen}, Status: {status}"])

            if (status == "bound"):
                plugin_objects.add_object(
                    primaryId   = mac_address,
                    secondaryId = '',
                    watched1    = address,
                    watched2    = host_name,
                    watched3    = last_seen,
                    watched4    = '',
                    extra       = '',
                    helpVal1    = comment, 
                    foreignKey  = mac_address)

    except TrapError as e:
        mylog('error', [f"An error occurred: {e}"])
    except Exception as e:
        mylog('error', [f"Failed to connect to MikroTik API: {e}"])

    mylog('verbose', [f'[{pluginName}] Script finished'])   
    
    return plugin_objects


#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    main()
