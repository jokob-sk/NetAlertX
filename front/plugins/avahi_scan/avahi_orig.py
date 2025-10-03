#!/usr/bin/env python

import os
import pathlib
import sys
import json

import subprocess

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
from pytz import timezone

# Make sure the TIMEZONE for logging is correct
conf.tz = timezone(get_setting_value('TIMEZONE'))

# Make sure log level is initialized correctly
Logger(get_setting_value('LOG_LEVEL'))

pluginName = 'AVAHISCAN'

# Define the current path and log file paths
LOG_PATH = logPath + '/plugins'
LOG_FILE = os.path.join(LOG_PATH, f'script.{pluginName}.log')
RESULT_FILE = os.path.join(LOG_PATH, f'last_result.{pluginName}.log')

# Initialize the Plugin obj output file
plugin_objects = Plugin_Objects(RESULT_FILE)



def main():
    mylog('verbose', [f'[{pluginName}] In script']) 

    # Retrieve timeout from settings (use AVAHISCAN_RUN_TIMEOUT), fall back to 20
    try:
        _timeout_val = get_setting_value('AVAHISCAN_RUN_TIMEOUT')
        if _timeout_val is None or _timeout_val == '':
            timeout = 20
        else:
            try:
                timeout = int(_timeout_val)
            except (ValueError, TypeError):
                timeout = 20
    except Exception:
        timeout = 20
    
    # Create a database connection
    db = DB()  # instance of class DB
    db.open()

    # Initialize the Plugin obj output file
    plugin_objects = Plugin_Objects(RESULT_FILE)

    # Create a DeviceInstance instance
    device_handler = DeviceInstance(db)

    # Retrieve devices
    if get_setting_value("REFRESH_FQDN"): 
        devices = device_handler.getAll()
    else:        
        devices = device_handler.getUnknown()

    mylog('verbose', [f'[{pluginName}] Devices count: {len(devices)}'])   
    
    # Mock list of devices (replace with actual device_handler.getUnknown() in production)
    # devices = [
    #     {'devMac': '00:11:22:33:44:55', 'devLastIP': '192.168.1.121'},
    #     {'devMac': '00:11:22:33:44:56', 'devLastIP': '192.168.1.9'},
    #     {'devMac': '00:11:22:33:44:57', 'devLastIP': '192.168.1.82'},
    # ]

    if len(devices) > 0:
        # ensure service is running
        ensure_avahi_running()

    for device in devices:
        domain_name = execute_name_lookup(device['devLastIP'], timeout)

        #  check if found and not a timeout ('to')
        if domain_name != '' and domain_name != 'to': 
            plugin_objects.add_object(
            # "MAC", "IP", "Server", "Name"
            primaryId   = device['devMac'],
            secondaryId = device['devLastIP'],
            watched1    = '',  # You can add any relevant info here if needed
            watched2    = domain_name,
            watched3    = '',
            watched4    = '',
            extra       = '',
            foreignKey  = device['devMac'])

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
        mylog('debug', [f'[{pluginName}] DEBUG CMD :', args])
        
        # Run the subprocess with a forced timeout
        output = subprocess.check_output(args, universal_newlines=True, stderr=subprocess.STDOUT, timeout=timeout)

        mylog('debug', [f'[{pluginName}] DEBUG OUTPUT : {output}'])
        
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

        mylog('debug', [f'[{pluginName}] Domain Name: {domain_name}'])

        return domain_name

    except subprocess.CalledProcessError as e:
        mylog('none', [f'[{pluginName}] ⚠ ERROR - {e.output}'])                    

    except subprocess.TimeoutExpired as e:
        # Return a distinct value that main() checks for when a timeout occurs
        # Keep logging for telemetry/debugging
        mylog('none', [f'[{pluginName}] TIMEOUT - the process forcefully terminated as timeout reached{": " + str(getattr(e, "output", "")) if getattr(e, "output", None) else ""}'])
        return 'to'

    if output == "":
        mylog('none', [f'[{pluginName}] Scan: FAIL - check logs']) 
    else: 
        mylog('debug', [f'[{pluginName}] Scan: SUCCESS'])

    return ''   

# Function to ensure Avahi and its dependencies are running
def ensure_avahi_running(attempt=1, max_retries=2):
    """
    Ensure that D-Bus is running and the Avahi daemon is started, with recursive retry logic.
    """
    mylog('debug', [f'[{pluginName}] Attempt {attempt} - Ensuring D-Bus and Avahi daemon are running...'])

    # Check rc-status
    try:
        subprocess.run(['rc-status'], check=True)
    except subprocess.CalledProcessError as e:
        mylog('none', [f'[{pluginName}] ⚠ ERROR - Failed to check rc-status: {e.output}'])
        return

    # Create OpenRC soft level (wrap in try/except to keep error handling consistent)
    try:
        subprocess.run(['touch', '/run/openrc/softlevel'], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        mylog('none', [f'[{pluginName}] ⚠ ERROR - Failed to create OpenRC soft level: {e.stderr if e.stderr else str(e)}'])
        return

    # Add Avahi daemon to runlevel
    try:
        subprocess.run(['rc-update', 'add', 'avahi-daemon'], check=True)
    except subprocess.CalledProcessError as e:
        mylog('none', [f'[{pluginName}] ⚠ ERROR - Failed to add Avahi to runlevel: {e.output}'])
        return

    # Start the D-Bus service
    try:
        subprocess.run(['rc-service', 'dbus', 'start'], check=True)
    except subprocess.CalledProcessError as e:
        mylog('none', [f'[{pluginName}] ⚠ ERROR - Failed to start D-Bus: {e.output}'])
        return

    # Check Avahi status
    status_output = subprocess.run(['rc-service', 'avahi-daemon', 'status'], capture_output=True, text=True)
    if 'started' in status_output.stdout:
        mylog('debug', [f'[{pluginName}] Avahi Daemon is already running.'])
        return

    mylog('none', [f'[{pluginName}] Avahi Daemon is not running, attempting to start... (Attempt {attempt})'])

    # Start the Avahi daemon
    try:
        subprocess.run(['rc-service', 'avahi-daemon', 'start'], check=True)
    except subprocess.CalledProcessError as e:
        mylog('none', [f'[{pluginName}] ⚠ ERROR - Failed to start Avahi daemon: {e.output}'])

    # Check status after starting
    status_output = subprocess.run(['rc-service', 'avahi-daemon', 'status'], capture_output=True, text=True)
    if 'started' in status_output.stdout:
        mylog('debug', [f'[{pluginName}] Avahi Daemon successfully started.'])
        return

    # Retry if not started and attempts are left
    if attempt < max_retries:
        mylog('debug', [f'[{pluginName}] Retrying... ({attempt + 1}/{max_retries})'])
        ensure_avahi_running(attempt + 1, max_retries)
    else:
        mylog('none', [f'[{pluginName}] ⚠ ERROR - Avahi Daemon failed to start after {max_retries} attempts.'])

    # rc-update add avahi-daemon
    # rc-service avahi-daemon status
    # rc-service avahi-daemon start

if __name__ == '__main__':
    main()