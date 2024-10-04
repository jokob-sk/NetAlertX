#!/usr/bin/env python

import os
import pathlib
import sys
import json
import sqlite3
import subprocess

# Define the installation path and extend the system path for plugin imports
INSTALL_PATH = "/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from plugin_helper import Plugin_Object, Plugin_Objects, decodeBase64
from plugin_utils import get_plugins_configs
from logger import mylog
from const import pluginsPath, fullDbPath
from helper import timeNowTZ, get_setting_value 
from notification import write_notification
from database import DB
from device import Device_obj
import conf
from pytz import timezone

# Make sure the TIMEZONE for logging is correct
conf.tz = timezone(get_setting_value('TIMEZONE'))

# Define the current path and log file paths
CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
LOG_FILE = os.path.join(CUR_PATH, 'script.log')
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

# Initialize the Plugin obj output file
plugin_objects = Plugin_Objects(RESULT_FILE)

pluginName = 'AVAHISCAN'

def main():
    mylog('verbose', [f'[{pluginName}] In script']) 

    # timeout = get_setting_value('AVAHI_RUN_TIMEOUT')
    timeout = 20
    
    # ensure service is running
    ensure_avahi_running()

    # Create a database connection
    db = DB()  # instance of class DB
    db.open()

    # Initialize the Plugin obj output file
    plugin_objects = Plugin_Objects(RESULT_FILE)

    # Create a Device_obj instance
    device_handler = Device_obj(db)

    # Retrieve devices
    unknown_devices = device_handler.getUnknown()
    
    # # Mock list of devices (replace with actual device_handler.getUnknown() in production)
    # unknown_devices = [
    #     {'dev_MAC': '00:11:22:33:44:55', 'dev_LastIP': '192.168.1.121'},
    #     {'dev_MAC': '00:11:22:33:44:56', 'dev_LastIP': '192.168.1.9'},
    #     {'dev_MAC': '00:11:22:33:44:57', 'dev_LastIP': '192.168.1.82'},
    # ]

    mylog('verbose', [f'[{pluginName}] Unknown devices count: {len(unknown_devices)}'])   

    for device in unknown_devices:
        domain_name = execute_name_lookup(device['dev_LastIP'], timeout)

        if domain_name != '':
            plugin_objects.add_object(
            # "MAC", "IP", "Server", "Name"
            primaryId   = device['dev_MAC'],
            secondaryId = device['dev_LastIP'],
            watched1    = '',  # You can add any relevant info here if needed
            watched2    = domain_name,
            watched3    = '',
            watched4    = '',
            extra       = '',
            foreignKey  = device['dev_MAC'])

    plugin_objects.write_result_file()
    
    mylog('verbose', [f'[{pluginName}] Script finished'])   
    
    return 0

#===============================================================================
# Execute scan
#===============================================================================
def execute_name_lookup(ip, timeout):
    """
    Execute the avahi-resolve command on the IP.
    """

    args = ['avahi-resolve', '-a', ip]

    # Execute command
    output = ""

    try:
        mylog('verbose', [f'[{pluginName}] DEBUG CMD :', args])
        
        # Run the subprocess with a forced timeout
        output = subprocess.check_output(args, universal_newlines=True, stderr=subprocess.STDOUT, timeout=timeout)

        mylog('verbose', [f'[{pluginName}] DEBUG OUTPUT : {output}'])
        
        domain_name = ''

        # Split the output into lines
        lines = output.splitlines()

        # Look for the resolved IP address
        for line in lines:
            if ip in line:
                parts = line.split()
                if len(parts) > 1:
                    domain_name = parts[1]  # Second part is the resolved domain name
                else:
                    mylog('verbose', [f'[{pluginName}] ⚠ ERROR - Unexpected output format: {line}'])

        mylog('verbose', [f'[{pluginName}] Domain Name: {domain_name}'])

        return domain_name

    except subprocess.CalledProcessError as e:
        mylog('verbose', [f'[{pluginName}] ⚠ ERROR - {e.output}'])                    

    except subprocess.TimeoutExpired:
        mylog('verbose', [f'[{pluginName}] TIMEOUT - the process forcefully terminated as timeout reached']) 

    if output == "":
        mylog('verbose', [f'[{pluginName}] Scan: FAIL - check logs']) 
    else: 
        mylog('verbose', [f'[{pluginName}] Scan: SUCCESS'])

    return ''   

# Function to ensure Avahi and its dependencies are running
def ensure_avahi_running():
    """
    Ensure that D-Bus is running and the Avahi daemon is started.
    """
    mylog('verbose', [f'[{pluginName}] Ensuring D-Bus and Avahi daemon are running...'])
    
    # # Install D-Bus if not already installed
    # try:
    #     subprocess.run(['apk', 'add', 'dbus'], check=True)
    # except subprocess.CalledProcessError as e:
    #     mylog('verbose', [f'[{pluginName}] ⚠ ERROR - Failed to install D-Bus: {e.output}'])
    #     return

    # Start the D-Bus service
    try:
        subprocess.run(['rc-service', 'dbus', 'start'], check=True)
    except subprocess.CalledProcessError as e:
        mylog('verbose', [f'[{pluginName}] ⚠ ERROR - Failed to start D-Bus: {e.output}'])
        return

    # Create OpenRC soft level if needed
    subprocess.run(['touch', '/run/openrc/softlevel'], check=True)
    
    # Add Avahi daemon to runlevel
    try:
        subprocess.run(['rc-update', 'add', 'avahi-daemon'], check=True)
    except subprocess.CalledProcessError as e:
        mylog('verbose', [f'[{pluginName}] ⚠ ERROR - Failed to add Avahi to runlevel: {e.output}'])
        return
    
    # Start the Avahi daemon
    try:
        subprocess.run(['rc-service', 'avahi-daemon', 'start'], check=True)
    except subprocess.CalledProcessError as e:
        mylog('verbose', [f'[{pluginName}] ⚠ ERROR - Failed to start Avahi daemon: {e.output}'])
        return
    
    # Check status
    status_output = subprocess.run(['rc-service', 'avahi-daemon', 'status'], capture_output=True, text=True)
    mylog('verbose', [f'[{pluginName}] Avahi Daemon Status: {status_output.stdout.strip()}'])

if __name__ == '__main__':
    main()
