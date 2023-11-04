
#!/usr/bin/env python

import json
import subprocess
import argparse
import os
import pathlib
import sys
import requests
from datetime import datetime
from base64 import b64encode

# Replace these paths with the actual paths to your Pi.Alert directories
sys.path.extend(["/home/pi/pialert/front/plugins", "/home/pi/pialert/pialert"])

import conf
from plugin_helper import Plugin_Objects, handleEmpty
from logger import mylog, append_line_to_file
from helper import timeNowTZ, get_setting_value, hide_string
from notification import Notification_obj
from database import DB

CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

pluginName = 'PUSHSAFER'

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
        response_text, response_status_code = send(notification["Text"])    

        # Log result
        plugin_objects.add_object(
            primaryId   = pluginName,
            secondaryId = timeNowTZ(),            
            watched1    = notification["GUID"],
            watched2    = handleEmpty(response_text),            
            watched3    = response_status_code,
            watched4    = 'null',
            extra       = 'null',
            foreignKey  = notification["GUID"]
        )

    plugin_objects.write_result_file()


    
#-------------------------------------------------------------------------------
def send(text):

    response_text = ''
    response_status_code = ''

    token = get_setting_value('PUSHSAFER_TOKEN')

    mylog('verbose', [f'[{pluginName}] PUSHSAFER_TOKEN: "{hide_string(token)}"'])    
    

    try:
        url = 'https://www.pushsafer.com/api'
        post_fields = {
            "t" : 'Pi.Alert Message',
            "m" : text,
            "s" : 11,
            "v" : 3,
            "i" : 148,
            "c" : '#ef7f7f',
            "d" : 'a',
            "u" : get_setting_value('REPORT_DASHBOARD_URL'),
            "ut" : 'Open Pi.Alert',
            "k" : token,
            }
        response = requests.post(url, data=post_fields)
        
        response_status_code = response.status_code


        # Check if the request was successful (status code 200)
        if response_status_code == 200:
            response_text = response.text  # This captures the response body/message      
        else:
            response_text = json.dumps(response.text) 

    except requests.exceptions.RequestException as e:  
        mylog('none', [f'[{pluginName}] ⚠ ERROR: ', e])

        response_text = e

        return response_text, response_status_code
    

    return response_text, response_status_code    





#-------------------------------------------------------------------------------
def check_config():
        if get_setting_value('PUSHSAFER_TOKEN') == 'ApiKey':           
            return False
        else:
            return True

#  -------------------------------------------------------
if __name__ == '__main__':
    sys.exit(main())

