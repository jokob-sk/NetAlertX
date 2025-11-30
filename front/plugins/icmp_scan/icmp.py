#!/usr/bin/env python
# test script by running:
# tbc

import os
import subprocess
import sys
import re

# Register NetAlertX directories
INSTALL_PATH = os.getenv('NETALERTX_APP', '/app')
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from plugin_helper import Plugin_Objects  # noqa: E402 [flake8 lint suppression]
from logger import mylog, Logger  # noqa: E402 [flake8 lint suppression]
from helper import get_setting_value  # noqa: E402 [flake8 lint suppression]
from const import logPath  # noqa: E402 [flake8 lint suppression]
from database import DB  # noqa: E402 [flake8 lint suppression]
from models.device_instance import DeviceInstance  # noqa: E402 [flake8 lint suppression]
import conf  # noqa: E402 [flake8 lint suppression]
from pytz import timezone  # noqa: E402 [flake8 lint suppression]

# Make sure the TIMEZONE for logging is correct
conf.tz = timezone(get_setting_value('TIMEZONE'))

# Make sure log level is initialized correctly
Logger(get_setting_value('LOG_LEVEL'))

pluginName = 'ICMP'

LOG_PATH = logPath + '/plugins'
LOG_FILE = os.path.join(LOG_PATH, f'script.{pluginName}.log')
RESULT_FILE = os.path.join(LOG_PATH, f'last_result.{pluginName}.log')


def main():

    mylog('verbose', [f'[{pluginName}] In script'])

    timeout = get_setting_value('ICMP_RUN_TIMEOUT')
    args = get_setting_value('ICMP_ARGS')
    in_regex = get_setting_value('ICMP_IN_REGEX')

    # Create a database connection
    db = DB()  # instance of class DB
    db.open()

    # Initialize the Plugin obj output file
    plugin_objects = Plugin_Objects(RESULT_FILE)

    # Create a DeviceInstance instance
    device_handler = DeviceInstance(db)

    # Retrieve devices
    all_devices = device_handler.getAll()

    # Compile the regex for efficiency if it will be used multiple times
    regex_pattern = re.compile(in_regex)

    # Filter devices based on the regex match
    filtered_devices = [
        device for device in all_devices
        if regex_pattern.match(device['devLastIP'])
    ]

    mylog('verbose', [f'[{pluginName}] Devices to PING: {len(filtered_devices)}'])

    for device in filtered_devices:
        is_online, output = execute_scan(device['devLastIP'], timeout, args)

        mylog('verbose', [f"[{pluginName}] ip: {device['devLastIP']} is_online: {is_online}"])

        if is_online:
            plugin_objects.add_object(
                # "MAC", "IP", "Name", "Output"
                primaryId   = device['devMac'],
                secondaryId = device['devLastIP'],
                watched1    = device['devName'],
                watched2    = output.replace('\n', ''),
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
def execute_scan(ip, timeout, args):
    """
    Execute the ICMP command on IP.
    """

    icmp_args = ['ping'] + args.split() + [ip]

    # Execute command
    output = ""

    try:
        # try runnning a subprocess with a forced (timeout)  in case the subprocess hangs
        output = subprocess.check_output(
            icmp_args,
            universal_newlines=True,
            stderr=subprocess.STDOUT,
            timeout=(timeout),
            text=True
        )

        mylog('verbose', [f'[{pluginName}] DEBUG OUTPUT : {output}'])

        # Parse output using case-insensitive regular expressions
        # Synology-NAS:/# ping -i 0.5 -c 3 -W 8 -w 9 192.168.1.82
        # PING 192.168.1.82 (192.168.1.82): 56 data bytes
        # 64 bytes from 192.168.1.82: seq=0 ttl=64 time=0.080 ms
        # 64 bytes from 192.168.1.82: seq=1 ttl=64 time=0.081 ms
        # 64 bytes from 192.168.1.82: seq=2 ttl=64 time=0.089 ms

        # --- 192.168.1.82 ping statistics ---
        # 3 packets transmitted, 3 packets received, 0% packet loss
        # round-trip min/avg/max = 0.080/0.083/0.089 ms
        # Synology-NAS:/# ping -i 0.5 -c 3 -W 8 -w 9 192.168.1.82a
        # ping: bad address '192.168.1.82a'
        # Synology-NAS:/# ping -i 0.5 -c 3 -W 8 -w 9 192.168.1.92
        # PING 192.168.1.92 (192.168.1.92): 56 data bytes

        # --- 192.168.1.92 ping statistics ---
        # 3 packets transmitted, 0 packets received, 100% packet loss

        # TODO: parse output and return True if online, False if Offline (100% packet loss, bad address)
        is_online = True

        # Check for 0% packet loss in the output
        if re.search(r"0% packet loss", output, re.IGNORECASE):
            is_online = True
        elif re.search(r"bad address", output, re.IGNORECASE):
            is_online = False
        elif re.search(r"100% packet loss", output, re.IGNORECASE):
            is_online = False

        return is_online, output

    except subprocess.CalledProcessError as e:
        # An error occurred, handle it
        mylog('verbose', [f'[{pluginName}] ⚠ ERROR - check logs'])
        mylog('verbose', [f'[{pluginName}]', e.output])

        return False, output

    except subprocess.TimeoutExpired:
        mylog('verbose', [f'[{pluginName}] TIMEOUT - the process forcefully terminated as timeout reached'])
        return False, output

    return False, output


# ===============================================================================
# BEGIN
# ===============================================================================
if __name__ == '__main__':
    main()
