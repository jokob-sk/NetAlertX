#!/usr/bin/env python

import os
import sys

# Register NetAlertX directories
INSTALL_PATH = os.getenv('NETALERTX_APP', '/app')
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from plugin_helper import Plugin_Objects  # noqa: E402 [flake8 lint suppression]
from logger import mylog, Logger  # noqa: E402 [flake8 lint suppression]
from helper import get_setting_value  # noqa: E402 [flake8 lint suppression]
from const import logPath  # noqa: E402 [flake8 lint suppression]
import conf  # noqa: E402 [flake8 lint suppression]
from pytz import timezone  # noqa: E402 [flake8 lint suppression]
from librouteros import connect  # noqa: E402 [flake8 lint suppression]
from librouteros.exceptions import TrapError  # noqa: E402 [flake8 lint suppression]

# Make sure the TIMEZONE for logging is correct
conf.tz = timezone(get_setting_value('TIMEZONE'))

# Make sure log level is initialized correctly
Logger(get_setting_value('LOG_LEVEL'))

pluginName = 'MTSCAN'

LOG_PATH = logPath + '/plugins'
LOG_FILE = os.path.join(LOG_PATH, f'script.{pluginName}.log')
RESULT_FILE = os.path.join(LOG_PATH, f'last_result.{pluginName}.log')


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
            device_name = comment or host_name or "(unknown)"

            mylog('verbose', f"ID: {lease_id}, Address: {address}, MAC: {mac_address}, Host Name: {host_name}, Comment: {comment}, Last Seen: {last_seen}, Status: {status}")

            if (status == "bound"):
                plugin_objects.add_object(
                    primaryId   = mac_address,
                    secondaryId = address,
                    watched1    = address,
                    watched2    = device_name,
                    watched3    = host_name,
                    watched4    = last_seen,
                    extra       = '',
                    helpVal1    = comment,
                    foreignKey  = mac_address)

    except TrapError as e:
        mylog('error', [f"An error occurred: {e}"])
    except Exception as e:
        mylog('error', [f"Failed to connect to MikroTik API: {e}"])

    mylog('verbose', [f'[{pluginName}] Script finished'])

    return plugin_objects


# ===============================================================================
# BEGIN
# ===============================================================================
if __name__ == '__main__':
    main()
