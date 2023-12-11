#!/usr/bin/env python

from __future__ import unicode_literals
import pathlib
import subprocess
import argparse
import os
import sys
import chardet  

sys.path.append("/home/pi/pialert/front/plugins")
sys.path.append('/home/pi/pialert/pialert') 

from plugin_helper import Plugin_Object, Plugin_Objects, handleEmpty, is_mac
from logger import mylog
from dhcp_leases import DhcpLeases

CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
LOG_FILE = os.path.join(CUR_PATH, 'script.log')
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')


pluginName= 'DHCPLSS'

# -------------------------------------------------------------
def main():    
    mylog('verbose', [f'[{pluginName}] In script'])
    last_run_logfile = open(RESULT_FILE, 'a') 
    last_run_logfile.write("")

    parser = argparse.ArgumentParser(description='Import devices from dhcp.leases files')
    parser.add_argument('paths',  action="store",  help="absolute dhcp.leases file paths to check separated by ','")  
    values = parser.parse_args()

    plugin_objects = Plugin_Objects(RESULT_FILE)

    if values.paths:
        for path in values.paths.split('=')[1].split(','): 
            plugin_objects = get_entries(path, plugin_objects)
            mylog('verbose', [f'[{pluginName}] {len(plugin_objects)} Entries found in "{path}"'])        
            
    plugin_objects.write_result_file()

# -------------------------------------------------------------
def get_entries(path, plugin_objects):

    # Check if the path exists
    if not os.path.exists(path):
        mylog('none', [f'[{pluginName}] ⚠ ERROR: "{path}" does not exist.'])
    else:
        # Detect file encoding
        with open(path, 'rb') as f:
            result = chardet.detect(f.read())

        # Use the detected encoding
        encoding = result['encoding']

        # Handle pihole-specific dhcp.leases files
        if 'pihole' in path:
            with open(path, 'r', encoding=encoding, errors='replace') as f:
                for line in f:
                    row = line.rstrip().split()
                    if len(row) == 5:
                        plugin_objects.add_object(
                            primaryId   = handleEmpty(row[1]),
                            secondaryId = handleEmpty(row[2]),
                            watched1    = handleEmpty('True'),
                            watched2    = handleEmpty(row[3]),
                            watched3    = handleEmpty(row[4]),
                            watched4    = handleEmpty('True'),
                            extra       = handleEmpty(path),
                            foreignKey  = handleEmpty(row[1])
                        )
        else:
            #  Handle generic dhcp.leases files
            leases = DhcpLeases(path)
            leasesList = leases.get()
            for lease in leasesList:

                # filter out irrelevant entries (e.g. from OPNsense dhcp.leases files)
                if is_mac(lease.ethernet):

                    plugin_objects.add_object(
                        primaryId   = handleEmpty(lease.ethernet),    
                        secondaryId = handleEmpty(lease.ip),  
                        watched1    = handleEmpty(lease.active),   
                        watched2    = handleEmpty(lease.hostname),
                        watched3    = handleEmpty(lease.hardware),
                        watched4    = handleEmpty(lease.binding_state),
                        extra       = handleEmpty(path),
                        foreignKey  = handleEmpty(lease.ethernet)
                    )
    return plugin_objects

if __name__ == '__main__':    
    main()  
