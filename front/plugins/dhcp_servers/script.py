#!/usr/bin/env python
# Based on the work of https://github.com/leiweibau/Pi.Alert

import subprocess
from datetime import datetime

import sys

sys.path.append("/home/pi/pialert/front/plugins")
sys.path.append('/home/pi/pialert/pialert') 

from plugin_helper import Plugin_Objects, Plugin_Object
from logger import mylog

def main():

    mylog('verbose', ['[DHCPSRVS] In script'])
    RESULT_FILE = 'last_result.log'
    last_run_logfile = open(RESULT_FILE, 'a') 
    last_run_logfile.write("")
    
    plugin_objects = Plugin_Objects(RESULT_FILE)
    timeoutSec = 10

    nmapArgs = ['sudo', 'nmap', '--script', 'broadcast-dhcp-discover']

    try:
        dhcp_probes = 1
        newLines = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        
        for _ in range(dhcp_probes):
            output = subprocess.check_output(nmapArgs, universal_newlines=True, stderr=subprocess.STDOUT, timeout=timeoutSec)
            newLines += output.split("\n")

        newEntries = []

        for line in newLines:
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
        mylog('none', ['Error in main:', str(e)])

if __name__ == '__main__':
    main()
