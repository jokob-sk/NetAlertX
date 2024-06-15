#!/usr/bin/env python

import os
import pathlib
import sys
import json
import sqlite3


# Define the installation path and extend the system path for plugin imports
INSTALL_PATH = "/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from plugin_helper import Plugin_Object, Plugin_Objects, decodeBase64
from plugin_utils import get_plugins_configs
from logger import mylog
from const import pluginsPath, fullDbPath
from helper import timeNowTZ, get_setting_value 
from notification import write_notification

# Define the current path and log file paths
CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
LOG_FILE = os.path.join(CUR_PATH, 'script.log')
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

# Initialize the Plugin obj output file
plugin_objects = Plugin_Objects(RESULT_FILE)

pluginName = '<unique_prefix>'

# ----------------------------------------------
# Main initialization
def main():
    mylog('verbose', [f'[{pluginName}] In script']) 

    # Retrieve configuration settings
    some_setting = get_setting_value('OMDSDN_url')

    mylog('verbose', [f'[{pluginName}] some_setting calue {some_setting}'])

    # retrieve data
    device_data = get_device_data(some_setting)

    #  Process the data into native application tables
    if len(device_data) > 0:

        # insert devices into the lats_result.log 
        # make sure the below mapping is mapped in config.json, for example: 
        #"database_column_definitions": [
        # {
        #   "column": "Object_PrimaryID",                 <--------- the value I save into primaryId
        #   "mapped_to_column": "cur_MAC",                <--------- gets unserted into the CurrentScan DB table column cur_MAC
        # 
        for device in device_data:
                plugin_objects.add_object(
                    primaryId   = device['some_id'],    #  MAC
                    secondaryId = device['some_id'],    #  IP
                    watched1    = device['some_id'],    #  NAME/HOSTNAME
                    watched2    = device['some_id'],    #  PARENT NETWORK NODE MAC
                    watched3    = device['some_id'],    #  PORT
                    watched4    = device['some_id'],    #  SSID
                    extra       = device['some_id'],    #  SITENAME (cur_NetworkSite) or VENDOR (cur_Vendor) (PICK one and adjust config.json -> "column": "Extra")
                    foreignKey  = device['some_id'])    #  usually MAC

        mylog('verbose', [f'[{pluginName}] New entries: "{len(new_devices)}"'])

    # log result
    plugin_objects.write_result_file()

    return 0

# ----------------------------------------------
#  retrieve data
def get_device_data(some_setting):
    
    device_data = []

    # do some processing, call exteranl APIs, and return a device list
    #  ...
    # 

    return device_data

if __name__ == '__main__':
    main()
