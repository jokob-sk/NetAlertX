#!/usr/bin/env python
# Based on the work of https://github.com/leiweibau/Pi.Alert

import argparse
import requests
import pathlib
import sys
import os
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Register NetAlertX directories
INSTALL_PATH="/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from plugin_helper import Plugin_Objects
from datetime import datetime
from const import logPath
from helper import timeNowTZ, get_setting_value 
import conf
from pytz import timezone
from logger import mylog, Logger

# Make sure the TIMEZONE for logging is correct
conf.tz = timezone(get_setting_value('TIMEZONE'))

# Make sure log level is initialized correctly
Logger(get_setting_value('LOG_LEVEL'))

pluginName = 'WEBMON'

LOG_PATH = logPath + '/plugins'
RESULT_FILE = os.path.join(LOG_PATH, f'last_result.{pluginName}.log')


mylog('verbose', [f'[{pluginName}] In script'])

def main():

    values = get_setting_value('WEBMON_urls_to_check')

    mylog('verbose', [f'[{pluginName}] Checking URLs: {values}'])
   

    if len(values) > 0:
        plugin_objects = Plugin_Objects(RESULT_FILE)
        # plugin_objects = service_monitoring(values.urls.split('=')[1].split(','), plugin_objects)
        plugin_objects = service_monitoring(values, plugin_objects)
        plugin_objects.write_result_file()
    else:
        return

def check_services_health(site):
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    try:
        resp = requests.get(site, verify=False, timeout=10)
        latency = resp.elapsed.total_seconds()
        status = resp.status_code
    except requests.exceptions.SSLError:
        status = 503
        latency = 99999
    except:
        status = 503
        latency = 99999
    return status, latency

def service_monitoring(urls, plugin_objects):
    for site in urls:
        status, latency = check_services_health(site)
        plugin_objects.add_object(
            primaryId=site,
            secondaryId='null',            
            watched1=status,
            watched2=latency,
            watched3='null',
            watched4='null',
            extra='null',
            foreignKey='null'
        )
    return plugin_objects

if __name__ == '__main__':
    sys.exit(main())


