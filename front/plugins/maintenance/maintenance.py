# !/usr/bin/env python

import os
import sys
from collections import deque

# Register NetAlertX directories
INSTALL_PATH = os.getenv('NETALERTX_APP', '/app')
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from logger import mylog, Logger  # noqa: E402 [flake8 lint suppression]
from helper import get_setting_value  # noqa: E402 [flake8 lint suppression]
from const import logPath  # noqa: E402 [flake8 lint suppression]
from messaging.in_app import remove_old  # noqa: E402 [flake8 lint suppression]
import conf  # noqa: E402 [flake8 lint suppression]
from pytz import timezone  # noqa: E402 [flake8 lint suppression]

# Make sure the TIMEZONE for logging is correct
conf.tz = timezone(get_setting_value('TIMEZONE'))

# Make sure log level is initialized correctly
Logger(get_setting_value('LOG_LEVEL'))

pluginName = 'MAINT'

LOG_PATH = logPath + '/plugins'
LOG_FILE = os.path.join(LOG_PATH, f'script.{pluginName}.log')
RESULT_FILE = os.path.join(LOG_PATH, f'last_result.{pluginName}.log')


def main():

    mylog('verbose', [f'[{pluginName}] In script'])

    MAINT_LOG_LENGTH = int(get_setting_value('MAINT_LOG_LENGTH'))
    MAINT_NOTI_LENGTH = int(get_setting_value('MAINT_NOTI_LENGTH'))

    # Check if set
    if MAINT_LOG_LENGTH != 0:

        mylog('verbose', [f'[{pluginName}] Cleaning file'])

        logFile = logPath + "/app.log"

        # Using a deque to efficiently keep the last N lines
        lines_to_keep = deque(maxlen=MAINT_LOG_LENGTH)

        with open(logFile, 'r') as file:
            # Read lines from the file and store the last N lines
            for line in file:
                lines_to_keep.append(line)

        with open(logFile, 'w') as file:
            # Write the last N lines back to the file
            file.writelines(lines_to_keep)

        mylog('verbose', [f'[{pluginName}] Cleanup finished'])

    # Check if set
    if MAINT_NOTI_LENGTH != 0:
        mylog('verbose', [f'[{pluginName}] Cleaning in-app notification history'])
        remove_old(MAINT_NOTI_LENGTH)

    return 0


# ===============================================================================
# BEGIN
# ===============================================================================
if __name__ == '__main__':
    main()
