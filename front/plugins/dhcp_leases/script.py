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
from dhcp_leases import DhcpLeases

curPath = str(pathlib.Path(__file__).parent.resolve())
log_file = curPath + '/script.log'
last_run = curPath + '/last_result.log'

print(last_run)

# Workflow

def main():    

    last_run_logfile = open(last_run, 'a') 

    # empty file
    last_run_logfile.write("")

    parser = argparse.ArgumentParser(description='Import devices from dhcp.leases files')
    parser.add_argument('paths',  action="store",  help="absolute dhcp.leases file paths to check separated by ','")  
    values = parser.parse_args()

    # parse output
    newEntries = []

    if values.paths:
        for path in values.paths.split('=')[1].split(','):           

            newEntries = get_entries(newEntries, path)  

   
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
# -----------------------------------------------------------------------------
def get_entries(newEntries, path):

    #  PiHole dhcp.leases format
    if 'pihole' in path:
        data = []
        reporting = False
        with open(piholeDhcpleases, 'r') as f:
            for line in f:                
                
                row = line.rstrip().split()
                # rows: DHCP_DateTime, DHCP_MAC, DHCP_IP, DHCP_Name, DHCP_MAC2
                if len(row) == 5 :
                    tmpPlugObj = plugin_object_class(row[1], row[2], 'True', row[3], row[4], 'True', path)
                    newEntries.append(tmpPlugObj) 

    #  Generic dhcp.leases format
    else:
        leases = DhcpLeases(path)
        leasesList = leases.get()

        for lease in leasesList:

            tmpPlugObj = plugin_object_class(lease.ethernet, lease.ip, lease.active, lease.hostname, lease.hardware, lease.binding_state, path)
            newEntries.append(tmpPlugObj) 

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

#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':    
    main()  

