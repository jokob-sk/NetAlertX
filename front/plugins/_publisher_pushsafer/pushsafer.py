
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

# Register NetAlertX directories
INSTALL_PATH="/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

import conf
from const import confFileName, logPath
from plugin_helper import Plugin_Objects, handleEmpty
from logger import mylog, Logger, append_line_to_file
from helper import get_setting_value, hide_string
from utils.datetime_utils import timeNowDB
from models.notification_instance import NotificationInstance
from database import DB
from pytz import timezone

# Make sure the TIMEZONE for logging is correct
conf.tz = timezone(get_setting_value('TIMEZONE'))

# Make sure log level is initialized correctly
Logger(get_setting_value('LOG_LEVEL'))

pluginName = 'PUSHSAFER'

LOG_PATH = logPath + '/plugins'
RESULT_FILE = os.path.join(LOG_PATH, f'last_result.{pluginName}.log')



def main():
    
    mylog('verbose', [f'[{pluginName}](publisher) In script'])    
    
    # Check if basic config settings supplied
    if check_config() == False:
        mylog('none', [f'[{pluginName}] ⚠ ERROR: Publisher notification gateway not set up correctly. Check your {confFileName} {pluginName}_* variables.'])
        return

    # Create a database connection
    db = DB()  # instance of class DB
    db.open()

    # Initialize the Plugin obj output file
    plugin_objects = Plugin_Objects(RESULT_FILE)

    # Create a NotificationInstance instance
    notifications = NotificationInstance(db)

    # Retrieve new notifications
    new_notifications = notifications.getNew()

    # Process the new notifications (see the Notifications DB table for structure or check the /php/server/query_json.php?file=table_notifications.json endpoint)
    for notification in new_notifications:

        # Send notification
        response_text, response_status_code = send(notification["Text"])    

        # Log result
        plugin_objects.add_object(
            primaryId   = pluginName,
            secondaryId = timeNowDB(),            
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
            "t" : 'NetAlertX Message',
            "m" : text,
            "s" : 11,
            "v" : 3,
            "i" : 148,
            "c" : '#ef7f7f',
            "d" : 'a',
            "u" : get_setting_value('REPORT_DASHBOARD_URL'),
            "ut" : 'Open NetAlertX',
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

