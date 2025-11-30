#!/usr/bin/env python
"""
NetAlertX plugin: PIHOLEAPI
Imports devices from Pi-hole v6 API (Network endpoints) into NetAlertX plugin results.
"""

import os
import sys
import datetime
import requests
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# --- NetAlertX plugin bootstrap (match example) ---
INSTALL_PATH = os.getenv('NETALERTX_APP', '/app')
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

pluginName = 'PIHOLEAPI'

from plugin_helper import Plugin_Objects, is_mac  # noqa: E402 [flake8 lint suppression]
from logger import mylog, Logger  # noqa: E402 [flake8 lint suppression]
from helper import get_setting_value  # noqa: E402 [flake8 lint suppression]
from const import logPath  # noqa: E402 [flake8 lint suppression]
import conf  # noqa: E402 [flake8 lint suppression]
from pytz import timezone  # noqa: E402 [flake8 lint suppression]
from utils.crypto_utils import string_to_mac_hash  # noqa: E402 [flake8 lint suppression]

# Setup timezone & logger using standard NAX helpers
conf.tz = timezone(get_setting_value('TIMEZONE'))
Logger(get_setting_value('LOG_LEVEL'))

LOG_PATH = logPath + '/plugins'
RESULT_FILE = os.path.join(LOG_PATH, f'last_result.{pluginName}.log')

plugin_objects = Plugin_Objects(RESULT_FILE)

# --- Global state for session ---
PIHOLEAPI_URL = None
PIHOLEAPI_PASSWORD = None
PIHOLEAPI_SES_VALID = False
PIHOLEAPI_SES_SID = None
PIHOLEAPI_SES_CSRF = None
PIHOLEAPI_API_MAXCLIENTS = None
PIHOLEAPI_VERIFY_SSL = True
PIHOLEAPI_RUN_TIMEOUT = 10
PIHOLEAPI_FAKE_MAC = get_setting_value('PIHOLEAPI_FAKE_MAC')
VERSION_DATE = "NAX-PIHOLEAPI-1.0"


# ------------------------------------------------------------------
def pihole_api_auth():
    """Authenticate to Pi-hole v6 API and populate session globals."""

    global PIHOLEAPI_SES_VALID, PIHOLEAPI_SES_SID, PIHOLEAPI_SES_CSRF

    if not PIHOLEAPI_URL:
        mylog('none', [f'[{pluginName}] PIHOLEAPI_URL not configured — skipping.'])
        return False

    # handle SSL verification setting - disable insecure warnings only when PIHOLEAPI_VERIFY_SSL=False
    if not PIHOLEAPI_VERIFY_SSL:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "User-Agent": "NetAlertX/" + VERSION_DATE
    }
    data = {"password": PIHOLEAPI_PASSWORD}

    try:
        resp = requests.post(PIHOLEAPI_URL + 'api/auth', headers=headers, json=data, verify=PIHOLEAPI_VERIFY_SSL, timeout=PIHOLEAPI_RUN_TIMEOUT)
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        mylog('none', [f'[{pluginName}] Pi-hole auth request timed out. Try increasing PIHOLEAPI_RUN_TIMEOUT.'])
        return False
    except requests.exceptions.ConnectionError:
        mylog('none', [f'[{pluginName}] Connection error during Pi-hole auth. Check PIHOLEAPI_URL and PIHOLEAPI_PASSWORD'])
        return False
    except Exception as e:
        mylog('none', [f'[{pluginName}] Unexpected auth error: {e}'])
        return False

    try:
        response_json = resp.json()
    except Exception:
        mylog('none', [f'[{pluginName}] Unable to parse Pi-hole auth response JSON.'])
        return False

    session_data = response_json.get('session', {})

    if session_data.get('valid', False):
        PIHOLEAPI_SES_VALID = True
        PIHOLEAPI_SES_SID = session_data.get('sid')
        # csrf might not be present if no password set
        PIHOLEAPI_SES_CSRF = session_data.get('csrf')
        mylog('verbose', [f'[{pluginName}] Authenticated to Pi-hole (sid present).'])
        return True
    else:
        mylog('none', [f'[{pluginName}] Pi-hole auth required or failed.'])
        return False


# ------------------------------------------------------------------
def pihole_api_deauth():
    """Logout from Pi-hole v6 API (best-effort)."""
    global PIHOLEAPI_SES_VALID, PIHOLEAPI_SES_SID, PIHOLEAPI_SES_CSRF

    if not PIHOLEAPI_URL:
        return
    if not PIHOLEAPI_SES_SID:
        return

    headers = {"X-FTL-SID": PIHOLEAPI_SES_SID}
    try:
        requests.delete(PIHOLEAPI_URL + 'api/auth', headers=headers, verify=PIHOLEAPI_VERIFY_SSL, timeout=PIHOLEAPI_RUN_TIMEOUT)
    except Exception:
        # ignore errors on logout
        pass
    PIHOLEAPI_SES_VALID = False
    PIHOLEAPI_SES_SID = None
    PIHOLEAPI_SES_CSRF = None


