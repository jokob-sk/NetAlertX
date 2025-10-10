#!/usr/bin/env python3
import os
import sys
import json
import socket
import ipaddress
from zeroconf import Zeroconf, ServiceBrowser, ServiceInfo, InterfaceChoice, IPVersion
from zeroconf.asyncio import AsyncZeroconf

INSTALL_PATH = "/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from plugin_helper import Plugin_Objects
from logger import mylog, Logger
from const import logPath
from helper import get_setting_value
from database import DB
from models.device_instance import DeviceInstance
import conf
from pytz import timezone

# Configure timezone and logging
conf.tz = timezone(get_setting_value("TIMEZONE"))
Logger(get_setting_value("LOG_LEVEL"))

pluginName = "AVAHISCAN"

# Define log paths
LOG_PATH = os.path.join(logPath, "plugins")
LOG_FILE = os.path.join(LOG_PATH, f"script.{pluginName}.log")
RESULT_FILE = os.path.join(LOG_PATH, f"last_result.{pluginName}.log")

# Initialize plugin results
plugin_objects = Plugin_Objects(RESULT_FILE)


# =============================================================================
# Helper functions
# =============================================================================

def resolve_mdns_name(ip: str, timeout: int = 5) -> str:
    """
    Attempts to resolve a hostname via multicast DNS using the Zeroconf library.

    Args:
        ip (str): The IP address to resolve.
        timeout (int): Timeout in seconds for mDNS resolution.

    Returns:
        str: Resolved hostname (or empty string if not found).
    """
    mylog("debug", [f"[{pluginName}] Resolving mDNS for {ip}"])

    # Convert string IP to an address object
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        mylog("none", [f"[{pluginName}] Invalid IP: {ip}"])
        return ""

    # Reverse lookup name, e.g. "121.1.168.192.in-addr.arpa"
    if addr.version == 4:
        rev_name = ipaddress.ip_address(ip).reverse_pointer
    else:
        rev_name = ipaddress.ip_address(ip).reverse_pointer

    try:
        zeroconf = Zeroconf()
        hostname = socket.getnameinfo((ip, 0), socket.NI_NAMEREQD)[0]
        zeroconf.close()
        if hostname and hostname != ip:
            mylog("debug", [f"[{pluginName}] Found mDNS name: {hostname}"])
            return hostname
    except Exception as e:
        mylog("debug", [f"[{pluginName}] Zeroconf lookup failed for {ip}: {e}"])
    finally:
        try:
            zeroconf.close()
        except Exception:
            pass

    return ""


# =============================================================================
# Main logic
# =============================================================================

def main():
    mylog("verbose", [f"[{pluginName}] Script started"])

    timeout = get_setting_value("AVAHISCAN_RUN_TIMEOUT")
    use_mock = "--mockdata" in sys.argv
    
    if use_mock:
        mylog("verbose", [f"[{pluginName}] Running in MOCK mode"])
        devices = [
            {"devMac": "00:11:22:33:44:55", "devLastIP": "192.168.1.121"},
            {"devMac": "00:11:22:33:44:56", "devLastIP": "192.168.1.9"},
            {"devMac": "00:11:22:33:44:57", "devLastIP": "192.168.1.82"},
        ]
    else:
        db = DB()
        db.open()
        device_handler = DeviceInstance(db)
        devices = (
            device_handler.getAll()
            if get_setting_value("REFRESH_FQDN")
            else device_handler.getUnknown()
        )

    mylog("verbose", [f"[{pluginName}] Devices count: {len(devices)}"])

    for device in devices:
        ip = device["devLastIP"]
        mac = device["devMac"]

        hostname = resolve_mdns_name(ip, timeout)

        if hostname:
            plugin_objects.add_object(
                primaryId=mac,
                secondaryId=ip,
                watched1="",
                watched2=hostname,
                watched3="",
                watched4="",
                extra="",
                foreignKey=mac,
            )

    plugin_objects.write_result_file()

    mylog("verbose", [f"[{pluginName}] Script finished"])
    return 0


# =============================================================================
# Entrypoint
# =============================================================================
if __name__ == "__main__":
    main()
