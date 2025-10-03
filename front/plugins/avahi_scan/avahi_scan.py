#!/usr/bin/env python

import os
import pathlib
import sys
import json
import dns.resolver

# Define the installation path and extend the system path for plugin imports
INSTALL_PATH = "/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from plugin_helper import Plugin_Object, Plugin_Objects, decodeBase64
from plugin_utils import get_plugins_configs
from logger import mylog as write_log, Logger
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

#===============================================================================
# Execute scan using DNS resolver
#===============================================================================
def resolve_ips_with_zeroconf(ips, timeout):
    """
    Uses DNS resolver to actively query PTR records for reverse DNS lookups on given IP addresses.
    """
    resolved_hosts = {}
    
    for ip in ips:
        try:
            # Construct the reverse IP for PTR query (e.g., 8.1.168.192.in-addr.arpa.)
            reverse_ip = '.'.join(reversed(ip.split('.'))) + '.in-addr.arpa.'
            
            # Query PTR record with timeout; respect the passed timeout per query
            answers = dns.resolver.resolve(reverse_ip, 'PTR', lifetime=max(1, timeout))
            
            if answers:
                # For PTR records, the hostname is in the target field
                hostname = str(answers[0].target).rstrip('.')
                resolved_hosts[ip] = hostname
                write_log('verbose', [f'[{pluginName}] Resolved {ip} -> {hostname}'])
        except Exception as e:
            write_log('verbose', [f'[{pluginName}] Error resolving {ip}: {e}'])
    
    write_log('verbose', [f'[{pluginName}] Active resolution finished. Found {len(resolved_hosts)} hosts.'])
    return resolved_hosts

def main():
    write_log('verbose', [f'[{pluginName}] In script'])

    # Get timeout from settings, default to 20s, and subtract a buffer
    try:
        timeout_setting = int(get_setting_value('AVAHISCAN_RUN_TIMEOUT'))
    except (ValueError, TypeError):
        timeout_setting = 30 # Default to 30s as a safe value
    
    # Use a timeout 5 seconds less than the plugin's configured timeout to allow for cleanup
    scan_duration = max(5, timeout_setting - 5)
    
    db = DB()
    db.open()

    plugin_objects = Plugin_Objects(RESULT_FILE)
    device_handler = DeviceInstance(db)

    # Retrieve devices based on REFRESH_FQDN setting to match original script's logic
    if get_setting_value("REFRESH_FQDN"):
        devices = device_handler.getAll()
        write_log('verbose', [f'[{pluginName}] REFRESH_FQDN is true, getting all devices.'])
    else:
        devices = device_handler.getUnknown()
        write_log('verbose', [f'[{pluginName}] REFRESH_FQDN is false, getting devices with unknown hostnames.'])

    # db.close() # This was causing the crash, DB object doesn't have a close method.

    write_log('verbose', [f'[{pluginName}] Devices to scan: {len(devices)}'])

    if len(devices) > 0:
        ips_to_find = [device['devLastIP'] for device in devices if device['devLastIP']]
        if ips_to_find:
            write_log('verbose', [f'[{pluginName}] IPs to be scanned: {ips_to_find}'])
            resolved_hosts = resolve_ips_with_zeroconf(ips_to_find, scan_duration)

            for device in devices:
                domain_name = resolved_hosts.get(device['devLastIP'])
                if domain_name:
                    plugin_objects.add_object(
                        primaryId   = device['devMac'],
                        secondaryId = device['devLastIP'],
                        watched1    = '',
                        watched2    = domain_name,
                        watched3    = '',
                        watched4    = '',
                        extra       = '',
                        foreignKey  = device['devMac']
                    )
        else:
            write_log('verbose', [f'[{pluginName}] No devices with IP addresses to scan.'])

    plugin_objects.write_result_file()
    
    write_log('verbose', [f'[{pluginName}] Script finished'])
    
    return 0

if __name__ == '__main__':
    main()