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
from models.device_instance import DeviceInstance  # noqa: E402 [flake8 lint suppression]
from utils.crypto_utils import string_to_fake_mac  # noqa: E402 [flake8 lint suppression]
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


def parse_scan_subnets(subnets):
    """Extract subnet and interface from SCAN_SUBNETS"""
    ranges = []
    interfaces = []
    for entry in subnets:
        parts = entry.split("--interface=")
        ranges.append(parts[0].strip())
        if len(parts) > 1:
            interfaces.append(parts[1].strip())
    return ranges, interfaces


def get_device_by_ip(ip, all_devices):
    """Get existing device based on IP"""
    for device in all_devices:
        if device["devLastIP"] == ip:
            return device

    return None


def main():

    mylog('verbose', [f'[{pluginName}] In script'])

    timeout = get_setting_value('ICMP_RUN_TIMEOUT')
    args = get_setting_value('ICMP_ARGS')
    regex  = get_setting_value('ICMP_IN_REGEX')
    mode = get_setting_value('ICMP_MODE')
    fakeMac = get_setting_value('ICMP_FAKE_MAC')
    scan_subnets = get_setting_value("SCAN_SUBNETS")

    subnets, interfaces = parse_scan_subnets(scan_subnets)

    # Initialize the Plugin obj output file
    plugin_objects = Plugin_Objects(RESULT_FILE)

    # Create a DeviceInstance instance
    device_handler = DeviceInstance()

    # Retrieve devices
    all_devices = device_handler.getAll()

    # Compile the regex for efficiency if it will be used multiple times
    regex_pattern = re.compile(regex)

    if mode == "ping":
        plugin_objects = execute_ping(timeout, args, all_devices, regex_pattern, plugin_objects)

    elif mode == "fping":
        plugin_objects = execute_fping(timeout, args, all_devices, plugin_objects, subnets, interfaces, fakeMac)

    plugin_objects.write_result_file()

    mylog('verbose', [f'[{pluginName}] Script finished'])

    return 0


# ===============================================================================
# Execute scan
# ===============================================================================
def execute_ping(timeout, args, all_devices, regex_pattern, plugin_objects):
    """
    Execute ICMP command on filtered devices.
    """

    # Filter devices based on the regex match
    filtered_devices = [
        device for device in all_devices
        if regex_pattern.match(device['devLastIP'])
    ]

    mylog('verbose', [f'[{pluginName}] Devices to PING: {len(filtered_devices)}'])

    for device in filtered_devices:

        cmd = ["ping"] + args.split() + [device['devLastIP']]

        output = ""

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

        try:
            output = subprocess.check_output(
                cmd, universal_newlines=True, stderr=subprocess.STDOUT, timeout=timeout, text=True
            )

            mylog("verbose", [f"[{pluginName}] DEBUG OUTPUT : {output}"])

            is_online = True
            if re.search(r"0% packet loss", output, re.IGNORECASE):
                is_online = True
            elif re.search(r"bad address", output, re.IGNORECASE):
                is_online = False
            elif re.search(r"100% packet loss", output, re.IGNORECASE):
                is_online = False

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

            mylog('verbose', [f"[{pluginName}] ip: {device['devLastIP']} is_online: {is_online}"])

        except subprocess.CalledProcessError as e:
            mylog("verbose", [f"[{pluginName}] ⚠ ERROR - check logs"])
            mylog("verbose", [f"[{pluginName}]", e.output])
        except subprocess.TimeoutExpired:
            mylog("verbose", [f"[{pluginName}] TIMEOUT - process terminated"])

    return plugin_objects


def execute_fping(timeout, args, all_devices, plugin_objects, subnets, interfaces, fakeMac):
    """
    Run fping command and return alive IPs
    """
    cmd = ["fping", "-a"]

    if interfaces:
        cmd += ["-I", ",".join(interfaces)]

    # Build a lookup dict once
    device_map = {d["devLastIP"]: d for d in all_devices if d.get("devLastIP")}

    known_ips = list(device_map.keys())
    online_ips = []

    cmd += args.split()
    cmd += subnets
    cmd += known_ips

    mylog("verbose", [f"[{pluginName}] fping cmd: {' '.join(cmd)}"])

    try:
        output = subprocess.check_output(
            cmd,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            text=True
        )
        online_ips = [line.strip() for line in output.splitlines() if line.strip()]

    except subprocess.CalledProcessError:
        online_ips = []

    except subprocess.TimeoutExpired:
        mylog("verbose", [f"[{pluginName}] fping timeout"])
        online_ips = []

    # process all online IPs
    for onlineIp in online_ips:
        if onlineIp in known_ips:
            # use lookup dict instead of looping
            device = device_map.get(onlineIp)
            if device:
                plugin_objects.add_object(
                    primaryId   = device['devMac'],
                    secondaryId = device['devLastIP'],
                    watched1    = device['devName'],
                    watched2    = 'mode:fping',
                    watched3    = '',
                    watched4    = '',
                    extra       = '',
                    foreignKey  = device['devMac']
                )
            else:
                mylog("none", [f"[{pluginName}] ERROR reverse device lookup failed unexpectedly for {onlineIp}"])
        elif fakeMac:
            fakeMacFromIp = string_to_fake_mac(onlineIp)
            plugin_objects.add_object(
                primaryId   = fakeMacFromIp,
                secondaryId = onlineIp,
                watched1    = "(unknown)",
                watched2    = 'mode:fping',
                watched3    = '',
                watched4    = '',
                extra       = '',
                foreignKey  = fakeMacFromIp
            )
        else:
            mylog('verbose', [f"[{pluginName}] Skipping: {onlineIp}, as new IP and ICMP_FAKE_MAC setting not enabled"])


# ===============================================================================
# BEGIN
# ===============================================================================
if __name__ == '__main__':
    main()
