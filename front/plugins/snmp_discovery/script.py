#!/usr/bin/env python

from __future__ import unicode_literals
import pathlib
import subprocess
import argparse
import os
import sys

# Register NetAlertX directories
INSTALL_PATH="/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from plugin_helper import Plugin_Object, Plugin_Objects, decodeBase64, handleEmpty, normalize_mac
from logger import mylog
from helper import timeNowTZ
from const import logPath, applicationPath

CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

# Workflow

def main():    
    mylog('verbose', ['[SNMPDSC] In script ']) 

    # init global variables
    global snmpWalkCmds

    
    parser = argparse.ArgumentParser(description='This plugin is used to discover devices via the arp table(s) of a RFC1213 compliant router or switch.')    
    parser.add_argument('routers',  action="store",  help="IP(s) of routers, separated by comma (,) if passing multiple")                        
    values = parser.parse_args()

    plugin_objects = Plugin_Objects(RESULT_FILE)

    if values.routers:        
        snmpWalkCmds = values.routers.split('=')[1].replace('\'','')  
        

        if ',' in snmpWalkCmds:
            commands = snmpWalkCmds.split(',')
        else:
            commands = [snmpWalkCmds]
    
        for cmd in commands:
            mylog('verbose', ['[SNMPDSC] Router snmpwalk command: ', cmd]) 
            timeoutSec = 10
            # split the string, remove white spaces around each item, and exclude any empty strings
            snmpwalkArgs = [arg.strip() for arg in cmd.split(' ') if arg.strip()]


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

                        if len(ipStr) == 4:
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
                        else:
                            mylog('verbose', [f'[SNMPDSC] ipStr does not seem to contain a valid IP:', ipStr]) 


                    elif line.startswith('ipNetToMediaPhysAddress'):
                        # Format: snmpwalk -OXsq output
                        parts = line.split()
                        if len(parts) == 2:

                            ipAddress  = parts[0].split('[')[-1][:-1]
                            macAddress = normalize_mac(parts[1])

                            mylog('verbose', [f'[SNMPDSC] IP: {ipAddress} MAC: {macAddress}'])

                            plugin_objects.add_object(
                                primaryId   = handleEmpty(macAddress),
                                secondaryId = handleEmpty(ipAddress.strip()),
                                watched1    = '(unknown)',
                                watched2    = handleEmpty(snmpwalkArgs[6]),
                                extra       = handleEmpty(line),
                                foreignKey  = handleEmpty(macAddress)
                            )

    mylog('verbose', ['[SNMPDSC] Entries found: ', len(plugin_objects)]) 

    plugin_objects.write_result_file()

    

# BEGIN
if __name__ == '__main__':    
    main()
