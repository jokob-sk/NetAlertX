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

sys.path.append("/home/pi/pialert/front/plugins")
sys.path.append('/home/pi/pialert/pialert') 

from plugin_helper import Plugin_Object, Plugin_Objects
from logger import mylog, append_line_to_file
from helper import timeNowTZ
from const import logPath, pialertPath

CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
LOG_FILE = os.path.join(CUR_PATH, 'script.log')
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')


def main():    

    mylog('verbose',['[DHCPLSS] In script'])

    last_run_logfile = open(RESULT_FILE, 'a') 

    # empty file
    last_run_logfile.write("")

    parser = argparse.ArgumentParser(description='Import devices from dhcp.leases files')
    parser.add_argument('paths',  action="store",  help="absolute dhcp.leases file paths to check separated by ','")  
    values = parser.parse_args()


    #  Init the file
    plug_objects = Plugin_Objects( RESULT_FILE )

    # parse output   

    if values.paths:
        for path in values.paths.split('=')[1].split(','): 

            plug_objects_tmp =  get_entries(path, plug_objects) 

            mylog('verbose',[f'[DHCPLSS] {len(plug_objects_tmp)} Entries found in "{path}"'])        

            plug_objects =  plug_objects + plug_objects_tmp

    plug_objects.write_result_file()


# -----------------------------------------------------------------------------
def get_entries(path, plug_objects):

    #  PiHole dhcp.leases format
    if 'pihole' in path:
        data = []
        reporting = False
        with open(piholeDhcpleases, 'r') as f:
            for line in f:                
                
                row = line.rstrip().split()
                # rows: DHCP_DateTime, DHCP_MAC, DHCP_IP, DHCP_Name, DHCP_MAC2
                if len(row) == 5 :
                    plug_objects.add_object(
                                primaryId   =   row[1],    
                                secondaryId =   row[2],  
                                watched1    =   'True',   
                                watched2    =   row[3],
                                watched3    =   row[4],
                                watched4    =   'True',
                                extra       =   path,
                                foreignKey  =   row[1]
                            )
                    

    #  Generic dhcp.leases format
    else:
        leases = DhcpLeases(path)
        leasesList = leases.get()

        for lease in leasesList:
            plug_objects.add_object(
                primaryId   =   lease.ethernet,    
                secondaryId =   lease.ip,  
                watched1    =   lease.active,   
                watched2    =   lease.hostname,
                watched3    =   lease.hardware,
                watched4    =   lease.binding_state,
                extra       =   path,
                foreignKey  =   lease.ethernet
            )

    return plug_objects


#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':    
    main()  

