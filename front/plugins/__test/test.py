#!/usr/bin/env python
# Just a testing library plugin for development purposes
import json
import subprocess
import argparse
import os
import pathlib
import sys
from datetime import datetime
import time
import re
import hashlib
import sqlite3


# Register NetAlertX directories
INSTALL_PATH="/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

# NetAlertX modules
import conf
from const import apiPath, confFileName, logPath
from utils.plugin_utils import getPluginObject
from plugin_helper import Plugin_Objects
from logger import mylog, Logger, append_line_to_file
from helper import get_setting_value, bytes_to_string, sanitize_string, cleanDeviceName
from models.notification_instance import NotificationInstance
from database import DB, get_device_stats

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
