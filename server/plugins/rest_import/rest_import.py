#!/usr/bin/env python

import os
import sys
import re
import requests
from pytz import timezone

INSTALL_PATH = os.getenv('NETALERTX_APP', '/app')
sys.path.extend([f"{INSTALL_PATH}/server/plugins", f"{INSTALL_PATH}/server"])

from plugin_helper import Plugin_Objects, decode_settings_base64, normalize_mac  # noqa: E402
from logger import mylog, Logger  # noqa: E402
from helper import get_setting_value  # noqa: E402
from const import logPath  # noqa: E402
from utils.crypto_utils import string_to_fake_mac  # noqa: E402
import conf  # noqa: E402

conf.tz = timezone(get_setting_value('TIMEZONE'))
Logger(get_setting_value('LOG_LEVEL'))

pluginName = 'RSTIMPRT'

LOG_PATH = logPath + '/plugins'
RESULT_FILE = os.path.join(LOG_PATH, f'last_result.{pluginName}.log')

VALID_METHODS = ('GET', 'POST')
VALID_AUTH_TYPES = ('none', 'basic', 'bearer')

# Valid normalized MAC: exactly xx:xx:xx:xx:xx:xx with hex digits
_MAC_RE = re.compile(r'^([0-9a-f]{2}:){5}[0-9a-f]{2}$')

# Ordered scan field keys as they appear in add_object() positional slots
SCAN_FIELD_SLOTS = [
    'RSTIMPRT_scanName',        # watched1
    'RSTIMPRT_scanVendor',      # watched2
    'RSTIMPRT_scanSSID',        # watched3
    'RSTIMPRT_scanType',        # watched4
    'RSTIMPRT_scanParentMAC',   # helpVal1
    'RSTIMPRT_scanParentPort',  # helpVal2
    'RSTIMPRT_scanSite',        # helpVal3
    'RSTIMPRT_scanVlan',        # helpVal4
]


def main():
    mylog('verbose', [f'[{pluginName}] In script'])

    import_configs = get_setting_value('RSTIMPRT_imports')
    plugin_objects = Plugin_Objects(RESULT_FILE)

    if not import_configs:
        mylog('none', [f'[{pluginName}] No import definitions configured'])
        plugin_objects.write_result_file()
        return 0

    mylog('verbose', [f'[{pluginName}] Import definitions: {len(import_configs)}'])

    for raw_config in import_configs:
        cfg = decode_settings_base64(raw_config)
        process_import(cfg, plugin_objects)

    plugin_objects.write_result_file()
    return 0


def process_import(cfg, plugin_objects):
    name = cfg.get('RSTIMPRT_name', 'Unnamed')
    url = cfg.get('RSTIMPRT_url', '').strip()
    method = cfg.get('RSTIMPRT_method', 'GET').strip().upper()
    verify_ssl = bool(cfg.get('RSTIMPRT_verify_ssl', True))
    auth_type = cfg.get('RSTIMPRT_auth_type', 'none').strip().lower()
    username = cfg.get('RSTIMPRT_username', '')
    password = cfg.get('RSTIMPRT_password', '')
    bearer_token = cfg.get('RSTIMPRT_bearer_token', '')
    raw_headers = cfg.get('RSTIMPRT_headers', '')
    post_body = cfg.get('RSTIMPRT_post_body', '')
    device_path = cfg.get('RSTIMPRT_device_path', '').strip()
    mac_field = cfg.get('RSTIMPRT_scanMac', '').strip()
    ip_field = cfg.get('RSTIMPRT_scanLastIP', '').strip()
    fake_mac = bool(cfg.get('RSTIMPRT_fake_mac', False))

    mylog('none', [f'[{pluginName}] {name}'])

    if not url:
        mylog('none', [f'[{pluginName}] Skipping "{name}" - URL is empty'])
        return

    if method not in VALID_METHODS:
        mylog('none', [f'[{pluginName}] Skipping "{name}" - invalid method "{method}"'])
        return

    if auth_type not in VALID_AUTH_TYPES:
        mylog('none', [f'[{pluginName}] Skipping "{name}" - invalid auth_type "{auth_type}"'])
        return

    headers = build_headers(raw_headers)
    auth = build_auth(auth_type, username, password, bearer_token, headers)

    response = make_request(name, url, method, verify_ssl, auth, headers, post_body)
    if response is None:
        return

    try:
        data = response.json()
    except ValueError:
        mylog('none', [f'[{pluginName}] Invalid JSON response from "{name}"'])
        return

    records = resolve_path(name, data, device_path)
    if records is None:
        return

    imported = 0
    skipped = 0

    for idx, record in enumerate(records):
        result = map_record(name, idx, record, cfg, mac_field, ip_field, fake_mac)
        if result is None:
            skipped += 1
            continue

        plugin_objects.add_object(
            primaryId   = result['mac'],
            secondaryId = result['ip'],
            watched1    = result['name'],
            watched2    = result['vendor'],
            watched3    = result['ssid'],
            watched4    = result['dev_type'],
            extra       = '',
            foreignKey  = result['mac'],
            helpVal1    = result['parent_mac'],
            helpVal2    = result['parent_port'],
            helpVal3    = result['site'],
            helpVal4    = result['vlan'],
        )
        imported += 1

    mylog('none', [f'[{pluginName}] Retrieved {len(records)} records'])
    mylog('none', [f'[{pluginName}] Imported {imported} devices'])
    if skipped:
        mylog('none', [f'[{pluginName}] Skipped {skipped} devices'])


