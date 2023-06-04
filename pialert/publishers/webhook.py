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

    # use data type based on specified payload type
    if conf.WEBHOOK_PAYLOAD == 'json':
        payloadData = msg.json
    if conf.WEBHOOK_PAYLOAD == 'html':
        payloadData = msg.html
    if conf.WEBHOOK_PAYLOAD == 'text':
        payloadData = to_text(msg.json)  # TO DO can we just send msg.text?

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
    if(conf.WEBHOOK_URL.startswith('https://discord.com/api/webhooks/') and not conf.WEBHOOK_URL.endswith("/slack")):
        _WEBHOOK_URL = f"{conf.WEBHOOK_URL}/slack"
        curlParams = ["curl","-i","-H", "Content-Type:application/json" ,"-d", json.dumps(_json_payload), _WEBHOOK_URL]
    else:
        _WEBHOOK_URL = conf.WEBHOOK_URL
        curlParams = ["curl","-i","-X", conf.WEBHOOK_REQUEST_METHOD ,"-H", "Content-Type:application/json" ,"-d", json.dumps(_json_payload), _WEBHOOK_URL]

    # execute CURL call
    try:
        # try runnning a subprocess
        mylog('debug', ['[send_webhook] curlParams: ', curlParams])
        p = subprocess.Popen(curlParams, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        stdout, stderr = p.communicate()

        # write stdout and stderr into .log files for debugging if needed
        logResult (stdout, stderr)     # TO-DO should be changed to mylog
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        mylog('none', ['[send_webhook]', e.output])





#-------------------------------------------------------------------------------
def to_text(_json):
    payloadData = ""
    if len(_json['internet']) > 0 and 'internet' in conf.INCLUDED_SECTIONS:
        payloadData += "INTERNET\n"
        for event in _json['internet']:
            payloadData += event[3] + ' on ' + event[2] + '. ' + event[4] + '. New address:' + event[1] + '\n'

    if len(_json['new_devices']) > 0 and 'new_devices' in conf.INCLUDED_SECTIONS:
        payloadData += "NEW DEVICES:\n"
        for event in _json['new_devices']:
            if event[4] is None:
                event[4] = event[11]
            payloadData += event[1] + ' - ' + event[4] + '\n'

    if len(_json['down_devices']) > 0 and 'down_devices' in conf.INCLUDED_SECTIONS:
        write_file (logPath + '/down_devices_example.log', _json['down_devices'])
        payloadData += 'DOWN DEVICES:\n'
        for event in _json['down_devices']:
            if event[4] is None:
                event[4] = event[11]
            payloadData += event[1] + ' - ' + event[4] + '\n'

    if len(_json['events']) > 0 and 'events' in conf.INCLUDED_SECTIONS:
        payloadData += "EVENTS:\n"
        for event in _json['events']:
            if event[8] != "Internet":
                payloadData += event[8] + " on " + event[1] + " " + event[3] + " at " + event[2] + "\n"

    return payloadData