
import json
import subprocess
import conf
from helper import noti_struc
from logger import logResult, mylog

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

    # Define Apprise compatible payload (https://github.com/caronc/apprise-api#stateless-solution)
    payload = html

    if conf.APPRISE_PAYLOAD == 'text':
        payload = text

    _json_payload = {
        "urls": conf.APPRISE_URL,
        "title": "Pi.Alert Notifications",
        "format": conf.APPRISE_PAYLOAD,
        "body": payload
    }

    try:
        # Construct the curl command with input from the JSON payload
        curl_command = [
            "curl", "-i", "-X", "POST", "-H", "Content-Type:application/json",
            conf.APPRISE_HOST
        ]

        # Run the curl command with the JSON payload as input
        completed_process = subprocess.run(
            curl_command, input=json.dumps(_json_payload),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        # Log the stdout and stderr
        logResult(completed_process.stdout, completed_process.stderr)  # TO-DO should be changed to mylog
    except subprocess.CalledProcessError as e:
        # An error occurred, handle it
        mylog('none', [e.output])