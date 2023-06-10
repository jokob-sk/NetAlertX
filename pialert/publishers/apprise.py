
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
def send (msg: noti_struc):
    html = msg.html
    text = msg.text

    #Define Apprise compatible payload (https://github.com/caronc/apprise-api#stateless-solution)
    payload = html

    if conf.APPRISE_PAYLOAD == 'text':
        payload = text

    _json_payload={
    "urls": conf.APPRISE_URL,
    "title": "Pi.Alert Notifications",
    "format": conf.APPRISE_PAYLOAD,
    "body": payload
    }

    try:
        # try runnning a subprocess
        p = subprocess.Popen(["curl","-i","-X", "POST" ,"-H", "Content-Type:application/json" ,"-d", json.dumps(_json_payload), conf.APPRISE_HOST], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = p.communicate()
        # write stdout and stderr into .log files for debugging if needed
        logResult (stdout, stderr)      # TO-DO should be changed to mylog
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        mylog('none', [e.output])