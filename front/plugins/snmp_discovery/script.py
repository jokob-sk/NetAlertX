#!/usr/bin/env python

# Example call
# python3 /home/pi/pialert/front/plugins/snmp_discovery/script.py routers='snmpwalk -v 2c -c public -OXsq 192.168.1.1 .1.3.6.1.2.1.3.1.1.2'

from __future__ import unicode_literals
from time import sleep, time, strftime
import requests
from requests                               import Request, Session, packages
import pathlib
import threading
import subprocess
import socket
import json
import argparse
import io
import sys
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import pwd
import os

sys.path.append("/home/pi/pialert/front/plugins")
sys.path.append('/home/pi/pialert/pialert') 

from plugin_helper import Plugin_Object, Plugin_Objects, decodeBase64
from logger import mylog, append_line_to_file
from helper import timeNowTZ
from const import logPath, pialertPath

CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
LOG_FILE = os.path.join(CUR_PATH, 'script.log')
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')


# Workflow

def main():    

    mylog('verbose', ['[SNMPDSC] In script ']) 

    # init global variables
    global ROUTERS

    # empty file
    open(RESULT_FILE , 'w').close()   

    last_run_logfile = open(RESULT_FILE, 'a')     

    parser = argparse.ArgumentParser(description='This plugin is used to discover devices via the arp table(s) of a RFC1213 compliant router or switch.')    
    parser.add_argument('routers',  action="store",  help="IP(s) of routers, separated by comma (,) if passing multiple")                        
    values = parser.parse_args()

    # parse output
    newEntries = []

    if values.routers:        

        ROUTERS = values.routers.split('=')[1].replace('\'','')  
        newEntries = get_entries(newEntries)  
   
    mylog('verbose', ['[SNMPDSC] Entries found: ', len(newEntries)]) 

    for e in newEntries:        
        # Insert list into the log      
              
        service_monitoring_log(e.primaryId, e.secondaryId, e.created, e.watched1, e.watched2, e.watched3, e.watched4, e.extra, e.foreignKey )

# -----------------------------------------------------------------------------
def get_entries(newEntries):

    routers = []

    if ',' in ROUTERS:
        # multiple
        routers = ROUTERS.split(',')
    
    else:
        # only one
        routers.append(ROUTERS)

    for router in routers:
        # snmpwalk -v 2c -c public -OXsq 192.168.1.1 .1.3.6.1.2.1.3.1.1.2

        mylog('verbose', ['[SNMPDSC] Router snmpwalk command: ', router]) 

        timeoutSec = 10

        snmpwalkArgs = router.split(' ')

        # Execute N probes and insert in list
        probes = 1 #  N probes
        newLines = []                
        for _ in range(probes):
            output = subprocess.check_output (snmpwalkArgs, universal_newlines=True,  stderr=subprocess.STDOUT, timeout=(timeoutSec ))
            newLines = newLines + output.split("\n")

        # Process outputs
        # Sample: iso.3.6.1.2.1.3.1.1.2.3.1.192.168.1.2 "6C 6C 6C 6C 6C 6C "

        with open(LOG_FILE, 'a') as run_logfile:
            for line in newLines:              
                
                # debug
                run_logfile.write(line)

                tmpSplt = line.split('"')   

                if len(tmpSplt) == 3:
                    ipStr = tmpSplt[0].split('.')[-4:]  # Get the last 4 elements to extract the IP
                    macStr = tmpSplt[1].strip().split(' ')  # Remove leading/trailing spaces from MAC

                    if 'iso.' in line and len(ipStr) == 4:
                        macAddress = ':'.join(macStr)
                        ipAddress = '.'.join(ipStr)

                        tmpEntry = plugin_object_class(
                            macAddress,
                            ipAddress,
                            watched1='(unknown)',
                            watched2=snmpwalkArgs[6],  # router IP
                            extra=line
                        )
                        newEntries.append(tmpEntry)
        
    return newEntries


# -------------------------------------------------------------------
class plugin_object_class:
    def __init__(self, primaryId = '',secondaryId = '', watched1 = '',watched2 = '',watched3 = '',watched4 = '',extra = '',foreignKey = ''):        
        self.pluginPref   = ''
        self.primaryId    = primaryId
        self.secondaryId  = secondaryId
        self.created      = strftime("%Y-%m-%d %H:%M:%S")
        self.changed      = ''
        self.watched1     = watched1
        self.watched2     = watched2
        self.watched3     = watched3
        self.watched4     = watched4
        self.status       = ''
        self.extra        = extra
        self.userData     = ''
        self.foreignKey   = foreignKey

# -----------------------------------------------------------------------------
def service_monitoring_log(primaryId, secondaryId, created, watched1, watched2 = 'null', watched3 = 'null', watched4 = 'null', extra ='null', foreignKey ='null'  ):
    
    if watched1 == '':
        watched1 = 'null'
    if watched2 == '':
        watched2 = 'null'
    if watched3 == '':
        watched3 = 'null'
    if watched4 == '':
        watched4 = 'null'
    if extra == '':
        extra = 'null'
    if foreignKey == '':
        foreignKey = 'null'

    with open(RESULT_FILE, 'a') as last_run_logfile:        
        last_run_logfile.write("{}|{}|{}|{}|{}|{}|{}|{}|{}\n".format(
                                                primaryId,
                                                secondaryId,
                                                created,                                                
                                                watched1,
                                                watched2,
                                                watched3,
                                                watched4,
                                                extra,
                                                foreignKey
                                                )
                             )


#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':    
    main()  

