
import requests


import conf
from helper import  noti_struc
from logger import mylog

#-------------------------------------------------------------------------------
def check_config():
        if conf.PUSHSAFER_TOKEN == 'ApiKey':
            mylog('none', ['[Check Config] Error: Pushsafer service not set up correctly. Check your pialert.conf PUSHSAFER_TOKEN variable.'])
            return False
        else:
            return True

#-------------------------------------------------------------------------------
def send ( msg:noti_struc ):
    _Text = msg.text
    url = 'https://www.pushsafer.com/api'
    post_fields = {
        "t" : 'Pi.Alert Message',
        "m" : _Text,
        "s" : 11,
        "v" : 3,
        "i" : 148,
        "c" : '#ef7f7f',
        "d" : 'a',
        "u" : conf.REPORT_DASHBOARD_URL,
        "ut" : 'Open Pi.Alert',
        "k" : conf.PUSHSAFER_TOKEN,
        }
    requests.post(url, data=post_fields)