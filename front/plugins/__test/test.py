#!/usr/bin/env python
# Just a testing library plugin for development purposes
import os
import sys
import re
import hashlib


# Register NetAlertX directories
INSTALL_PATH = os.getenv('NETALERTX_APP', '/app')
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

# NetAlertX modules
from const import logPath  # noqa: E402 [flake8 lint suppression]
from plugin_helper import Plugin_Objects  # noqa: E402 [flake8 lint suppression]
from logger import mylog  # noqa: E402 [flake8 lint suppression]
from helper import get_setting_value  # noqa: E402 [flake8 lint suppression]

pluginName = 'TESTONLY'

LOG_PATH = logPath + '/plugins'
RESULT_FILE = os.path.join(LOG_PATH, f'last_result.{pluginName}.log')


# Initialize the Plugin obj output file
plugin_objects = Plugin_Objects(RESULT_FILE)
# Create an MD5 hash object
md5_hash = hashlib.md5()


# globals
def main():
    # START
    mylog('verbose', [f'[{pluginName}] In script'])

    # SPACE FOR TESTING 🔽

    str = "ABC-MBP._another.localdomain."
    # cleanDeviceName(str, match_IP)
    # result = cleanDeviceName(str, True)

    regexes = get_setting_value('NEWDEV_NAME_CLEANUP_REGEX')
    print(regexes)
    subnets = get_setting_value('SCAN_SUBNETS')

    print(subnets)

    for rgx in regexes:
        mylog('trace', ["[cleanDeviceName] applying regex    : " + rgx])
        mylog('trace', ["[cleanDeviceName] name before regex : " + str])

        str = re.sub(rgx, "", str)
        mylog('trace', ["[cleanDeviceName] name after regex  : " + str])

    mylog('debug', ["[cleanDeviceName] output: " + str])
    # SPACE FOR TESTING 🔼

    # END
    mylog('verbose', [f'[{pluginName}] result "{str}"'])


#  -------------INIT---------------------
if __name__ == '__main__':
    sys.exit(main())
