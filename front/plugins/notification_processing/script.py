#!/usr/bin/env python

import os
import pathlib
import argparse
import sys
import hashlib
import csv
import sqlite3
from io import StringIO
from datetime import datetime

sys.path.append("/home/pi/pialert/front/plugins")
sys.path.append('/home/pi/pialert/pialert') 

from plugin_helper import Plugin_Object, Plugin_Objects, decodeBase64
from logger import mylog, append_line_to_file
from helper import timeNowTZ, get_setting_value
from const import logPath, pialertPath, fullDbPath


CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
LOG_FILE = os.path.join(CUR_PATH, 'script.log')
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

pluginName = 'NTFPRCS'

def main():

    mylog('verbose', [f'[{pluginName}] In script'])
    
    # TODO
    # process_notifications(fullDbPath)
    
    mylog('verbose', [f'[{pluginName}] Script finished'])
    
    return 0

#===============================================================================
# Cleanup / upkeep database
#===============================================================================
def process_notifications (dbPath):
   
    # Connect to the PiAlert SQLite database
    conn    = sqlite3.connect(dbPath)
    cursor  = conn.cursor()

    # Cleanup Events
    # mylog('verbose', [f'[DBCLNP] Events: Delete all older than {str(DAYS_TO_KEEP_EVENTS)} days (DAYS_TO_KEEP_EVENTS setting)'])

    # cursor.execute (f"""DELETE FROM Events 
    #                         WHERE eve_DateTime <= date('now', '-{str(DAYS_TO_KEEP_EVENTS)} day')""")
               

    conn.commit()

    # Close the database connection
    conn.close()
    
    

#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    main()