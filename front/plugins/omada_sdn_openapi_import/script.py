#!/usr/bin/env python

"""
This plugin imports devices and clients from Omada Controller using their OpenAPI.

It was inspired by the 'omada_sdn_imp/omada_sdn.py' plugin,
which relied on the 'tplink_omada_client' library instead of OpenAPI.
However, I found that approach somewhat unstable, so I decided
to give it a shot and create a new plugin with the goal of providing
same, but more reliable results.

Please note that this is my first plugin, and I’m not a Python developer.
Any comments, bug fixes, or contributions are greatly appreciated.

Author: https://github.com/xfilo
"""

__author__ = "xfilo"
__version__ = 0.1       # Initial version

import os
import sys
import urllib3
import requests
import time
import datetime
import pytz

from datetime import datetime
from typing import Literal, Any, Dict

# Define the installation path and extend the system path for plugin imports
INSTALL_PATH = "/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from plugin_helper import Plugin_Objects, is_typical_router_ip, is_mac
from logger import mylog, Logger
from const import logPath
from helper import get_setting_value
import conf

# Make sure the TIMEZONE for logging is correct
conf.tz = pytz.timezone(get_setting_value('TIMEZONE'))

# Make sure log level is initialized correctly
Logger(get_setting_value('LOG_LEVEL'))

pluginName = 'OMDSDNOPENAPI'

# Define the current path and log file paths
LOG_PATH = logPath + '/plugins'
LOG_FILE = os.path.join(LOG_PATH, f'script.{pluginName}.log')
RESULT_FILE = os.path.join(LOG_PATH, f'last_result.{pluginName}.log')

