#!/usr/bin/env python

import os
import sys
import speedtest

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

    mylog('verbose', ['[INTRSPD] In script'])

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
