#!/usr/bin/env python
# test script by running:
# /home/pi/pialert/front/plugins/db_cleanup/script.py pluginskeephistory=250 hourstokeepnewdevice=48 daystokeepevents=90

import os
import pathlib
import argparse
import sys
import hashlib
import subprocess
import csv
import sqlite3
from io import StringIO
from datetime import datetime

sys.path.append("/home/pi/pialert/front/plugins")
sys.path.append('/home/pi/pialert/pialert') 

from plugin_helper import Plugin_Object, Plugin_Objects, decodeBase64, handleEmpty
from logger import mylog, append_line_to_file
from helper import timeNowTZ
from const import logPath, pialertPath, fullDbPath
from device import query_MAC_vendor


CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
LOG_FILE = os.path.join(CUR_PATH, 'script.log')
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

def main():   

    mylog('verbose', ['[VNDRPDT] In script']) 

    # Get newest DB   
    update_vendor_database() 

    # Resolve missing vendors
    plugin_objects = Plugin_Objects(RESULT_FILE)

    plugin_objects = update_vendors(fullDbPath, plugin_objects)

    plugin_objects.write_result_file()
    
    mylog('verbose', ['[VNDRPDT] Update complete'])   
    
    return 0

#===============================================================================
# Update device vendors database
#===============================================================================
def update_vendor_database():

    # Update vendors DB (iab oui)
    mylog('verbose', ['    Updating vendors DB (iab & oui)'])    
    update_args = ['sh', pialertPath + '/back/update_vendors.sh']

    # Execute command     
    try:
        # try runnning a subprocess safely
        update_output = subprocess.check_output (update_args)
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        mylog('none', ['    FAILED: Updating vendors DB, set LOG_LEVEL=debug for more info'])  
        mylog('none', [e.output])        

# ------------------------------------------------------------------------------
# resolve missing vendors
def update_vendors (dbPath, plugin_objects): 
   
    # Connect to the PiAlert SQLite database
    conn = sqlite3.connect(dbPath)
    sql  = conn.cursor()

    # Initialize variables
    recordsToUpdate = []
    ignored = 0
    notFound = 0

    
    mylog('verbose', ['    Searching devices vendor']) 

    # Get devices without a vendor
    sql.execute  ("""SELECT 
                            dev_MAC, 
                            dev_LastIP, 
                            dev_Name, 
                            dev_Vendor 
                            FROM Devices
                            WHERE   dev_Vendor      = '(unknown)' 
                                    OR dev_Vendor   = ''
                                    OR dev_Vendor   IS NULL
                        """)
    devices = sql.fetchall() 
    conn.commit()    

    # Close the database connection
    conn.close()  

    # All devices loop
    for device in devices:
        # Search vendor in HW Vendors DB
        vendor = query_MAC_vendor (device[0])
        if vendor == -1 :
            notFound += 1
        elif vendor == -2 :
            ignored += 1
        else :
            plugin_objects.add_object(
                primaryId   = handleEmpty(device[0]),    # MAC (Device Name)
                secondaryId = handleEmpty(device[1]),    # IP Address (always 0.0.0.0)
                watched1    = handleEmpty(vendor),  
                watched2    = handleEmpty(device[2]),    # Device name
                watched3    = "",
                watched4    = "",
                extra       = "",            
                foreignKey  = handleEmpty(device[0])           
            )            
            
    # Print log    
    mylog('verbose', ["    Devices Ignored             : ", ignored])
    mylog('verbose', ["    Devices with missing vendor : ", len(devices)])
    mylog('verbose', ["    Vendors Not Found           : ", notFound])
    mylog('verbose', ["    Vendors updated             : ", len(plugin_objects) ])


    return plugin_objects

    

#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    main()