# Disable insecure request warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class OmadaHelper:
    @staticmethod
    def log(message: str, level: Literal["minimal", "verbose", "debug", "trace"] = "minimal") -> None:
        mylog(level, [f"[{pluginName}] {message}"])

    @staticmethod
    def debug(message: str) -> None:
        return OmadaHelper.log(message, "debug")

    @staticmethod
    def verbose(message: str) -> None:
        return OmadaHelper.log(message, "verbose")

    @staticmethod
    def minimal(message: str) -> None:
        return OmadaHelper.log(message, "minimal")

    @staticmethod
    def response(response_type: str, response_message: str, response_result: Any = None) -> Dict[str, Any]:
        return {"response_type": response_type, "response_message": response_message,
                "response_result": response_result}

    @staticmethod
    def timestamp_to_datetime(ms: int, timezone: str) -> Dict[str, Any]:
        """Returns datetime from millisecond timestamp with required timezone."""
        try:
            if not ms or not isinstance(ms, (str, int)):
                raise ValueError(f"Value '{ms}' is not a valid timestamp")

            timestamp = ms / 1000
            tz = pytz.timezone("UTC")
            utc_datetime = datetime.fromtimestamp(timestamp, tz=tz)
            target_timezone = pytz.timezone(timezone)
            local_datetime = utc_datetime.astimezone(target_timezone)
            result = local_datetime.strftime("%Y-%m-%d %H:%M:%S")

            msg = f"Converted timestamp {ms} to datetime {result} with timezone {timezone}"
            OmadaHelper.debug(msg)
            return OmadaHelper.response("success", msg, result)
        except pytz.UnknownTimeZoneError:
            msg = f"Failed to convert timestamp - unknown timezone: {timezone}"
            OmadaHelper.verbose(msg)
            return OmadaHelper.response("error", msg)
        except Exception as ex:
            msg = f"Failed to convert timestamp - error: {str(ex)}"
            OmadaHelper.verbose(msg)
            return OmadaHelper.response("error", msg)

    @staticmethod
    def normalize_mac(mac: str) -> Dict[str, Any]:
        """Returns a normalized version of MAC address."""
        try:
            if not mac or not isinstance(mac, str) or mac is None:
                raise Exception(f"Value '{mac}' is not a valid MAC address")

            result = mac.lower().replace("-", ":")
            msg = f"Normalized MAC address from {mac} to {result}"
            OmadaHelper.debug(msg)
            return OmadaHelper.response("success", msg, result)
        except Exception as ex:
            msg = f"Failed to normalize MAC address '{mac}' - error: {str(ex)}"
            OmadaHelper.verbose(msg)
            return OmadaHelper.response("error", msg)

    @staticmethod
    def normalize_data(input_data: list, input_type: str, site_name: str, timezone: str) -> Dict[str, Any]:
        """Returns a normalized dictionary of input data (clients, devices)."""
        try:
            if not isinstance(input_data, list):
                raise Exception(f"Expected a list, but got '{type(input_data)}'.")

            OmadaHelper.verbose(f"Starting normalization of {len(input_data)} {input_type}(s) from site {site_name}")
            default_entry = {
                "mac_address": "",
                "ip_address": "",
                "name": "",
                "last_seen": "",
                "site_name": site_name,
                "parent_node_mac_address": "",
                "parent_node_port": "",
                "parent_node_ssid": "",
                "vlan_id": "",
            }

            result = []
            for data in input_data:

                mac = OmadaHelper.normalize_mac(data.get("mac"))
                if not isinstance(mac, dict) or mac.get("response_type") != "success":
                    continue
                mac = mac.get("response_result")

                if not is_mac(mac):
                    OmadaHelper.debug(f"Skipping {input_type}, not a MAC address: {mac}")
                    continue

                entry = default_entry.copy()
                entry["mac_address"] = mac
                entry["ip_address"] = data.get("ip", "")
                entry["name"] = data.get("name", "")

                last_seen = OmadaHelper.timestamp_to_datetime(data.get("lastSeen", 0), timezone)
                entry["last_seen"] = last_seen.get("response_result") if isinstance(last_seen, dict) and last_seen.get(
                    "response_type") == "success" else ""

                if input_type == "device":
                    entry["device_type"] = data.get("type")
                    if data.get("type", "") != "gateway":
                        parent_mac = OmadaHelper.normalize_mac(data.get("uplinkDeviceMac"))
                        parent_mac = parent_mac.get("response_result") if isinstance(parent_mac,
                                                                                     dict) and parent_mac.get(
                            "response_type") == "success" else ""
                        entry["parent_node_mac_address"] = parent_mac

                if input_type == "client":
                    entry["vlan_id"] = data.get("vid")
                    entry["device_type"] = data.get("deviceType")
                    if data.get("connectDevType", "") == "gateway":
                        parent_mac = OmadaHelper.normalize_mac(data.get("gatewayMac"))
                        entry["parent_node_mac_address"] = parent_mac.get("response_result") if isinstance(parent_mac,
                                                                                                           dict) and parent_mac.get(
                            "response_type") == "success" else ""
                        entry["parent_node_port"] = data.get("port", "")
                    elif data.get("connectDevType", "") == "switch":
                        parent_mac = OmadaHelper.normalize_mac(data.get("switchMac"))
                        entry["parent_node_mac_address"] = parent_mac.get("response_result") if isinstance(parent_mac,
                                                                                                           dict) and parent_mac.get(
                            "response_type") == "success" else ""
                        entry["parent_node_port"] = data.get("port", "")
                    elif data.get("connectDevType", "") == "ap":
                        parent_mac = OmadaHelper.normalize_mac(data.get("apMac"))
                        entry["parent_node_mac_address"] = parent_mac.get("response_result") if isinstance(parent_mac,
                                                                                                           dict) and parent_mac.get(
                            "response_type") == "success" else ""
                        entry["parent_node_ssid"] = data.get("ssid", "")

                result.append(entry)
                OmadaHelper.debug(f"Processed {input_type} entry: {entry}")

            msg = f"Successfully normalized {len(result)} {input_type}(s) from site: {site_name}"
            OmadaHelper.verbose(msg)
            final_result = OmadaHelper.response("success", msg, result)
        except Exception as ex:
            msg = f"Failed normalizing {input_type}(s) from site '{site_name}' - error: {str(ex)}"
            OmadaHelper.verbose(msg)
            final_result = OmadaHelper.response("error", msg)

        return final_result


