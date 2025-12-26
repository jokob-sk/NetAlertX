#!/usr/bin/env python

import os
import sys
import subprocess
import json

# Register NetAlertX directories
INSTALL_PATH = os.getenv('NETALERTX_APP', '/app')
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from plugin_helper import Plugin_Objects  # noqa: E402 [flake8 lint suppression]
from utils.datetime_utils import timeNowDB  # noqa: E402 [flake8 lint suppression]
from logger import mylog, Logger  # noqa: E402 [flake8 lint suppression]
from helper import get_setting_value  # noqa: E402 [flake8 lint suppression]
import conf  # noqa: E402 [flake8 lint suppression]
from pytz import timezone  # noqa: E402 [flake8 lint suppression]
from const import logPath  # noqa: E402 [flake8 lint suppression]

# Make sure the TIMEZONE for logging is correct
conf.tz = timezone(get_setting_value('TIMEZONE'))

# Make sure log level is initialized correctly
Logger(get_setting_value('LOG_LEVEL'))

pluginName = 'INTRSPD'

LOG_PATH = logPath + '/plugins'
RESULT_FILE = os.path.join(LOG_PATH, f'last_result.{pluginName}.log')


def main():

    mylog('verbose', ['[INTRSPD] In script (Native Binary Optimization)'])

    plugin_objects = Plugin_Objects(RESULT_FILE)
    speed_data = run_speedtest()
    
    plugin_objects.add_object(
        primaryId   = 'Speedtest',
        secondaryId = timeNowDB(),
        watched1    = speed_data['down'],    # Download Mbps
        watched2    = speed_data['up'],      # Upload Mbps
        watched3    = speed_data['json'],    # Payload for n8n/webhooks
        watched4    = 'null',
        extra       = 'null',
        foreignKey  = 'null'
    )
    plugin_objects.write_result_file()


def run_speedtest():
    native_bin = '/usr/bin/speedtest'
    cmd = [native_bin, "--format=json", "--accept-license", "--accept-gdpr"]
    
    # Get configurable timeout with minimum 60s enforcement
    try:
        timeout = int(get_setting_value('INTRSPD_TIMEOUT'))
        timeout = max(timeout, 60)
    except (ValueError, TypeError):
        timeout = 60
    
    try:
        mylog('verbose', [f"[INTRSPD] Executing native binary: {native_bin}"])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        
        if result.returncode != 0:
            mylog('none', [f"[INTRSPD] Native binary failed: {result.stderr}"])
            return {'down': 0.0, 'up': 0.0, 'json': '{}'}

        o = json.loads(result.stdout)
        
        try:
            down_mbps = round((o['download']['bandwidth'] * 8) / 10**6, 2)
            up_mbps = round((o['upload']['bandwidth'] * 8) / 10**6, 2)
            
            # Payload optimized for n8n/webhooks
            payload = {
                "download": int(o['download']['bandwidth'] * 8),
                "upload": int(o['upload']['bandwidth'] * 8),
                "ping": o['ping']['latency'],
                "server": {"name": o['server']['name']},
                "timestamp": o['timestamp']
            }
        except (KeyError, ValueError, TypeError) as e:
            mylog('none', [f"[INTRSPD] Failed to process JSON data: {e!s}. Raw output: {result.stdout}"])
            return {'down': 0.0, 'up': 0.0, 'json': json.dumps({"error": "invalid_json_structure", "raw": result.stdout})}
        
        mylog('verbose', [f"[INTRSPD] Result (down|up): {down_mbps} Mbps | {up_mbps} Mbps"])
        
        return {
            'down': down_mbps, 
            'up': up_mbps, 
            'json': json.dumps(payload)
        }

    except subprocess.TimeoutExpired:
        mylog('none', [f"[INTRSPD] Speedtest timed out after {timeout}s"])
        return {'down': 0.0, 'up': 0.0, 'json': json.dumps({"error": "timeout"})}
    except json.JSONDecodeError as e:
        mylog('none', [f"[INTRSPD] Failed to parse JSON output: {e!s}"])
        return {'down': 0.0, 'up': 0.0, 'json': json.dumps({"error": "json_parse_error"})}
    except subprocess.SubprocessError as e:
        mylog('none', [f"[INTRSPD] Subprocess error: {e!s}"])
        return {'down': 0.0, 'up': 0.0, 'json': json.dumps({"error": str(e)})}
    except Exception as e:
        mylog('none', [f"[INTRSPD] Unexpected error: {e!s}"])
        return {'down': 0.0, 'up': 0.0, 'json': json.dumps({"error": str(e)})}


if __name__ == '__main__':
    sys.exit(main())