def build_headers(raw_headers_str):
    headers = {}
    if not raw_headers_str:
        return headers
    for line in raw_headers_str.splitlines():
        line = line.strip()
        if not line or ':' not in line:
            continue
        key, _, value = line.partition(':')
        key = key.strip()
        value = value.strip()
        if key:
            headers[key] = value
    return headers


def build_auth(auth_type, username, password, bearer_token, headers):
    if auth_type == 'basic' and username:
        return (username, password)
    if auth_type == 'bearer' and bearer_token:
        headers['Authorization'] = f'Bearer {bearer_token}'
    return None


def make_request(name, url, method, verify_ssl, auth, headers, post_body):
    try:
        body_data = None
        if method == 'POST' and post_body:
            body_data = post_body

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            auth=auth,
            data=body_data,
            verify=verify_ssl,
            timeout=30,
        )

        mylog('verbose', [f'[{pluginName}] {name} HTTP {response.status_code}'])

        if response.status_code == 401:
            mylog('none', [f'[{pluginName}] Authentication failed for "{name}"'])
            return None

        if not response.ok:
            mylog('none', [f'[{pluginName}] HTTP error {response.status_code} for "{name}"'])
            return None

        return response

    except requests.exceptions.SSLError:
        mylog('none', [f'[{pluginName}] SSL error for "{name}" - try disabling Verify SSL'])
        return None
    except requests.exceptions.ConnectionError:
        mylog('none', [f'[{pluginName}] Connection error for "{name}" - check URL'])
        return None
    except requests.exceptions.Timeout:
        mylog('none', [f'[{pluginName}] Request timed out for "{name}"'])
        return None
    except requests.exceptions.RequestException as e:
        mylog('none', [f'[{pluginName}] Request error for "{name}": {e}'])
        return None


def resolve_path(name, data, path):
    if not path:
        if isinstance(data, list):
            return data
        mylog('none', [f'[{pluginName}] Device path not configured and response is not an array for "{name}"'])
        return None

    node = data
    for key in path.split('.'):
        if not isinstance(node, dict) or key not in node:
            mylog('none', [f'[{pluginName}] Device path not found: {path} for "{name}"'])
            return None
        node = node[key]

    if not isinstance(node, list):
        mylog('none', [f'[{pluginName}] Device path "{path}" does not point to an array for "{name}"'])
        return None

    return node


def map_record(name, idx, record, cfg, mac_field, ip_field, fake_mac):
    raw_mac = record.get(mac_field, '') if mac_field else ''
    raw_ip = record.get(ip_field, '') if ip_field else ''

    mac = _resolve_mac(name, idx, raw_mac, raw_ip, fake_mac)
    if mac is None:
        return None

    ip = str(raw_ip).strip() if raw_ip else ''

    return {
        'mac': mac,
        'ip': ip,
        'name': _get_field(record, cfg, 'RSTIMPRT_scanName'),
        'vendor': _get_field(record, cfg, 'RSTIMPRT_scanVendor'),
        'ssid': _get_field(record, cfg, 'RSTIMPRT_scanSSID'),
        'dev_type': _get_field(record, cfg, 'RSTIMPRT_scanType'),
        'parent_mac': _get_field(record, cfg, 'RSTIMPRT_scanParentMAC'),
        'parent_port': _get_field(record, cfg, 'RSTIMPRT_scanParentPort'),
        'site': _get_field(record, cfg, 'RSTIMPRT_scanSite'),
        'vlan': _get_field(record, cfg, 'RSTIMPRT_scanVlan'),
    }


def _resolve_mac(name, idx, raw_mac, raw_ip, fake_mac):
    if raw_mac:
        mac = validate_mac(str(raw_mac))
        if mac:
            return mac

    if fake_mac:
        ip = str(raw_ip).strip() if raw_ip else ''
        if ip:
            return string_to_fake_mac(ip)
        mylog('none', [f'[{pluginName}] Skipped record {idx} - no IP for fake MAC generation for "{name}"'])
        return None

    mylog('none', [f'[{pluginName}] Skipped record {idx} - invalid MAC address for "{name}"'])
    return None


def _get_field(record, cfg, config_key):
    api_field = cfg.get(config_key, '').strip()
    if not api_field:
        return ''
    value = record.get(api_field, '')
    return str(value).strip() if value is not None else ''


def validate_mac(raw):
    if not raw:
        return None
    mac = normalize_mac(raw)
    if not mac:
        return None
    # normalize_mac reformats any string — verify result is actually a MAC
    if not _MAC_RE.match(mac.lower()):
        return None
    return mac


if __name__ == '__main__':
    main()
