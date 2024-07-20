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
import conf
from pytz import timezone

# Make sure the TIMEZONE for logging is correct
conf.tz = timezone(get_setting_value('TIMEZONE'))

CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

def main():
    parser = argparse.ArgumentParser(description='Simple URL monitoring tool')
    parser.add_argument('urls', action="store", help="URLs to check separated by ','")
    values = parser.parse_args()

    if values.urls:
        plugin_objects = Plugin_Objects(RESULT_FILE)
        plugin_objects = service_monitoring(values.urls.split('=')[1].split(','), plugin_objects)
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


