#!/usr/bin/env python
# Based on the work of https://github.com/leiweibau/Pi.Alert

import json
import subprocess
import argparse
import os
import pathlib
import sys
from datetime import datetime

# Replace these paths with the actual paths to your Pi.Alert directories
sys.path.extend(["/home/pi/pialert/front/plugins", "/home/pi/pialert/pialert"])

import conf
from plugin_helper import Plugin_Objects
from logger import mylog, append_line_to_file
from helper import timeNowTZ, noti_struc


CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

def main():
    
    mylog('verbose', ['[APPRISE](publisher) In script'])    

    parser = argparse.ArgumentParser(description='APPRISE publisher Plugin')
    values = parser.parse_args()

    plugin_objects = Plugin_Objects(RESULT_FILE)

    speedtest_result = send()

    plugin_objects.add_object(
        primaryId   = 'APPRISE',
        secondaryId = timeNowTZ(),            
        watched1    = speedtest_result['download_speed'],
        watched2    = speedtest_result['upload_speed'],
        watched3    = 'null',
        watched4    = 'null',
        extra       = 'null',
        foreignKey  = 'null'
    )

    plugin_objects.write_result_file()

#-------------------------------------------------------------------------------
def check_config():
        if conf.APPRISE_URL == '' or conf.APPRISE_HOST == '':
            mylog('none', ['[Check Config] Error: Apprise service not set up correctly. Check your pialert.conf APPRISE_* variables.'])
            return False
        else:
            return True

#-------------------------------------------------------------------------------
def send(msg: noti_struc):
    html = msg.html
    text = msg.text

    payloadData = ''

    # limit = 1024 * 1024  # 1MB limit (1024 bytes * 1024 bytes = 1MB)
    limit = conf.APPRISE_SIZE

    #  truncate size
    if conf.APPRISE_PAYLOAD == 'html':                 
        if len(msg.html) > limit:
            payloadData = msg.html[:limit] + " <h1> (text was truncated)</h1>"
        else:
            payloadData = msg.html
    if conf.APPRISE_PAYLOAD == 'text':            
        if len(msg.text) > limit:
            payloadData = msg.text[:limit] + " (text was truncated)"
        else:
            payloadData = msg.text

    # Define Apprise compatible payload (https://github.com/caronc/apprise-api#stateless-solution)

    _json_payload = {
        "urls": conf.APPRISE_URL,
        "title": "Pi.Alert Notifications",
        "format": conf.APPRISE_PAYLOAD,
        "body": payloadData
    }

    try:
        # try runnning a subprocess
        p = subprocess.Popen(["curl","-i","-X", "POST" ,"-H", "Content-Type:application/json" ,"-d", json.dumps(_json_payload), conf.APPRISE_HOST], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = p.communicate()
        # write stdout and stderr into .log files for debugging if needed
        

        # Log the stdout and stderr
        mylog('debug', [stdout, stderr])  # TO-DO should be changed to mylog
    except subprocess.CalledProcessError as e:
        # An error occurred, handle it
        mylog('none', [e.output])

if __name__ == '__main__':
    sys.exit(main())
