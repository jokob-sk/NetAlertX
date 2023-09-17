#!/usr/bin/env python
#
#-------------------------------------------------------------------------------
#  Pi.Alert  v2.70  /  2021-02-01
#  Open Source Network Guard / WIFI & LAN intrusion detector 
#
#  pialert.py - Back module. Network scanner
#-------------------------------------------------------------------------------
#  Puche 2021 / 2022+ jokob             jokob@duck.com                GNU GPLv3
#-------------------------------------------------------------------------------


#===============================================================================
# IMPORTS
#===============================================================================
#from __future__ import print_function

import sys
import time
import datetime
import multiprocessing

# pialert modules
import conf
from const import *
from logger import  mylog
from helper import   filePermissions, isNewVersion,  timeNowTZ, updateState, get_setting_value
from api import update_api
from networkscan import process_scan
from initialise import importConfigs
from database import DB, get_all_devices
from reporting import check_and_run_event, send_notifications
from plugin import run_plugin_scripts 

# different scanners
from scanners.internet import check_internet_IP



#===============================================================================
#===============================================================================
#                              MAIN
#===============================================================================
#===============================================================================
"""
main structure of Pi Alert

    Initialise All
    start Loop forever
        initialise loop 
            (re)import config
            (re)import plugin config
        run plugins (once)
        run frontend events
        update API         
        run plugins (scheduled)
        check internet IP
        check vendor                        
        processing scan results
        run plugins (after Scan)
        reporting        
    end loop
"""

def main ():
    mylog('none', ['[MAIN] Setting up ...']) # has to be level 'none' as user config not loaded yet

    mylog('none', [f'[conf.tz] Setting up ...{conf.tz}'])

    
    # indicates, if a new version is available
    conf.newVersionAvailable = False
    
    # check file permissions and fix if required
    filePermissions()

    # Open DB once and keep open
    # Opening / closing DB frequently actually casues more issues
    db = DB()  # instance of class DB
    db.open()
    sql = db.sql  # To-Do replace with the db class

    # Upgrade DB if needed
    db.upgradeDB()

    #===============================================================================
    # This is the main loop of Pi.Alert 
    #===============================================================================

    mylog('debug', '[MAIN] Starting loop')

    while True:

        # re-load user configuration and plugins   
        importConfigs(db)

        # update time started
        conf.loop_start_time = timeNowTZ()
        
        # TODO fix these
        loop_start_time = conf.loop_start_time # TODO fix
        last_update_vendors = conf.last_update_vendors                
        last_version_check = conf.last_version_check        
        
        # check if new version is available / only check once an hour
        if conf.last_version_check  + datetime.timedelta(hours=1) < conf.loop_start_time :
            # if newVersionAvailable is already true the function does nothing and returns true again
            mylog('debug', [f"[Version check] Last version check timestamp: {conf.last_version_check}"])
            conf.last_version_check = conf.loop_start_time
            conf.newVersionAvailable = isNewVersion(conf.newVersionAvailable)

        # Handle plugins executed ONCE
        if conf.plugins_once_run == False:
            pluginsState = run_plugin_scripts(db, 'once')  
            conf.plugins_once_run = True

        # check if there is a front end initiated event which needs to be executed
        pluginsState = check_and_run_event(db, pluginsState)

        # Update API endpoints              
        update_api(db)
        
        # proceed if 1 minute passed
        if conf.last_scan_run + datetime.timedelta(minutes=1) < conf.loop_start_time :

             # last time any scan or maintenance/upkeep was run
            conf.last_scan_run = loop_start_time
            last_internet_IP_scan = conf.last_internet_IP_scan

            # Header
            updateState("Process: Start")      

            # Timestamp
            startTime = loop_start_time
            startTime = startTime.replace (microsecond=0) 

            # Check if any plugins need to run on schedule
            pluginsState = run_plugin_scripts(db,'schedule', pluginsState) 

            # determine run/scan type based on passed time
            # --------------------------------------------

            # check for changes in Internet IP
            if last_internet_IP_scan + datetime.timedelta(minutes=3) < loop_start_time:
                conf.cycle = 'internet_IP'                
                last_internet_IP_scan = loop_start_time
                check_internet_IP(db)
           
            # Run splugin scripts which are set to run every timne after a scans finished            
            pluginsState = run_plugin_scripts(db,'always_after_scan', pluginsState)

            
            # process all the scanned data into new devices
            mylog('debug', [f'[MAIN] processScan: {pluginsState.processScan}'])
            
            if pluginsState.processScan == True:   
                mylog('debug', "[MAIN] start processig scan results")  
                pluginsState.processScan = False
                process_scan(db)
                          
            
            # Reporting   
            # Check if new devices found
            sql.execute (sql_new_devices)
            newDevices = sql.fetchall()
            db.commitDB()
            
            #  new devices were found
            if len(newDevices) > 0:
                #  run all plugins registered to be run when new devices are found                    
                pluginsState = run_plugin_scripts(db, 'on_new_device', pluginsState)                

            # send all configured notifications
            send_notifications(db)

            # Commit SQL
            db.commitDB()          
            
            # Footer
            updateState("Process: Wait")
            mylog('verbose', ['[MAIN] Process: Wait'])            
        else:
            # do something
            conf.cycle = "" 
            mylog('verbose', ['[MAIN] waiting to start next loop'])

        #loop     
        time.sleep(5) # wait for N seconds      








#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    mylog('debug', ['[__main__] Welcome to Pi.Alert'])
    sys.exit(main())       
