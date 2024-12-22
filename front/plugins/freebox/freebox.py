#!/usr/bin/env python

import os
import pathlib
import sys
import json
import sqlite3
from pytz import timezone
import asyncio
from datetime import datetime
from pathlib import Path
from typing import cast
import socket
import aiofreepybox
from aiofreepybox import Freepybox
from aiofreepybox.api.lan import Lan
from aiofreepybox.exceptions import NotOpenError, AuthorizationError

# Define the installation path and extend the system path for plugin imports
INSTALL_PATH = "/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from plugin_helper import Plugin_Object, Plugin_Objects, decodeBase64
from plugin_utils import get_plugins_configs
from logger import mylog, Logger
from const import pluginsPath, fullDbPath, logPath
from helper import timeNowTZ, get_setting_value
from notification import write_notification
import conf

# Make sure the TIMEZONE for logging is correct
conf.tz = timezone(get_setting_value("TIMEZONE"))

# Make sure log level is initialized correctly
Logger(get_setting_value('LOG_LEVEL'))

pluginName = 'FREEBOX'

# Define the current path and log file paths
LOG_PATH = logPath + '/plugins'
LOG_FILE = os.path.join(LOG_PATH, f'script.{pluginName}.log')
RESULT_FILE = os.path.join(LOG_PATH, f'last_result.{pluginName}.log')

# Initialize the Plugin obj output file
plugin_objects = Plugin_Objects(RESULT_FILE)

device_type_map = {
    "workstation": "PC",
    "laptop": "Laptop",
    "smartphone": "Smartphone",
    "tablet": "Tablet",
    "printer": "Printer",
    "vg_console": "Game Console",
    "television": "SmartTV",
    "nas": "NAS",
    "ip_camera": "IP Camera",
    "ip_phone": "Phone",
    "freebox_player": "TV Decoder",
    "freebox_hd": "TV Decoder",
    "freebox_crystal": "TV Decoder",
    "freebox_mini": "TV Decoder",
    "freebox_delta": "Gateway",
    "freebox_one": "Gateway",
    "freebox_wifi": "Gateway",
    "freebox_pop": "AP",
    "networking_device": "Router",
    "multimedia_device": "TV Decoder",
    "car": "House Appliance",
    "other": "(Unknown)",
}


def map_device_type(type: str):
    return device_type_map[type]


async def get_device_data(api_version: int, api_address: str, api_port: int):
    # ensure existence of db path
    data_dir = Path("/app/config/freeboxdb")
    data_dir.mkdir(parents=True, exist_ok=True)

    # Instantiate Freepybox class using default application descriptor
    # and custom token_file location
    fbx = Freepybox(
        app_desc={
            "app_id": "netalertx",
            "app_name": "NetAlertX",
            "app_version": aiofreepybox.__version__,
            "device_name": socket.gethostname(),
        },
        api_version="v" + str(api_version),
        data_dir=data_dir,
    )

    # Connect to the freebox
    # Be ready to authorize the application on the Freebox if you run this
    # for the first time
    try:
        await fbx.open(host=api_address, port=api_port)
    except NotOpenError as e:
        mylog("verbose", [f"[{pluginName}] Error connecting to freebox: {e}"])
    except AuthorizationError as e:
        mylog("verbose", [f"[{pluginName}] Auth error: {str(e)}"])

    # get also info of the freebox itself
    config = await fbx.system.get_config()
    freebox = await cast(Lan, fbx.lan).get_config()
    hosts = await cast(Lan, fbx.lan).get_hosts_list()
    assert config is not None
    assert freebox is not None
    freebox["mac"] = config["mac"]
    freebox["operator"] = config["model_info"]["net_operator"]

    # Close the freebox session
    await fbx.close()

    return freebox, hosts


def main():
    mylog("verbose", [f"[{pluginName}] In script"])

    # Retrieve configuration settings
    api_settings = {
        "api_address": get_setting_value("FREEBOX_address"),
        "api_version": get_setting_value("FREEBOX_api_version"),
        "api_port": get_setting_value("FREEBOX_api_port"),
    }

    mylog("verbose", [f"[{pluginName}] Settings: {api_settings}"])

    # retrieve data
    loop = asyncio.new_event_loop()
    freebox, hosts = loop.run_until_complete(get_device_data(**api_settings))
    loop.close()

    mylog("verbose", [freebox])
    mylog("verbose", [hosts])

    plugin_objects.add_object(
        primaryId=freebox["mac"],
        secondaryId=freebox["ip"],
        watched1=freebox["name"],
        watched2=freebox["operator"],
        watched3="Gateway",
        watched4=datetime.now,
        extra="",
        foreignKey=freebox["mac"],
    )
    for host in hosts:
        for ip in [ip for ip in host["l3connectivities"] if ip["reachable"]]:
            mac: str = host["l2ident"]["id"]
            plugin_objects.add_object(
                primaryId=mac,
                secondaryId=ip["addr"],
                watched1=host["primary_name"],
                watched2=host["vendor_name"] if host["vendor_name"] else "(unknown)",
                watched3=map_device_type(host["host_type"]),
                watched4=datetime.fromtimestamp(ip["last_time_reachable"]),
                extra="",
                foreignKey=mac,
            )

    # commit result
    plugin_objects.write_result_file()

    return 0


if __name__ == "__main__":
    main()
