
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
from helper import timeNowTZ, get_setting_value
from notification import Notification_obj
from database import DB


CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

pluginName = 'NTFY'

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
        response_text, response_status_code = send(notification["HTML"], notification["Text"])    

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
def check_config():
    if get_setting_value('NTFY_HOST') == '' or get_setting_value('NTFY_TOPIC') == '':        
        return False
    else:
        return True
    
#-------------------------------------------------------------------------------
def send(html, text):

    response_text = ''
    response_status_code = ''


    headers = {
        "Title": "Pi.Alert Notification",
        "Actions": "view, Open Dashboard, "+ get_setting_value('REPORT_DASHBOARD_URL'),
        "Priority": "urgent",
        "Tags": "warning"
    }
    
    # if username and password are set generate hash and update header
    if get_setting_value('NTFY_USER') != "" and get_setting_value('NTFY_PASSWORD') != "":
	# Generate hash for basic auth
        # usernamepassword = "{}:{}".format(get_setting_value('NTFY_USER'),get_setting_value('NTFY_PASSWORD'))
        basichash = b64encode(bytes(get_setting_value('NTFY_USER') + ':' + get_setting_value('NTFY_PASSWORD'), "utf-8")).decode("ascii")

	# add authorization header with hash
        headers["Authorization"] = "Basic {}".format(basichash)

    try:
        response = requests.post("{}/{}".format(   get_setting_value('NTFY_HOST'), 
                                        get_setting_value('NTFY_TOPIC')),
                                        data    = text,
                                        headers = headers)

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


if __name__ == '__main__':
    sys.exit(main())

