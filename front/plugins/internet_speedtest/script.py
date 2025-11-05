#!/usr/bin/env python

import argparse
import os
import pathlib
import sys
from datetime import datetime
import speedtest

# Register NetAlertX directories
INSTALL_PATH="/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from plugin_helper import Plugin_Objects
from logger import mylog, Logger, append_line_to_file
from helper import get_setting_value 
from utils.datetime_utils import timeNowDB
import conf
from pytz import timezone
from const import logPath

# Make sure the TIMEZONE for logging is correct
conf.tz = timezone(get_setting_value('TIMEZONE'))

# Make sure log level is initialized correctly
Logger(get_setting_value('LOG_LEVEL'))

pluginName = 'INTRSPD'

LOG_PATH = logPath + '/plugins'
RESULT_FILE = os.path.join(LOG_PATH, f'last_result.{pluginName}.log')

def main():
    
    mylog('verbose', ['[INTRSPD] In script'])    

    parser = argparse.ArgumentParser(description='Speedtest Plugin for NetAlertX')
    values = parser.parse_args()

    plugin_objects = Plugin_Objects(RESULT_FILE)
    speedtest_result = run_speedtest()
    plugin_objects.add_object(
        primaryId   = 'Speedtest',
        secondaryId = timeNowDB(),            
        watched1    = speedtest_result['download_speed'],
        watched2    = speedtest_result['upload_speed'],
        watched3    = 'null',
        watched4    = 'null',
        extra       = 'null',
        foreignKey  = 'null'
    )
    plugin_objects.write_result_file()

def run_speedtest():
    try:
        st = speedtest.Speedtest(secure=True)
        st.get_best_server()
        download_speed = round(st.download() / 10**6, 2)  # Convert to Mbps
        upload_speed = round(st.upload() / 10**6, 2)  # Convert to Mbps
        
        mylog('verbose', [f"[INTRSPD] Result (down|up): {str(download_speed)} Mbps|{upload_speed} Mbps"]) 

        return {
            'download_speed': download_speed,
            'upload_speed': upload_speed,
        }
    except Exception as e:
        mylog('verbose', [f"[INTRSPD] Error running speedtest: {str(e)}"]) 
        return {
            'download_speed': -1,
            'upload_speed': -1,
        }

if __name__ == '__main__':
    sys.exit(main())
