
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
import hashlib
import hmac

# Replace these paths with the actual paths to your Pi.Alert directories
sys.path.extend(["/home/pi/pialert/front/plugins", "/home/pi/pialert/pialert"])

# pialert modules
import conf
from const import logPath
from plugin_helper import Plugin_Objects, handleEmpty
from logger import mylog, append_line_to_file
from helper import timeNowTZ, get_setting_value, hide_string, write_file
from notification import Notification_obj
from database import DB

CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

pluginName = 'WEBHOOK'

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
        response_stdout, response_stderr = send(notification["Text"], notification["HTML"], notification["JSON"])    

        # Log result
        plugin_objects.add_object(
            primaryId   = pluginName,
            secondaryId = timeNowTZ(),            
            watched1    = notification["GUID"],
            watched2    = handleEmpty(response_stdout),            
            watched3    = handleEmpty(response_stderr),                        
            watched4    = 'null',
            extra       = 'null',
            foreignKey  = notification["GUID"]
        )

    plugin_objects.write_result_file()


#-------------------------------------------------------------------------------
def check_config():
        if get_setting_value('WEBHOOK_URL') == '':            
            return False
        else:
            return True
        
#-------------------------------------------------------------------------------        

def send (text_data, html_data, json_data):

    response_stderr = ''
    response_stdout = ''

    # limit = 1024 * 1024  # 1MB limit (1024 bytes * 1024 bytes = 1MB)
    limit         = get_setting_value('WEBHOOK_SIZE')
    payloadType   = get_setting_value('WEBHOOK_PAYLOAD')
    endpointUrl   = get_setting_value('WEBHOOK_URL')
    secret        = get_setting_value('WEBHOOK_SECRET')
    requestMethod = get_setting_value('WEBHOOK_REQUEST_METHOD')

    # use data type based on specified payload type
    if payloadType == 'json':
        # In this code, the truncate_json function is used to recursively traverse the JSON object 
        # and remove nodes that exceed the size limit. It checks the size of each node's JSON representation 
        # using json.dumps and includes only the nodes that are within the limit.        
        json_str = json.dumps(json_data)

        if len(json_str) <= limit:
            payloadData = json_data
        else:
            def truncate_json(obj):
                if isinstance(obj, dict):
                    return {
                        key: truncate_json(value)
                        for key, value in obj.items()
                        if len(json.dumps(value)) <= limit
                    }
                elif isinstance(obj, list):
                    return [
                        truncate_json(item)
                        for item in obj
                        if len(json.dumps(item)) <= limit
                    ]
                else:
                    return obj

            payloadData = truncate_json(json_data)
    if payloadType == 'html':                 
        if len(html_data) > limit:
            payloadData = html_data[:limit] + " <h1>(text was truncated)</h1>"
        else:
            payloadData = html_data
    if payloadType == 'text':            
        if len(text_data) > limit:
            payloadData = text_data[:limit] + " (text was truncated)"
        else:
            payloadData = text_data

    # Define slack-compatible payload
    _json_payload = { "text": payloadData } if payloadType == 'text' else {
    "username": "Pi.Alert",
    "text": "There are new notifications",
    "attachments": [{
      "title": "Pi.Alert Notifications",
      "title_link": get_setting_value('REPORT_DASHBOARD_URL'),
      "text": payloadData
    }]
    }

    # DEBUG - Write the json payload into a log file for debugging
    write_file (logPath + '/webhook_payload.json', json.dumps(_json_payload))

    # Using the Slack-Compatible Webhook endpoint for Discord so that the same payload can be used for both
    #  Consider: curl has the ability to load in data to POST from a file + piping
    if(endpointUrl.startswith('https://discord.com/api/webhooks/') and not endpointUrl.endswith("/slack")):
        _WEBHOOK_URL = f"{endpointUrl}/slack"
        curlParams = ["curl","-i","-H", "Content-Type:application/json" ,"-d", json.dumps(_json_payload), _WEBHOOK_URL]
    else:
        _WEBHOOK_URL = endpointUrl
        curlParams = ["curl","-i","-X", requestMethod , "-H", "Content-Type:application/json", "-d", json.dumps(_json_payload), _WEBHOOK_URL]

    # Add HMAC signature if configured
    if(secret != ''):
        h = hmac.new(secret.encode("UTF-8"), json.dumps(_json_payload, separators=(',', ':')).encode(), hashlib.sha256).hexdigest()
        curlParams.insert(4,"-H")
        curlParams.insert(5,f"X-Webhook-Signature: sha256={h}")

    try:
        # Execute CURL call
        mylog('debug', [f'[{pluginName}] curlParams: ', curlParams])
        result = subprocess.run(curlParams, capture_output=True, text=True)

        response_stderr = result.stderr
        response_stdout = result.stdout    

        # Write stdout and stderr into .log files for debugging if needed
        mylog('debug', [f'[{pluginName}] stdout: ', response_stdout])
        mylog('debug', [f'[{pluginName}] stderr: ', response_stderr])   



    except subprocess.CalledProcessError as e:
        # An error occurred, handle it
        mylog('none', [f'[{pluginName}] ⚠ ERROR: ', e.output])

        response_stderr = e.output


    return response_stdout, response_stderr   

#  -------------------------------------------------------
if __name__ == '__main__':
    sys.exit(main())

