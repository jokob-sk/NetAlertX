#!/usr/bin/env python
# Based on the work of https://github.com/leiweibau/Pi.Alert

from __future__ import unicode_literals
from time import sleep, time, strftime
import requests
import pathlib
import threading
import subprocess
import socket
import argparse
import io
import sys
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import pwd
import os

curPath = str(pathlib.Path(__file__).parent.resolve())
log_file = curPath + '/script.log'
last_run = curPath + '/last_result.log'

print(last_run)

# Workflow

def main():    

    last_run_logfile = open(last_run, 'a') 

    timeoutSec = 10

    nmapArgs = ['sudo', 'nmap', '--script', 'broadcast-dhcp-discover']

    # Execute N probes and insert in list
    dhcp_probes = 1 #  N probes
    newLines = []
    newLines.append(strftime("%Y-%m-%d %H:%M:%S"))
    #dhcp_server_list_time = []
    for _ in range(dhcp_probes):
        output = subprocess.check_output (nmapArgs, universal_newlines=True,  stderr=subprocess.STDOUT, timeout=(timeoutSec ))
        newLines = newLines + output.split("\n")

    # parse output
    newEntries = []
    
    duration = "" 
    for line in newLines:  
        
        if newEntries is None:
            index = 0
        else:    
            index = len(newEntries) - 1 

        if 'Response ' in line and ' of ' in line:            
            newEntries.append(plugin_object_class())                        
        elif 'Server Identifier' in line :
            newEntries[index].primaryId = line.split(':')[1].strip()   
        elif 'Domain Name' in line :
            newEntries[index].secondaryId = line.split(':')[1].strip()
        elif 'Domain Name Server' in line :
            newEntries[index].watched1 = line.split(':')[1].strip()
        elif 'IP Offered' in line :
            newEntries[index].watched2 = line.split(':')[1].strip()
        elif 'Interface' in line :
            newEntries[index].watched3 = line.split(':')[1].strip()
        elif 'Router' in line :
            newEntries[index].watched4   = line.split(':')[1].strip()
            newEntries[index].foreignKey = line.split(':')[1].strip()
        elif ('IP Address Lease Time' in line or 'Subnet Mask' in line or 'Broadcast Address' in line) :
            newEntries[index].extra  = newEntries[index].extra + ',' + line.split(':')[1].strip()    

    for e in newEntries:        
        # Insert list into the log            
        service_monitoring_log(e.primaryId, e.secondaryId, e.created, e.watched1, e.watched2, e.watched3, e.watched4, e.extra, e.foreignKey )

# -----------------------------------------------------------------------------
def service_monitoring_log(primaryId, secondaryId, created, watched1, watched2 = '', watched3 = '', watched4 = '', extra ='', foreignKey =''  ):
    
    if watched1 == '':
        watched1 = 'null'
    if watched2 == '':
        watched2 = 'null'
    if watched3 == '':
        watched3 = 'null'
    if watched4 == '':
        watched4 = 'null'

    with open(last_run, 'a') as last_run_logfile:
        # https://www.duckduckgo.com|192.168.0.1|2023-01-02 15:56:30|200|0.9898|null|null|Best search engine|null
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

#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    sys.exit(main())       

