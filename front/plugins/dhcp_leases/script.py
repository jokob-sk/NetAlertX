#!/usr/bin/env python

from __future__ import unicode_literals
import pathlib
import subprocess
import argparse
import os
import sys

sys.path.append("/home/pi/pialert/front/plugins")
sys.path.append('/home/pi/pialert/pialert') 

from plugin_helper import Plugin_Object, Plugin_Objects
from logger import mylog
from dhcp_leases import DhcpLeases

CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
LOG_FILE = os.path.join(CUR_PATH, 'script.log')
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

def main():    
    mylog('verbose', ['[DHCPLSS] In script'])
    last_run_logfile = open(RESULT_FILE, 'a') 
    last_run_logfile.write("")

    parser = argparse.ArgumentParser(description='Import devices from dhcp.leases files')
    parser.add_argument('paths',  action="store",  help="absolute dhcp.leases file paths to check separated by ','")  
    values = parser.parse_args()

    plugin_objects = Plugin_Objects(RESULT_FILE)

    if values.paths:
        for path in values.paths.split('=')[1].split(','): 
            plugin_objects = get_entries(path, plugin_objects)
            mylog('verbose', [f'[DHCPLSS] {len(plugin_objects)} Entries found in "{path}"'])        
            
    plugin_objects.write_result_file()

def get_entries(path, plugin_objects):
    if 'pihole' in path:
        
        
        with open(path, 'r') as f:
            for line in f:                
                row = line.rstrip().split()
                if len(row) == 5:
                    plugin_objects.add_object(
                        primaryId=row[1],    
                        secondaryId=row[2],  
                        watched1='True',   
                        watched2=row[3],
                        watched3=row[4],
                        watched4='True',
                        extra=path,
                        foreignKey=row[1]
                    )
    else:
        leases = DhcpLeases(path)
        leasesList = leases.get()
        for lease in leasesList:
            plugin_objects.add_object(
                primaryId=lease.ethernet,    
                secondaryId=lease.ip,  
                watched1=lease.active,   
                watched2=lease.hostname,
                watched3=lease.hardware,
                watched4=lease.binding_state,
                extra=path,
                foreignKey=lease.ethernet
            )
    return plugin_objects

if __name__ == '__main__':    
    main()  
