#!/usr/bin/env python

import os
import sys
from pytz import timezone

# Define the installation path and extend the system path for plugin imports
INSTALL_PATH = os.getenv('NETALERTX_APP', '/app')
sys.path.extend([f"{INSTALL_PATH}/server/plugins", f"{INSTALL_PATH}/server"])

from const import logPath # noqa: E402, E261 [flake8 lint suppression]
# If your plugin needs to persist its own files between runs, import dbFolderPath
# (internal state, e.g. "/data/db") and/or configPath (user-facing config
# artifacts, e.g. "/data/config") instead of hardcoding a path — see
# docs/PLUGINS_DEV.md#persisting-plugin-data-state--config-files
# from const import dbFolderPath, configPath
from plugin_helper import Plugin_Objects, decode_settings_base64 # noqa: E402, E261 [flake8 lint suppression]
from logger import mylog, Logger # noqa: E402, E261 [flake8 lint suppression]
from helper import get_setting_value # noqa: E402, E261 [flake8 lint suppression]

import conf # noqa: E402, E261 [flake8 lint suppression]

# Make sure the TIMEZONE for logging is correct
conf.tz = timezone(get_setting_value('TIMEZONE'))

# Make sure log level is initialized correctly
Logger(get_setting_value('LOG_LEVEL'))

pluginName = '<unique_prefix>'

# Define the current path and log file paths
LOG_PATH = logPath + '/plugins'
LOG_FILE = os.path.join(LOG_PATH, f'script.{pluginName}.log')
RESULT_FILE = os.path.join(LOG_PATH, f'last_result.{pluginName}.log')

# Example: a plugin-managed state file (uncomment and adjust if you need one)
# STATE_FILE = os.path.join(dbFolderPath, f'state.{pluginName}.json')

# Initialize the Plugin obj output file
plugin_objects = Plugin_Objects(RESULT_FILE)


def main():
    mylog('verbose', [f'[{pluginName}] In script'])

    # Retrieve configuration settings
    some_setting = get_setting_value('SYNC_plugins')

    mylog('verbose', [f'[{pluginName}] some_setting value {some_setting}'])

    # Example: reading the nested "one or more instances" setting pattern
    # (config.json's "nested_form_example") instead of a fixed hardcoded
    # "primary"/"secondary" pair - see docs/PLUGINS_DEV.md#conventions-checklist.
    for instance in get_configured_instances():
        mylog('verbose', [
            f"[{pluginName}] configured instance: {instance['name']} -> {instance['url']} "
            f"(enabled={instance['enabled']})"
        ])

    # retrieve data
    device_data = get_device_data(some_setting)

    #  Process the data into native application tables
    if len(device_data) > 0:

        # insert devices into the lats_result.log
        # make sure the below mapping is mapped in config.json, for example:
        # "database_column_definitions": [
        # {
        #   "column": "objectPrimaryId",     <--------- the value I save into primaryId
        #   "mapped_to_column": "scanMac",   <--------- gets inserted into the CurrentScan DB
        #                                               table column scanMac
        #
        for device in device_data:
            plugin_objects.add_object(
                primaryId   = device['mac_address'],
                secondaryId = device['ip_address'],
                watched1    = device['hostname'],
                watched2    = device['vendor'],
                watched3    = device['device_type'],
                watched4    = device['last_seen'],
                extra       = '',
                foreignKey  = device['mac_address']
                # helpVal1  = "Something1",  # Optional Helper values to be passed for mapping into the app
                # helpVal2  = "Something1",  # If you need to use even only 1, add the remaining ones too
                # helpVal3  = "Something1",  # and set them to 'null'. Check the the docs for details:
                # helpVal4  = "Something1",  # https://docs.netalertx.com/PLUGINS_DEV
            )

        mylog('verbose', [f'[{pluginName}] New entries: "{len(device_data)}"'])

    # log result
    plugin_objects.write_result_file()

    return 0


def get_configured_instances():
    """
    Example of processing the "nested_form_example" setting from config.json -
    the multi-instance settings pattern (a popup form per list entry), used
    when a plugin needs to support an arbitrary number of instances instead
    of a fixed "primary"/"secondary" pair. See server/plugins/rest_import for
    the full-featured version this is based on.

    Each raw entry in the setting's list is a base64-encoded JSON blob;
    decode_settings_base64() turns it into a dict keyed by the popupForm's
    "function" names (here: TMP_instance_name/_url/_enabled).
    """
    raw_instances = get_setting_value('TMP_nested_form_example') or []

    instances = []
    for raw in raw_instances:
        cfg = decode_settings_base64(raw)
        instances.append({
            'name':    cfg.get('TMP_instance_name', ''),
            'url':     cfg.get('TMP_instance_url', ''),
            'enabled': bool(cfg.get('TMP_instance_enabled', True)),
        })

    # Skip instances the user unchecked rather than deleted.
    return [instance for instance in instances if instance['enabled']]


#  retrieve data
def get_device_data(some_setting):

    device_data = []

    # do some processing, call exteranl APIs, and return a device_data list
    # ...
    #
    # If you call a network API here, remember RUN_TIMEOUT is the whole
    # script's kill-timeout (enforced by server/plugin.py), not a safe
    # per-request timeout - don't reuse its value as the timeout for each
    # individual HTTP call if you might make several in a loop, or one slow
    # call can burn the whole budget and get the process killed before it
    # writes RESULT_FILE. See docs/PLUGINS_DEV.md#conventions-checklist.
    #
    # Sample data for testing purposes, you can adjust the processing in main() as needed
    # ... before adding it to the plugin_objects.add_object(...)
    device_data = [
        {
            'device_id': 'device1',
            'mac_address': '00:11:22:33:44:55',
            'ip_address': '192.168.1.2',
            'hostname': 'iPhone 12',
            'vendor': 'Apple Inc.',
            'device_type': 'Smartphone',
            'last_seen': '2024-06-27 10:00:00',
            'port': '1',
            'network_id': 'network1'
        },
        {
            'device_id': 'device2',
            'mac_address': '00:11:22:33:44:66',
            'ip_address': '192.168.1.3',
            'hostname': 'Moto G82',
            'vendor': 'Motorola Inc.',
            'device_type': 'Laptop',
            'last_seen': '2024-06-27 10:05:00',
            'port': '',
            'network_id': 'network1'
        }
    ]

    # Return the data to be detected by the main application
    return device_data


if __name__ == '__main__':
    main()
