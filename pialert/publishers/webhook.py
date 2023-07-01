import json
import subprocess

import conf
from const import logPath
from helper import noti_struc, write_file
from logger import logResult, mylog

#-------------------------------------------------------------------------------
def check_config():
        if conf.WEBHOOK_URL == '':
            mylog('none', ['[Check Config] Error: Webhook service not set up correctly. Check your pialert.conf WEBHOOK_* variables.'])
            return False
        else:
            return True
        
#-------------------------------------------------------------------------------        

def send (msg: noti_struc):

    # limit = 1024 * 1024  # 1MB limit (1024 bytes * 1024 bytes = 1MB)
    limit = conf.WEBHOOK_SIZE

    # use data type based on specified payload type
    if conf.WEBHOOK_PAYLOAD == 'json':
        # In this code, the truncate_json function is used to recursively traverse the JSON object 
        # and remove nodes that exceed the size limit. It checks the size of each node's JSON representation 
        # using json.dumps and includes only the nodes that are within the limit.
        json_data = msg.json
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
    if conf.WEBHOOK_PAYLOAD == 'html':                 
        if len(msg.html) > limit:
            payloadData = msg.html[:limit] + " <h1> (text was truncated)</h1>"
        else:
            payloadData = msg.html
    if conf.WEBHOOK_PAYLOAD == 'text':            
        if len(msg.text) > limit:
            payloadData = msg.text[:limit] + " (text was truncated)"
        else:
            payloadData = msg.text

    # Define slack-compatible payload
    _json_payload = { "text": payloadData } if conf.WEBHOOK_PAYLOAD == 'text' else {
    "username": "Pi.Alert",
    "text": "There are new notifications",
    "attachments": [{
      "title": "Pi.Alert Notifications",
      "title_link": conf.REPORT_DASHBOARD_URL,
      "text": payloadData
    }]
    }

    # DEBUG - Write the json payload into a log file for debugging
    write_file (logPath + '/webhook_payload.json', json.dumps(_json_payload))

    # Using the Slack-Compatible Webhook endpoint for Discord so that the same payload can be used for both
    #  Consider: curl has the ability to load in data to POST from a file + piping
    if(conf.WEBHOOK_URL.startswith('https://discord.com/api/webhooks/') and not conf.WEBHOOK_URL.endswith("/slack")):
        _WEBHOOK_URL = f"{conf.WEBHOOK_URL}/slack"
        curlParams = ["curl","-i","-H", "Content-Type:application/json" ,"-d", json.dumps(_json_payload), _WEBHOOK_URL]
    else:
        _WEBHOOK_URL = conf.WEBHOOK_URL
        curlParams = ["curl","-i","-X", conf.WEBHOOK_REQUEST_METHOD ,"-H", "Content-Type:application/json" ,"-d", json.dumps(_json_payload), _WEBHOOK_URL]

    try:
        # Execute CURL call
        mylog('debug', ['[send_webhook] curlParams: ', curlParams])
        result = subprocess.run(curlParams, capture_output=True, text=True)

        stdout = result.stdout
        stderr = result.stderr

        # Write stdout and stderr into .log files for debugging if needed
        mylog('debug', ['[send_webhook] stdout: ', stdout])
        mylog('debug', ['[send_webhook] stderr: ', stderr])
        # logResult(stdout, stderr)  # TO-DO should be changed to mylog

    except subprocess.CalledProcessError as e:
        # An error occurred, handle it
        mylog('none', ['[send_webhook] Error: ', e.output])

