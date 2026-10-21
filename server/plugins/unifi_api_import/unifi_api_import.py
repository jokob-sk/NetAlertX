#!/usr/bin/env python

import json
import os
import sys
from pytz import timezone
from unifi_sm_api.api import SiteManagerAPI

INSTALL_PATH = os.getenv('NETALERTX_APP', '/app')
sys.path.extend([
    f"{INSTALL_PATH}/server/plugins",
    f"{INSTALL_PATH}/server"
])

from plugin_helper import Plugin_Objects, decode_settings_base64  # noqa: E402
from logger import mylog, Logger  # noqa: E402
from const import logPath  # noqa: E402
from helper import get_setting_value  # noqa: E402
import conf  # noqa: E402


conf.tz = timezone(get_setting_value('TIMEZONE'))
Logger(get_setting_value('LOG_LEVEL'))

pluginName = 'UNIFIAPI'

RESULT_FILE = os.path.join(
    logPath,
    'plugins',
    f'last_result.{pluginName}.log'
)

plugin_objects = Plugin_Objects(RESULT_FILE)


def main():
    mylog('verbose', [f'[{pluginName}] In script'])

    site_configs = get_setting_value('UNIFIAPI_sites')

    mylog(
        'verbose',
        [f'[{pluginName}] number of unifi_sites_configs: '
         f'{len(site_configs)}']
    )

    for site_config in site_configs:
        site_config = decode_settings_base64(site_config)

        mylog(
            'verbose',
            [f'[{pluginName}] siteDict: {json.dumps(site_config)}']
        )

        mylog(
            'none',
            [f'[{pluginName}] Connecting to: '
             f'{site_config["UNIFIAPI_site_name"]}']
        )

        api = SiteManagerAPI(
            api_key=site_config["UNIFIAPI_api_key"],
            version=site_config["UNIFIAPI_api_version"],
            base_url=site_config["UNIFIAPI_base_url"],
            verify_ssl=site_config["UNIFIAPI_verify_ssl"]
        )

        sites = api.get_sites().get("data", [])

        for site in sites:
            device_data = get_device_data(site, api)

            if not device_data:
                continue

            site_name = (
                site.get("name")
                or site_config.get("UNIFIAPI_site_name")
            )

            for device in device_data:
                plugin_objects.add_object(
                    primaryId=device["dev_mac"],
                    secondaryId=device["dev_ip"],
                    watched1=device["dev_name"],
                    watched2=device["dev_type"],
                    watched3=device["dev_connected"],
                    watched4=device["dev_parent_mac"],
                    extra="",
                    foreignKey=device["dev_mac"],
                    helpVal1=site_name,
                    helpVal2=device["dev_vlan_id"],
                    helpVal3=device["dev_vlan_name"],
                    helpVal4=device["dev_wan_name"]
                )

            mylog(
                'verbose',
                [f'[{pluginName}] New entries: "{len(device_data)}"']
            )

        plugin_objects.write_result_file()

    return 0


def get_device_data(site, api):
    site_id = site["id"]
    site_name = site.get("name", "Unnamed Site")

    mylog(
        'verbose',
        [f'[{pluginName}] Site: {site_name} ({site_id})']
    )

    # -------------------------------------------------------------------------
    # Networks
    # -------------------------------------------------------------------------

    networks_resp = api.get_networks(site_id)
    networks = networks_resp.get("data", [])

    mylog(
        'trace',
        [f'[{pluginName}] Site: {site_name} networks: '
         f'{json.dumps(networks_resp, indent=2)}']
    )

    network_lookup = {
        network["id"]: network
        for network in networks
        if network.get("id")
    }

    default_network = next(
        (
            network
            for network in networks
            if network.get("default") is True
        ),
        None
    )

    # -------------------------------------------------------------------------
    # WiFi broadcasts
    # -------------------------------------------------------------------------

    wifi_broadcasts_resp = api.get_wifi_broadcasts(site_id)
    wifi_broadcasts = wifi_broadcasts_resp.get("data", [])

    mylog(
        'trace',
        [f'[{pluginName}] WIFI BROADCASTS: '
         f'{json.dumps(wifi_broadcasts_resp, indent=2)}']
    )

    wifi_lookup = {
        wifi["name"]: wifi
        for wifi in wifi_broadcasts
        if wifi.get("name")
    }

    # -------------------------------------------------------------------------
    # WANs
    # -------------------------------------------------------------------------

    wans_resp = api.get_wans(site_id)

    mylog(
        'trace',
        [f'[{pluginName}] Site: {site_name} WANs: '
         f'{json.dumps(wans_resp, indent=2)}']
    )

    # The API exposes WAN definitions, but does not provide a client/device
    # -> WAN association in the responses currently supported here.

    # -------------------------------------------------------------------------
    # UniFi devices
    # -------------------------------------------------------------------------

    devices_resp = api.get_unifi_devices(site_id)
    devices = devices_resp.get("data", [])

    mylog(
        'trace',
        [f'[{pluginName}] Site: {site_name} UniFi devices: '
         f'{json.dumps(devices_resp, indent=2)}']
    )

    device_id_to_mac = {
        device["id"]: device.get("macAddress", "")
        for device in devices
        if device.get("id")
    }

    def resolve_parent_mac(uplink_device_id):
        if not uplink_device_id:
            return "internet"

        return device_id_to_mac.get(uplink_device_id, "Unknown")

    device_data = []

    # -------------------------------------------------------------------------
    # UniFi infrastructure devices
    # -------------------------------------------------------------------------

    for device in devices:
        features = device.get("features", [])

        if "accessPoint" in features:
            device_type = "AP"
        elif "switching" in features:
            device_type = "Switch"
        else:
            device_type = "Unknown"

        device_data.append({
            "dev_mac": device.get("macAddress", ""),
            "dev_ip": device.get("ipAddress", ""),
            "dev_name": device.get("name", ""),
            "dev_type": device_type,
            "dev_connected": "",
            "dev_parent_mac": resolve_parent_mac(
                device.get("uplinkDeviceId")
            ),
            "dev_vlan_id": "null",
            "dev_vlan_name": "null",
            "dev_wan_name": "null"
        })

    # -------------------------------------------------------------------------
    # Clients
    # -------------------------------------------------------------------------

    clients_resp = api.get_clients(site_id)
    clients = clients_resp.get("data", [])

    for client in clients:
        client_data = {
            "dev_mac": client.get("macAddress", ""),
            "dev_ip": client.get("ipAddress", ""),
            "dev_name": client.get("name", ""),
            "dev_type": "",
            "dev_connected": client.get("connectedAt", ""),
            "dev_parent_mac": resolve_parent_mac(
                client.get("uplinkDeviceId")
            ),
            "dev_vlan_id": "null",
            "dev_vlan_name": "null",
            "dev_wan_name": "null"
        }

        # The Integration API client response currently does not expose
        # network/VLAN information. Do not infer it from unsupported fields.

        device_data.append(client_data)

    return device_data


if __name__ == '__main__':
    main()