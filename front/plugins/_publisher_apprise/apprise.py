#!/usr/bin/env python

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
from helper import timeNowTZ, get_setting_value
from notification import Notification_obj
from database import DB


CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

pluginName = 'APPRISE'

def main():
    
    mylog('verbose', [f'[{pluginName}](publisher) In script'])    
    
    # Check if basic config settings supplied
    if check_config() == False:
        mylog('none', [f'[{pluginName}] ⚠ ERROR: Publisher notification gateway not set up correctly. Check your pialert.conf {pluginName}_* variables.'])
        return

    # Create a database connection
    db = DB()  # instance of class DB
    db.open()

    # Initialize the Plugin obj output file
    plugin_objects = Plugin_Objects(RESULT_FILE)

    # Create a Notification_obj instance
    notifications = Notification_obj(db)

    # Retrieve new notifications
    new_notifications = notifications.getNew()

    # Process the new notifications (see the Notifications DB table for structure or check the /api/table_notifications.json endpoint)
    for notification in new_notifications:

        # Send notification
        result = send(notification["HTML"], notification["Text"])    

        # Log result
        plugin_objects.add_object(
            primaryId   = pluginName,
            secondaryId = timeNowTZ(),            
            watched1    = notification["GUID"],
            watched2    = result,            
            watched3    = 'null',
            watched4    = 'null',
            extra       = 'null',
            foreignKey  = notification["GUID"]
        )

    plugin_objects.write_result_file()

#-------------------------------------------------------------------------------
def check_config():
        if get_setting_value('APPRISE_URL') == '' or get_setting_value('APPRISE_HOST') == '':            
            return False
        else:
            return True

#-------------------------------------------------------------------------------
def send(html, text):

    payloadData = ''
    result = ''

    # limit = 1024 * 1024  # 1MB limit (1024 bytes * 1024 bytes = 1MB)
    limit = get_setting_value('APPRISE_SIZE')

    #  truncate size
    if get_setting_value('APPRISE_PAYLOAD') == 'html':                 
        if len(html) > limit:
            payloadData = html[:limit] + "<h1>(text was truncated)</h1>"
        else:
            payloadData = html
    if get_setting_value('APPRISE_PAYLOAD') == 'text':            
        if len(text) > limit:
            payloadData = text[:limit] + " (text was truncated)"
        else:
            payloadData = text

    # Define Apprise compatible payload (https://github.com/caronc/apprise-api#stateless-solution)

    _json_payload = {
        "urls": get_setting_value('APPRISE_URL'),
        "title": "Pi.Alert Notifications",
        "format": get_setting_value('APPRISE_PAYLOAD'),
        "body": payloadData
    }

    try:
        # try runnning a subprocess
        p = subprocess.Popen(["curl","-i","-X", "POST" ,"-H", "Content-Type:application/json" ,"-d", json.dumps(_json_payload), get_setting_value('APPRISE_HOST')], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = p.communicate()

        # write stdout and stderr into .log files for debugging if needed
        # Log the stdout and stderr
        mylog('debug', [stdout, stderr])  

        # log result
        result = stdout

    except subprocess.CalledProcessError as e:
        # An error occurred, handle it
        mylog('none', [e.output])

        # log result
        result = e.output

    return result

if __name__ == '__main__':
    sys.exit(main())
