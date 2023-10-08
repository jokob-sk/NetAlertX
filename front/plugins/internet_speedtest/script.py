#!/usr/bin/env python

import argparse
import os
import pathlib
import sys
from datetime import datetime
import speedtest

# Replace these paths with the actual paths to your Pi.Alert directories
sys.path.extend(["/home/pi/pialert/front/plugins", "/home/pi/pialert/pialert"])

from plugin_helper import Plugin_Objects
from logger import mylog, append_line_to_file
from helper import timeNowTZ

CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

def main():
    
    mylog('verbose', ['[INTRSPD] In script'])    

    parser = argparse.ArgumentParser(description='Speedtest Plugin for Pi.Alert')
    values = parser.parse_args()

    plugin_objects = Plugin_Objects(RESULT_FILE)
    speedtest_result = run_speedtest()
    plugin_objects.add_object(
        primaryId   = 'Speedtest',
        secondaryId = timeNowTZ(),            
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
        st = speedtest.Speedtest()
        st.get_best_server()
        download_speed = round(st.download() / 10**6, 2)  # Convert to Mbps
        upload_speed = round(st.upload() / 10**6, 2)  # Convert to Mbps

        return {
            'download_speed': download_speed,
            'upload_speed': upload_speed,
        }
    except Exception as e:
        mylog('verbose', [f"Error running speedtest: {str(e)}"]) 
        return {
            'download_speed': -1,
            'upload_speed': -1,
        }

if __name__ == '__main__':
    sys.exit(main())
