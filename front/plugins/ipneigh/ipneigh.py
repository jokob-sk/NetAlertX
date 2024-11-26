#!/usr/bin/env python

import os
import pathlib
import sys
import json
import sqlite3
import subprocess
from datetime import datetime
from pytz import timezone
from functools import reduce

# Define the installation path and extend the system path for plugin imports
INSTALL_PATH = "/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from plugin_helper import Plugin_Object, Plugin_Objects, decodeBase64, handleEmpty
from plugin_utils import get_plugins_configs
from logger import mylog
from const import pluginsPath, fullDbPath
from helper import timeNowTZ, get_setting_value 
from notification import write_notification
import conf

# Make sure the TIMEZONE for logging is correct
conf.tz = timezone(get_setting_value('TIMEZONE'))

# Define the current path and log file paths
CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
LOG_FILE = os.path.join(CUR_PATH, 'script.log')
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

# Initialize the Plugin obj output file
plugin_objects = Plugin_Objects(RESULT_FILE)

pluginName = 'IPNEIGH'

def main():
    mylog('verbose', [f'[{pluginName}] In script']) 

    # Retrieve configuration settings
    interfaces = get_setting_value('IPNEIGH_interfaces')

    mylog('verbose', [f'[{pluginName}] Interfaces value: {interfaces}'])

    # retrieve data
    raw_neighbors = get_neighbors(interfaces)
    
    neighbors = parse_neighbors(raw_neighbors)
    
    #mylog('verbose', [f'[{pluginName}] Found neighbors: {neighbors}'])

    #  Process the data into native application tables
    if len(neighbors) > 0:

        # insert devices into the lats_result.log 
        # make sure the below mapping is mapped in config.json, for example: 
        #"database_column_definitions": [
        # {
        #   "column": "Object_PrimaryID",                 <--------- the value I save into primaryId
        #   "mapped_to_column": "cur_MAC",                <--------- gets inserted into the CurrentScan DB table column cur_MAC
        # 
        for device in neighbors:
                plugin_objects.add_object(
                    primaryId   = device['mac'],
                    secondaryId = device['ip'],
                    watched1    = handleEmpty(device['hostname']), # empty
                    watched2    = handleEmpty(device['vendor']), # empty
                    watched3    = handleEmpty(device['device_type']), # empty
                    watched4    = handleEmpty(device['last_seen']), # sometime empty
                    extra       = '',
                    foreignKey  = "" #device['mac']
                    # helpVal1  = "Something1",  # Optional Helper values to be passed for mapping into the app 
                    # helpVal2  = "Something1",  # If you need to use even only 1, add the remaining ones too 
                    # helpVal3  = "Something1",  # and set them to 'null'. Check the the docs for details:
                    # helpVal4  = "Something1",  # https://github.com/jokob-sk/NetAlertX/blob/main/docs/PLUGINS_DEV.md
                    )

        mylog('verbose', [f'[{pluginName}] New entries: "{len(neighbors)}"'])

    # log result
    plugin_objects.write_result_file()

    return 0

def parse_neighbors(raw_neighbors: list[str]):
    neighbors = []
    for line in raw_neighbors:
        if "lladdr" in line:
            # Known data
            fields = line.split()
            
            if not is_multicast(fields[0]):
                # mylog('verbose', [f'[{pluginName}] adding ip {fields[0]}"'])
                neighbor = {}
                neighbor['ip'] = fields[0]
                neighbor['mac'] = fields[2]
                neighbor['reachability'] = fields[3]

                # Unknown data
                neighbor['hostname'] = '(unknown)'
                neighbor['vendor'] = '(unknown)'
                neighbor['device_type'] = '(unknown)'

                # Last seen now if reachable
                if neighbor['reachability'] == "REACHABLE":
                    neighbor['last_seen'] = datetime.now()
                else:
                    neighbor['last_seen'] = ""
                
                neighbors.append(neighbor)
    
    return neighbors


def is_multicast(ip):
    prefixes = ['ff', '224', '231', '232', '233', '234', '238', '239']
    return reduce(lambda acc, prefix: acc or ip.startswith(prefix), prefixes, False)

#  retrieve data
def get_neighbors(interfaces):

    results = []

    for interface in interfaces.split(","):
        try:

            # Ping all IPv6 devices in multicast to trigger NDP 

            mylog('verbose', [f'[{pluginName}] Pinging on interface: "{interface}"'])
            command = f"ping ff02::1%{interface} -c 2".split()
            subprocess.run(command)
            mylog('verbose', [f'[{pluginName}] Pinging completed: "{interface}"'])

            # Check the neighbourhood tables

            mylog('verbose', [f'[{pluginName}] Scanning interface: "{interface}"'])
            command = f"ip neighbor show nud all dev {interface}".split()
            output = subprocess.check_output(command, universal_newlines=True)
            results += output.split("\n")

            mylog('verbose', [f'[{pluginName}] Scanning interface succeded: "{interface}"'])
        except subprocess.CalledProcessError as e:
            # An error occurred, handle it

            mylog('verbose', [f'[{pluginName}] Scanning interface failed: "{interface}"'])
            error_type = type(e).__name__  # Capture the error type

    return results

if __name__ == '__main__':
    main()
