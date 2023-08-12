
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
    # payload = html

    # if conf.APPRISE_PAYLOAD == 'text':
    #     payload = text

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
        logResult (stdout, stderr)      # TO-DO should be changed to mylog

        # Log the stdout and stderr
        mylog('debug', [stdout, stderr])  # TO-DO should be changed to mylog
    except subprocess.CalledProcessError as e:
        # An error occurred, handle it
        mylog('none', [e.output])