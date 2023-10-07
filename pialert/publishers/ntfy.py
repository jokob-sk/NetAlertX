
import conf
import requests
from base64 import b64encode

from logger import mylog
from helper import noti_obj

#-------------------------------------------------------------------------------
def check_config():
    if conf.NTFY_HOST == '' or conf.NTFY_TOPIC == '':
        mylog('none', ['[Check Config] Error: NTFY service not set up correctly. Check your pialert.conf NTFY_* variables.'])
        return False
    else:
        return True
    
#-------------------------------------------------------------------------------
def send  (msg: noti_obj):

    headers = {
        "Title": "Pi.Alert Notification",
        "Actions": "view, Open Dashboard, "+ conf.REPORT_DASHBOARD_URL,
        "Priority": "urgent",
        "Tags": "warning"
    }
    # if username and password are set generate hash and update header
    if conf.NTFY_USER != "" and conf.NTFY_PASSWORD != "":
	# Generate hash for basic auth
        # usernamepassword = "{}:{}".format(conf.NTFY_USER,conf.NTFY_PASSWORD)
        basichash = b64encode(bytes(conf.NTFY_USER + ':' + conf.NTFY_PASSWORD, "utf-8")).decode("ascii")

	# add authorization header with hash
        headers["Authorization"] = "Basic {}".format(basichash)

    try:
        requests.post("{}/{}".format( conf.NTFY_HOST, conf.NTFY_TOPIC),
                                        data=msg.text,
                                        headers=headers)
    except requests.exceptions.RequestException as e:  
        mylog('none', ['[NTFY] Error: ', e])
        return -1

    return 0    
