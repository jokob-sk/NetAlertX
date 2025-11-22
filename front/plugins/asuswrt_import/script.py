# !/usr/bin/env python
import os
import sys

INSTALL_PATH = os.getenv('NETALERTX_APP', '/app')
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])
pluginName = "ASUSWRT"

import asyncio  # noqa: E402 [flake8 lint suppression]
import aiohttp  # noqa: E402 [flake8 lint suppression]
import conf  # noqa: E402 [flake8 lint suppression]
from asusrouter import AsusData, AsusRouter  # noqa: E402 [flake8 lint suppression]
from asusrouter.modules.connection import ConnectionState  # noqa: E402 [flake8 lint suppression]
from const import logPath  # noqa: E402 [flake8 lint suppression]
from helper import get_setting_value  # noqa: E402 [flake8 lint suppression]
from logger import Logger, mylog  # noqa: E402 [flake8 lint suppression]
from plugin_helper import (Plugin_Objects, handleEmpty)  # noqa: E402 [flake8 lint suppression]
from pytz import timezone  # noqa: E402 [flake8 lint suppression]

conf.tz = timezone(get_setting_value("TIMEZONE"))

Logger(get_setting_value("LOG_LEVEL"))

LOG_PATH = logPath + "/plugins"
LOG_FILE = os.path.join(LOG_PATH, f"script.{pluginName}.log")
RESULT_FILE = os.path.join(LOG_PATH, f"last_result.{pluginName}.log")

plugin_objects = Plugin_Objects(RESULT_FILE)


def main():
    mylog("verbose", [f"[{pluginName}] started."])

    device_data = get_device_data()

    mylog(
        "verbose",
        [f"[{pluginName}] Found '{len(device_data)}' devices"],
    )

    filtered_devices = [
        (key, device)
        for key, device in device_data.items()
        if device.state == ConnectionState.CONNECTED
    ]

    mylog(
        "verbose",
        [f"[{pluginName}] Processing '{len(filtered_devices)}' connected devices"],
    )

    for mac, device in filtered_devices:
        entry_mac = str(device.description.mac).lower()

        plugin_objects.add_object(
            primaryId=entry_mac,
            secondaryId=handleEmpty(device.connection.ip_address),
            watched1=handleEmpty(device.description.name),
            watched2=handleEmpty(device.description.vendor),
            extra=pluginName,
            foreignKey=entry_mac,
        )

    plugin_objects.write_result_file()

    mylog("verbose", [f"[{pluginName}] finished"])

    return 0


def get_device_data():
    # Create a new event loop
    loop = asyncio.new_event_loop()

    # Create aiohttp session
    session = aiohttp.ClientSession(loop=loop)

    port = get_setting_value("ASUSWRT_port").strip()

    mylog("verbose", [f"[{pluginName}] Connecting to the Router..."])

    router = AsusRouter(  # required - both IP and URL supported
        hostname=get_setting_value("ASUSWRT_host"),  # required
        port=(None if not port else port),  # optional
        username=get_setting_value("ASUSWRT_user"),  # required
        password=get_setting_value("ASUSWRT_password"),  # required
        use_ssl=get_setting_value("ASUSWRT_ssl"),  # optional
        session=session,  # optional
    )

    # Connect to the router
    # Throws an error in case of failure
    loop.run_until_complete(router.async_connect())

    # Now you can use the router object to call methods
    clients = loop.run_until_complete(router.async_get_data(AsusData.CLIENTS))

    # Remember to disconnect and close the session when you're done
    loop.run_until_complete(router.async_disconnect())
    loop.run_until_complete(session.close())

    return clients


if __name__ == "__main__":
    main()