class OmadaAPI:
    def __init__(self, options: dict):
        OmadaHelper.debug("Initializing OmadaAPI with provided options")

        # Define parameters: required, optional, and default values
        params = {
            "host": {"type": str, "required": True},
            "omada_id": {"type": str, "required": True},
            "client_id": {"type": str, "required": True},
            "client_secret": {"type": str, "required": True},
            "verify_ssl": {"type": bool, "required": False, "default": True},
            "page_size": {"type": int, "required": False, "default": 1000},
            "sites": {"type": list, "required": False, "default": []}
        }

        # Validate and set attributes
        for param_name, param_info in params.items():
            value = options.get(param_name, param_info.get("default"))

            if param_info["required"] and (value is None or (param_info["type"] == str and not value)):
                raise ValueError(f"{param_name} is required and must be a non-empty {param_info['type'].__name__}")

            if not isinstance(value, param_info["type"]):
                raise TypeError(f"{param_name} must be of type {param_info['type'].__name__}")

            setattr(self, param_name, value)
            OmadaHelper.debug(f"Initialized option '{param_name}' with value: {value}")

        # Other parameters
        self.available_sites_dict = {}
        self.active_sites_dict = {}
        self.access_token = None
        self.refresh_token = None

        OmadaHelper.verbose("OmadaAPI initialized")

    def _get_headers(self, include_auth: bool = True) -> dict:
        """Return request headers."""
        headers = {"Content-type": "application/json"}
        if include_auth == True:
            if not self.access_token:
                OmadaHelper.debug("No access token available for headers")
            else:
                headers["Authorization"] = f"AccessToken={self.access_token}"
        OmadaHelper.debug(f"Generated headers: {headers}")
        return headers

    def _make_request(self, method: str, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        time.sleep(1)  # Sleep before making any request so it does not rate-limited
        OmadaHelper.verbose(f"{method} request to endpoint: {endpoint}")
        url = f"{getattr(self, 'host')}{endpoint}"
        headers = self._get_headers(kwargs.pop('include_auth', True))
        try:
            response = requests.request(method, url, headers=headers, verify=getattr(self, 'verify_ssl'), **kwargs)
            response.raise_for_status()
            data = response.json()
            response_type = "error" if data.get("errorCode", 0) != 0 else "success"
            msg = f"{method} request completed: {endpoint}"
            OmadaHelper.minimal(msg)
            return OmadaHelper.response(response_type, msg, data)
        except requests.exceptions.RequestException as ex:
            msg = f"{method} request failed: {str(ex)}"
            OmadaHelper.minimal(f"{method} request to {endpoint} failed")
            OmadaHelper.verbose(msg)
            return OmadaHelper.response("error", msg)

    def authenticate(self) -> Dict[str, any]:
        """Make an endpoint request to get access token."""
        OmadaHelper.verbose("Starting authentication process")
        endpoint = "/openapi/authorize/token?grant_type=client_credentials"
        payload = {
            "omadacId": getattr(self, 'omada_id'),
            "client_id": getattr(self, 'client_id'),
            "client_secret": getattr(self, 'client_secret')
        }

        response = self._make_request("POST", endpoint, json=payload, include_auth=False)
        if response["response_type"] == "success":
            token_data = response["response_result"]
            if token_data.get("errorCode") == 0:
                self.access_token = token_data["result"]["accessToken"]
                self.refresh_token = token_data["result"]["refreshToken"]
                OmadaHelper.minimal("Authentication successful")
                return OmadaHelper.response("success", "Authenticated successfully")

        OmadaHelper.minimal("Authentication failed")
        OmadaHelper.debug(f"Authentication response: {response}")
        return OmadaHelper.response("error",
                                    f"Authentication failed - error: {response.get('response_result').get('msg')}")

    def get_clients(self, site_id: str) -> Dict[str, Any]:
        """Make an endpoint request to get all online clients on a site."""
        OmadaHelper.verbose(f"Retrieving clients for site: {site_id}")
        endpoint = f"/openapi/v1/{getattr(self, 'omada_id')}/sites/{site_id}/clients?page=1&pageSize={getattr(self, 'page_size')}"
        return self._make_request("GET", endpoint)

    def get_devices(self, site_id: str) -> Dict[str, Any]:
        """Make an endpoint request to get all online devices on a site."""
        OmadaHelper.verbose(f"Retrieving devices for site: {site_id}")
        endpoint = f"/openapi/v1/{getattr(self, 'omada_id')}/sites/{site_id}/devices?page=1&pageSize={getattr(self, 'page_size')}"
        return self._make_request("GET", endpoint)

    def get_sites(self) -> Dict[str, Any]:
        """Make an endpoint request to populate all accesible sites."""
        OmadaHelper.verbose("Retrieving all accessible sites")
        endpoint = f"/openapi/v1/{getattr(self, 'omada_id')}/sites?page=1&pageSize={getattr(self, 'page_size')}"
        return self._make_request("GET", endpoint)

    def populate_sites(self) -> Dict[str, Any]:
        """Make an endpoint request to populate sites."""
        try:
            OmadaHelper.verbose("Starting site population process")

            # All allowed sites for credentials
            all_sites = self.get_sites()["response_result"].get("result").get("data", [])
            OmadaHelper.debug(f"Retrieved {len(all_sites)} sites in total")

            # All available sites
            self.available_sites_dict = {site["siteId"]: site["name"] for site in all_sites}
            OmadaHelper.debug(f"Available sites: {self.available_sites_dict}")

            # All valid sites from input
            active_sites_by_id = {site["siteId"]: site["name"] for site in all_sites if
                                  site["siteId"] in self.requested_sites()}
            active_sites_by_name = {site["siteId"]: site["name"] for site in all_sites if
                                    site["name"] in self.requested_sites()}
            self.active_sites_dict = active_sites_by_id | active_sites_by_name
            OmadaHelper.debug(f"Active sites after filtering: {self.active_sites_dict}")

            # If none of the input sites is valid/accessible, default to the first available site
            if not self.active_sites_dict:
                OmadaHelper.verbose(
                    "No valid site requested by configuration options, defaulting to first available site")
                first_available_site = next(iter(self.available_sites_dict.items()), (None, None))
                if first_available_site[0]:  # Check if there's an available site
                    self.active_sites_dict = {first_available_site[0]: first_available_site[1]}
                    OmadaHelper.debug(f"Using first available site: {first_available_site}")

            msg = f"Populated {len(self.active_sites_dict)} active sites"
            OmadaHelper.verbose(msg)
            result = OmadaHelper.response("success", msg)
        except Exception as ex:
            OmadaHelper.minimal("Failed to populate sites")
            msg = f"Site population error: {str(ex)}"
            OmadaHelper.verbose(msg)
            result = OmadaHelper.response("error", msg)

        return result

    def requested_sites(self) -> list:
        """Returns sites requested by user."""
        return getattr(self, 'sites')

    def available_sites(self) -> dict:
        """Returns all available sites."""
        return self.available_sites_dict

    def active_sites(self) -> dict:
        """Returns the sites the code will use."""
        return self.active_sites_dict


def make_entries(plugin_objects: Plugin_Objects, normalized_input_data: dict) -> None:
    if normalized_input_data.get("response_type", "error") != "success":
        OmadaHelper.minimal(
            f"Unable to make entries - error: {normalized_input_data.get('response_message', 'Not provided.')}")
        return

    response_result = normalized_input_data.get("response_result", {})
    for entry in response_result:
        OmadaHelper.verbose(f"Making entry for: {entry['mac_address']}")

        parent_node = entry["parent_node_mac_address"]
        if len(parent_node) == 0 and entry["device_type"] == "gateway" and is_typical_router_ip(entry["ip_address"]):
            parent_node = "Internet"

        device_type = entry["device_type"].lower()
        if device_type == "iphone":
            device_type = "iPhone"
        elif device_type == "pc":
            device_type = "PC"
        else:
            device_type = device_type.capitalize()

        plugin_objects.add_object(
            primaryId=entry["mac_address"],
            secondaryId=entry["ip_address"],
            watched1=entry["name"],
            watched2=parent_node,
            watched3=entry["parent_node_port"],
            watched4=entry["parent_node_ssid"],
            extra=device_type,
            foreignKey=entry["mac_address"],
            helpVal1=entry["last_seen"],
            helpVal2=entry["site_name"],
            helpVal3=entry["vlan_id"],
            helpVal4="null"
        )


def get_entries(plugin_objects: Plugin_Objects) -> Plugin_Objects:
    OmadaHelper.minimal("Starting data collection process")
    omada_api = OmadaAPI(OPTIONS)

    auth_result = omada_api.authenticate()
    if auth_result["response_type"] == "error":
        OmadaHelper.minimal("Authentication failed, aborting data collection")
        OmadaHelper.debug(f"Authentication error - {auth_result['response_message']}")
        return plugin_objects

    sites_result = omada_api.populate_sites()
    if sites_result["response_type"] == "error":
        OmadaHelper.minimal("Site population failed, aborting data collection")
        OmadaHelper.debug(f"Site population error - {auth_result['response_message']}")
        return plugin_objects

    requested_sites = omada_api.requested_sites()
    available_sites = omada_api.available_sites()
    active_sites = omada_api.active_sites()

    OmadaHelper.verbose(f"Requested sites: {requested_sites}")
    OmadaHelper.verbose(f"Available sites: {available_sites}")
    OmadaHelper.minimal(f"Active sites: {active_sites}")

    for site_id, site_name in active_sites.items():
        OmadaHelper.verbose(f"Processing site: {site_name} ({site_id})")

        devices_response = omada_api.get_devices(site_id)
        if devices_response["response_type"] == "error":
            OmadaHelper.minimal(f"Failed to retrieve devices for site: {site_name}")
        else:
            devices = devices_response["response_result"].get("result").get("data", [])
            OmadaHelper.debug(f"Retrieved {len(devices)} device(s) from site: {site_name}")
            devices = OmadaHelper.normalize_data(devices, "device", site_name, TIMEZONE)
            make_entries(plugin_objects, devices)

        clients_response = omada_api.get_clients(site_id)
        if clients_response["response_type"] == "error":
            OmadaHelper.minimal(f"Failed to retrieve clients for site {site_name}")
        else:
            clients = clients_response["response_result"].get("result").get("data", [])
            OmadaHelper.debug(f"Retrieved {len(clients)} client(s) from site: {site_name}")
            clients = OmadaHelper.normalize_data(clients, "client", site_name, TIMEZONE)
            make_entries(plugin_objects, clients)

        OmadaHelper.verbose(f"Site complete: {site_name} ({site_id})")

    OmadaHelper.minimal("Data collection process completed")
    return plugin_objects


def main():
    start_time = time.time()
    OmadaHelper.minimal("Starting execution")

    # Initialize the Plugin object output file
    plugin_objects = Plugin_Objects(RESULT_FILE)

    # Retrieve options
    global OPTIONS, TIMEZONE
    TIMEZONE = get_setting_value("TIMEZONE")
    OPTIONS = {
        "host": get_setting_value(f"{pluginName}_host").strip(),
        "client_id": get_setting_value(f"{pluginName}_client_id").strip(),
        "client_secret": get_setting_value(f"{pluginName}_client_secret").strip(),
        "omada_id": get_setting_value(f"{pluginName}_omada_id").strip(),
        "sites": get_setting_value(f"{pluginName}_sites"),
        "verify_ssl": get_setting_value(f"{pluginName}_verify_ssl")
    }
    OmadaHelper.verbose("Configuration options loaded")

    # Retrieve entries
    plugin_objects = get_entries(plugin_objects)
    plugin_objects.write_result_file()

    # Finish
    OmadaHelper.minimal(f"Execution completed in {time.time() - start_time:.2f}s, found {len(plugin_objects)} devices and clients")


if __name__ == '__main__':
    main()
