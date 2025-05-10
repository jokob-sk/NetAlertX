#!/usr/bin/env python

import os
import pathlib
import sys
import json
import sqlite3
from pytz import timezone
from wakeonlan import send_magic_packet

# Define the installation path and extend the system path for plugin imports
INSTALL_PATH = "/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from plugin_helper import Plugin_Object, Plugin_Objects, decodeBase64
from plugin_utils import get_plugins_configs
from logger import mylog, Logger
from const import pluginsPath, fullDbPath, logPath
from helper import timeNowTZ, get_setting_value 
from messaging.in_app import write_notification
from database import DB
from models.device_instance import DeviceInstance
import conf

# Make sure the TIMEZONE for logging is correct
conf.tz = timezone(get_setting_value('TIMEZONE'))

# Make sure log level is initialized correctly
Logger(get_setting_value('LOG_LEVEL'))

pluginName = 'WOL'

# Define the current path and log file paths
LOG_PATH = logPath + '/plugins'
LOG_FILE = os.path.join(LOG_PATH, f'script.{pluginName}.log')
RESULT_FILE = os.path.join(LOG_PATH, f'last_result.{pluginName}.log')

# Initialize the Plugin obj output file
plugin_objects = Plugin_Objects(RESULT_FILE)



def main():
    mylog('none', [f'[{pluginName}] In script']) 

    # Retrieve configuration settings
    broadcast_ips = get_setting_value('WOL_broadcast_ips')
    devices_to_wake = get_setting_value('WOL_devices_to_wake')
    ports = get_setting_value('WOL_ports')

    mylog('verbose', [f'[{pluginName}] broadcast_ips value {broadcast_ips}'])

    # Create a database connection
    db = DB()  # instance of class DB
    db.open()

    # Create a DeviceInstance instance
    device_handler = DeviceInstance(db)

    # Retrieve devices
    if 'offline' in devices_to_wake:

        devices_to_wake = device_handler.getOffline()

    elif 'down' in devices_to_wake:
        
        devices_to_wake = device_handler.getDown()

    else:
        mylog('verbose', [f'[{pluginName}] Invalid setting WOL_devices_to_wake {devices_to_wake}'])
        return

    # execute script if something to do
    if len(devices_to_wake) > 0:
        for device in devices_to_wake:
            for ip in broadcast_ips:
                for port in ports:
                    result = execute(port, ip, device['devMac'], device['devName'])

                    #  Process the data into native application tables
                    if len(result) > 0:

                        plugin_objects.add_object(
                            primaryId   = device['devMac'],
                            secondaryId = device['devLastIP'],
                            watched1    = device['devName'],
                            watched2    = result,
                            watched3    = '',
                            watched4    = '',
                            extra       = '',
                            foreignKey  = device['devMac']
                        )

        # log result
        plugin_objects.write_result_file()
    else:
        mylog('none', [f'[{pluginName}] No devices to wake'])     

    mylog('none', [f'[{pluginName}] Script finished']) 

    return 0

#  wake
def execute(port, ip, mac, name):
    
    result = 'null'
    try:
        # Send the magic packet to wake up the device
        send_magic_packet(mac, ip_address=ip, port=int(port))
        mylog('verbose', [f'[{pluginName}] Magic packet sent to {mac} ({name})'])

        result = 'success'
        
    except Exception as e:
        result = str(e)
        mylog('verbose', [f'[{pluginName}] Failed to send magic packet to {mac} ({name}): {e}'])

    # Return the data result
    return result

if __name__ == '__main__':
    main()