# ------------------------------------------------------------------
def get_pihole_interface_data():
    """Return dict mapping mac -> [ipv4 addresses] from Pi-hole interfaces endpoint."""

    result = {}
    if not PIHOLEAPI_SES_VALID:
        return result

    headers = {"X-FTL-SID": PIHOLEAPI_SES_SID}
    if PIHOLEAPI_SES_CSRF:
        headers["X-FTL-CSRF"] = PIHOLEAPI_SES_CSRF

    try:
        resp = requests.get(PIHOLEAPI_URL + 'api/network/interfaces', headers=headers, verify=PIHOLEAPI_VERIFY_SSL, timeout=PIHOLEAPI_RUN_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        mylog('none', [f'[{pluginName}] Failed to fetch Pi-hole interfaces: {e}'])
        return result

    for interface in data.get('interfaces', []):
        mac_address = interface.get('address')
        if not mac_address or mac_address == "00:00:00:00:00:00":
            continue
        addrs = []
        for addr in interface.get('addresses', []):
            if addr.get('family') == 'inet':
                a = addr.get('address')
                if a:
                    addrs.append(a)
        if addrs:
            result[mac_address] = addrs
    return result


# ------------------------------------------------------------------
def get_pihole_network_devices():
    """Return list of devices from Pi-hole v6 API (devices endpoint)."""

    devices = []

    # return empty list if no session available
    if not PIHOLEAPI_SES_VALID:
        return devices

    # prepare headers
    headers = {"X-FTL-SID": PIHOLEAPI_SES_SID}
    if PIHOLEAPI_SES_CSRF:
        headers["X-FTL-CSRF"] = PIHOLEAPI_SES_CSRF

    params = {
        'max_devices': str(PIHOLEAPI_API_MAXCLIENTS),
        'max_addresses': '2'
    }

    try:
        resp = requests.get(PIHOLEAPI_URL + 'api/network/devices', headers=headers, params=params, verify=PIHOLEAPI_VERIFY_SSL, timeout=PIHOLEAPI_RUN_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        mylog('debug', [f'[{pluginName}] Pi-hole API returned data: {json.dumps(data)}'])

    except Exception as e:
        mylog('none', [f'[{pluginName}] Failed to fetch Pi-hole devices: {e}'])
        return devices

    # The API returns 'devices' list
    return data.get('devices', [])


# ------------------------------------------------------------------
def gather_device_entries():
    """
    Build a list of device entries suitable for Plugin_Objects.add_object.
    Each entry is a dict with: mac, ip, name, macVendor, lastQuery
    """
    entries = []

    iface_map = get_pihole_interface_data()
    devices = get_pihole_network_devices()
    now_ts = int(datetime.datetime.now().timestamp())

    for device in devices:
        hwaddr = device.get('hwaddr')
        if not hwaddr or hwaddr == "00:00:00:00:00:00":
            continue

        macVendor = device.get('macVendor', '')
        lastQuery = device.get('lastQuery')
        # 'ips' is a list of dicts: {ip, name}
        for ip_info in device.get('ips', []):
            ip = ip_info.get('ip')
            if not ip:
                continue

            name = ip_info.get('name') or '(unknown)'

            # mark active if ip present on local interfaces
            for mac, iplist in iface_map.items():
                if ip in iplist:
                    lastQuery = str(now_ts)

            tmpMac = hwaddr.lower()

            # ensure fake mac if enabled
            if PIHOLEAPI_FAKE_MAC and is_mac(tmpMac) is False:
                tmpMac = string_to_mac_hash(ip)

            entries.append({
                'mac': tmpMac,
                'ip': ip,
                'name': name,
                'macVendor': macVendor,
                'lastQuery': str(lastQuery) if lastQuery is not None else ''
            })

    return entries


# ------------------------------------------------------------------
def main():
    """Main plugin entrypoint."""
    global PIHOLEAPI_URL, PIHOLEAPI_PASSWORD, PIHOLEAPI_API_MAXCLIENTS, PIHOLEAPI_VERIFY_SSL, PIHOLEAPI_RUN_TIMEOUT

    mylog('verbose', [f'[{pluginName}] start script.'])

    # Load settings from NAX config
    PIHOLEAPI_URL = get_setting_value('PIHOLEAPI_URL')

    # ensure trailing slash
    if not PIHOLEAPI_URL.endswith('/'):
        PIHOLEAPI_URL += '/'

    PIHOLEAPI_PASSWORD = get_setting_value('PIHOLEAPI_PASSWORD')
    PIHOLEAPI_API_MAXCLIENTS = get_setting_value('PIHOLEAPI_API_MAXCLIENTS')
    # Accept boolean or string "True"/"False"
    PIHOLEAPI_VERIFY_SSL = get_setting_value('PIHOLEAPI_SSL_VERIFY')
    PIHOLEAPI_RUN_TIMEOUT = get_setting_value('PIHOLEAPI_RUN_TIMEOUT')

    # Authenticate
    if not pihole_api_auth():
        mylog('none', [f'[{pluginName}] Authentication failed — no devices imported.'])
        return 1

    try:
        device_entries = gather_device_entries()

        if not device_entries:
            mylog('verbose', [f'[{pluginName}] No devices found on Pi-hole.'])
        else:
            for entry in device_entries:

                if is_mac(entry['mac']):
                    # Map to Plugin_Objects fields
                    mylog('verbose', [f"[{pluginName}] found: {entry['name']}|{entry['mac']}|{entry['ip']}"])

                    plugin_objects.add_object(
                        primaryId=str(entry['mac']),
                        secondaryId=str(entry['ip']),
                        watched1=str(entry['name']),
                        watched2=str(entry['macVendor']),
                        watched3=str(entry['lastQuery']),
                        watched4="",
                        extra=pluginName,
                        foreignKey=str(entry['mac'])
                    )
                else:
                    mylog('verbose', [f"[{pluginName}] Skipping invalid MAC (see PIHOLEAPI_FAKE_MAC setting): {entry['name']}|{entry['mac']}|{entry['ip']}"])

        # Write result file for NetAlertX to ingest
        plugin_objects.write_result_file()
        mylog('verbose', [f'[{pluginName}] Script finished. Imported {len(device_entries)} entries.'])

    finally:
        # Deauth best-effort
        pihole_api_deauth()

    return 0


if __name__ == '__main__':
    main()
