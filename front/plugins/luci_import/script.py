#!/usr/bin/env python
import os
import sys


INSTALL_PATH = os.getenv('NETALERTX_APP', '/app')
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])
pluginName = 'LUCIRPC'

from plugin_helper import Plugin_Objects
from logger import mylog, Logger
from helper import get_setting_value 
from const import logPath
import conf
from pytz import timezone

try:
    from openwrt_luci_rpc import OpenWrtRpc
except:
    mylog('error', [f'[{pluginName}] Failed import openwrt_luci_rpc']) 
    exit()

conf.tz = timezone(get_setting_value('TIMEZONE'))

Logger(get_setting_value('LOG_LEVEL'))

LOG_PATH = logPath + '/plugins'
LOG_FILE = os.path.join(LOG_PATH, f'script.{pluginName}.log')
RESULT_FILE = os.path.join(LOG_PATH, f'last_result.{pluginName}.log')

plugin_objects = Plugin_Objects(RESULT_FILE)

def main(): 
    mylog('verbose', [f'[{pluginName}] start script.']) 

    device_data = get_device_data()

    for entry in device_data:
        mylog('verbose', [f'[{pluginName}] found: ', str(entry.mac).lower()])  

        name = str(entry.hostname)

        if name.lower() == 'none':
            name = '(unknown)'

        plugin_objects.add_object(
            primaryId   = str(entry.mac).lower(),
            secondaryId = entry.ip, 
            watched1    = entry.host,
            watched2    = name,
            watched3    = "",          
            watched4    = "",
            extra       = pluginName, 
            foreignKey  = str(entry.mac).lower())

    plugin_objects.write_result_file()

    mylog('verbose', [f'[{pluginName}] Script finished'])   
    
    return 0

def get_device_data():
    router = OpenWrtRpc(
        get_setting_value("LUCIRPC_host"),
        get_setting_value("LUCIRPC_user"), 
        get_setting_value("LUCIRPC_password"), 
        get_setting_value("LUCIRPC_ssl"), 
        get_setting_value("LUCIRPC_verify_ssl")
        )

    if router.is_logged_in():
        mylog('verbose', [f'[{pluginName}] login successfully.']) 
    else:
        mylog('error', [f'[{pluginName}] login fail.']) 
    
    device_data = router.get_all_connected_devices(only_reachable=get_setting_value("LUCIRPC_only_reachable"))
    return device_data

if __name__ == '__main__':
    main()