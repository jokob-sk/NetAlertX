#!/usr/bin/env python

# Example call
# python3 /home/pi/pialert/front/plugins/snmp_discovery/script.py routers='snmpwalk -v 2c -c public -OXsq 192.168.1.1 .1.3.6.1.2.1.3.1.1.2'

from __future__ import unicode_literals
import pathlib
import subprocess
import argparse
import os
import sys

sys.path.append("/home/pi/pialert/front/plugins")
sys.path.append('/home/pi/pialert/pialert') 

from plugin_helper import Plugin_Object, Plugin_Objects, decodeBase64, handleEmpty
from logger import mylog
from helper import timeNowTZ
from const import logPath, pialertPath

CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

# Workflow

def main():    
    mylog('verbose', ['[SNMPDSC] In script ']) 

    # init global variables
    global ROUTERS

    
    parser = argparse.ArgumentParser(description='This plugin is used to discover devices via the arp table(s) of a RFC1213 compliant router or switch.')    
    parser.add_argument('routers',  action="store",  help="IP(s) of routers, separated by comma (,) if passing multiple")                        
    values = parser.parse_args()

    plugin_objects = Plugin_Objects(RESULT_FILE)

    if values.routers:        
        ROUTERS = values.routers.split('=')[1].replace('\'','')  
        

        if ',' in ROUTERS:
            routers = ROUTERS.split(',')
        else:
            routers = [ROUTERS]
    
        for router in routers:
            mylog('verbose', ['[SNMPDSC] Router snmpwalk command: ', router]) 
            timeoutSec = 10
            snmpwalkArgs = router.split(' ')

            # Execute N probes and insert in list
            probes = 1  # N probes
                
            for _ in range(probes):
                output = subprocess.check_output (snmpwalkArgs, universal_newlines=True, stderr=subprocess.STDOUT, timeout=(timeoutSec ))

                mylog('verbose', ['[SNMPDSC] output: ', output]) 

                lines = output.split('\n')

                for line in lines: 

                    tmpSplt = line.split('"')   
                    

                    if len(tmpSplt) == 3:
                        
                        ipStr = tmpSplt[0].split('.')[-4:]  # Get the last 4 elements to extract the IP
                        macStr = tmpSplt[1].strip().split(' ')  # Remove leading/trailing spaces from MAC

                        if 'iso.' in output and len(ipStr) == 4:
                            macAddress = ':'.join(macStr)
                            ipAddress = '.'.join(ipStr)

                            mylog('verbose', [f'[SNMPDSC] IP: {ipAddress} MAC: {macAddress}']) 
                            
                            plugin_objects.add_object(
                                primaryId   = handleEmpty(macAddress),
                                secondaryId = handleEmpty(ipAddress.strip()), # Remove leading/trailing spaces from IP
                                watched1    = '(unknown)',
                                watched2    = handleEmpty(snmpwalkArgs[6]),  # router IP
                                extra       = handleEmpty(line),
                                foreignKey  = handleEmpty(macAddress)  # Use the primary ID as the foreign key
                            )

    mylog('verbose', ['[SNMPDSC] Entries found: ', len(plugin_objects)]) 

    plugin_objects.write_result_file()

    

# BEGIN
if __name__ == '__main__':    
    main()
