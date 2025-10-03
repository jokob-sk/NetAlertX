#!/usr/bin/env python
# Based on the work of https://github.com/leiweibau/Pi.Alert

import subprocess
import os
from datetime import datetime

import sys

# Register NetAlertX directories
INSTALL_PATH="/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from plugin_helper import Plugin_Objects, Plugin_Object
from logger import mylog, Logger
from helper import timeNowTZ, get_setting_value 
import conf
from pytz import timezone
from const import logPath


# Make sure the TIMEZONE for logging is correct
conf.tz = timezone(get_setting_value('TIMEZONE'))

# Make sure log level is initialized correctly
Logger(get_setting_value('LOG_LEVEL'))

pluginName = 'DHCPSRVS'

LOG_PATH = logPath + '/plugins'
LOG_FILE = os.path.join(LOG_PATH, f'script.{pluginName}.log')
RESULT_FILE = os.path.join(LOG_PATH, f'last_result.{pluginName}.log')

def main():

    mylog('verbose', ['[DHCPSRVS] In script'])
    
    last_run_logfile = open(RESULT_FILE, 'a') 
    last_run_logfile.write("")
    
    plugin_objects = Plugin_Objects(RESULT_FILE)
    timeoutSec = get_setting_value('DHCPSRVS_RUN_TIMEOUT')

    nmapArgs = ['sudo', 'nmap', '--privileged', '--script', 'broadcast-dhcp-discover']

    try:
        dhcp_probes = 1
        newLines = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        
        for _ in range(dhcp_probes):
            output = subprocess.check_output(nmapArgs, universal_newlines=True, stderr=subprocess.STDOUT, timeout=timeoutSec)
            newLines += output.split("\n")

        newEntries = []

        for line in newLines:
            
            mylog('verbose', [f'[DHCPSRVS] Processing line: {line} '])
            
            if 'Response ' in line and ' of ' in line:
                newEntries.append(Plugin_Object())
            elif 'Server Identifier' in line:
                newEntries[-1].primaryId = line.split(':')[1].strip()
            elif 'Domain Name' in line:
                newEntries[-1].secondaryId = line.split(':')[1].strip()
            elif 'Domain Name Server' in line:
                newEntries[-1].watched1 = line.split(':')[1].strip()
            elif 'IP Offered' in line:
                newEntries[-1].watched2 = line.split(':')[1].strip()
            elif 'Interface' in line:
                newEntries[-1].watched3 = line.split(':')[1].strip()
            elif 'Router' in line:
                value = line.split(':')[1].strip()
                newEntries[-1].watched4 = value
                newEntries[-1].foreignKey = value

            if 'IP Address Lease Time' in line or 'Subnet Mask' in line or 'Broadcast Address' in line:
                newVal = line.split(':')[1].strip()
                if newEntries[-1].extra == '':
                    newEntries[-1].extra = newVal
                else:
                    newEntries[-1].extra += ',' + newVal

        for e in newEntries:
            
            plugin_objects.add_object(
                primaryId=e.primaryId,
                secondaryId=e.secondaryId,
                watched1=e.watched1,
                watched2=e.watched2,
                watched3=e.watched3,
                watched4=e.watched4,
                extra=e.extra,
                foreignKey=e.foreignKey
            )

        plugin_objects.write_result_file()
    except Exception as e:
        mylog('verbose', ['[DHCPSRVS] Error in main:', str(e)])

if __name__ == '__main__':
    main()
