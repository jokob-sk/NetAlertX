# !/usr/bin/env python

import os
import sys
import subprocess

# Define the installation path and extend the system path for plugin imports
INSTALL_PATH = os.getenv('NETALERTX_APP', '/app')
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from plugin_helper import Plugin_Objects  # noqa: E402 [flake8 lint suppression]
from logger import mylog, Logger  # noqa: E402 [flake8 lint suppression]
from const import logPath  # noqa: E402 [flake8 lint suppression]
from helper import get_setting_value   # noqa: E402 [flake8 lint suppression]
from database import DB  # noqa: E402 [flake8 lint suppression]
from models.device_instance import DeviceInstance  # noqa: E402 [flake8 lint suppression]
import conf  # noqa: E402 [flake8 lint suppression]
from pytz import timezone  # noqa: E402 [flake8 lint suppression]

# Make sure the TIMEZONE for logging is correct
conf.tz = timezone(get_setting_value('TIMEZONE'))

# Make sure log level is initialized correctly
Logger(get_setting_value('LOG_LEVEL'))

pluginName = 'NBTSCAN'

# Define the current path and log file paths
LOG_PATH = logPath + '/plugins'
LOG_FILE = os.path.join(LOG_PATH, f'script.{pluginName}.log')
RESULT_FILE = os.path.join(LOG_PATH, f'last_result.{pluginName}.log')

# Initialize the Plugin obj output file
plugin_objects = Plugin_Objects(RESULT_FILE)


def main():
    mylog('verbose', [f'[{pluginName}] In script'])

    # timeout = get_setting_value('NBLOOKUP_RUN_TIMEOUT')
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

    # TEST - below is a WINDOWS host IP
    # execute_name_lookup('192.168.1.121', timeout)

    for device in devices:
        domain_name, dns_server = execute_name_lookup(device['devLastIP'], timeout)

        if domain_name != '':
            plugin_objects.add_object(
                # "MAC", "IP", "Server", "Name"
                primaryId   = device['devMac'],
                secondaryId = device['devLastIP'],
                watched1    = dns_server,
                watched2    = domain_name,
                watched3    = '',
                watched4    = '',
                extra       = '',
                foreignKey  = device['devMac']
            )

    plugin_objects.write_result_file()

    mylog('verbose', [f'[{pluginName}] Script finished'])

    return 0


# ===============================================================================
# Execute scan
# ===============================================================================
def execute_name_lookup(ip, timeout):
    """
    Execute the NBTSCAN command on IP.
    """

    args = ['nbtscan', ip]

    # Execute command
    output = ""

    try:
        mylog('verbose', [f'[{pluginName}] DEBUG CMD :', args])

        # try runnning a subprocess with a forced (timeout)  in case the subprocess hangs
        output = subprocess.check_output(
            args,
            universal_newlines=True,
            stderr=subprocess.STDOUT,
            timeout=(timeout),
            text=True
        )

        mylog('verbose', [f'[{pluginName}] DEBUG OUTPUT : {output}'])

        domain_name = ''
        dns_server = ''

        # Split the output into lines
        lines = output.splitlines()

        # Look for the first line containing a valid NetBIOS name entry
        for line in lines:
            if 'Doing NBT name scan' not in line and ip in line:
                # Split the line and extract the primary NetBIOS name
                parts = line.split()
                if len(parts) > 1:
                    domain_name = parts[1]
                else:
                    mylog('verbose', [f'[{pluginName}] ⚠ ERROR - Unexpected output format: {line}'])

        mylog('verbose', [f'[{pluginName}] Domain Name: {domain_name}'])

        return domain_name, dns_server

    except subprocess.CalledProcessError as e:
        # An error occurred, handle it
        # if "NXDOMAIN" in e.output:
        #     mylog('verbose', [f'[{pluginName}]', f"No PTR record found for IP: {ip}"])
        # else:
        mylog('verbose', [f'[{pluginName}] ⚠ ERROR - {e.output}'])

    except subprocess.TimeoutExpired:
        mylog('verbose', [f'[{pluginName}] TIMEOUT - the process forcefully terminated as timeout reached'])

    if output == "":  # check if the subprocess failed
        mylog('verbose', [f'[{pluginName}] Scan: FAIL - check logs'])
    else:
        mylog('verbose', [f'[{pluginName}] Scan: SUCCESS'])

    return '', ''


# ===============================================================================
# BEGIN
# ===============================================================================
if __name__ == '__main__':
    main()
