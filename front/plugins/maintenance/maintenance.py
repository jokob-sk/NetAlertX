#!/usr/bin/env python
# test script by running:
# /home/pi/pialert/front/plugins/maintenance/maintenance.py 

import os
import pathlib
import argparse
import sys
import hashlib
import csv
import sqlite3
from io import StringIO
from datetime import datetime
from collections import deque

sys.path.extend(["/home/pi/pialert/front/plugins", "/home/pi/pialert/pialert"])

# pialert modules
from plugin_helper import Plugin_Object, Plugin_Objects, decodeBase64
from logger import mylog, append_line_to_file
from helper import timeNowTZ, get_setting_value
from const import logPath, pialertPath


CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
LOG_FILE = os.path.join(CUR_PATH, 'script.log')
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

pluginName = 'MAINT'

def main():

    mylog('verbose', [f'[{pluginName}] In script'])    

    MAINT_LOG_LENGTH = int(get_setting_value('MAINT_LOG_LENGTH'))

    # Check if set
    if MAINT_LOG_LENGTH != 0:

        mylog('verbose', [f'[{pluginName}] Cleaning file'])   

        logFile = logPath + "/pialert.log"

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

      

    return 0


#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    main()