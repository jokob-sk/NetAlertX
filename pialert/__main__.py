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
from helper import  filePermissions, timeNowTZ, updateState, get_setting_value
from api import update_api
from networkscan import process_scan
from initialise import importConfigs
from database import DB
from reporting import get_notifications
from notification import Notification_obj
from plugin import run_plugin_scripts, check_and_run_user_event 


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
        processing scan results
        run plugins (after Scan)
        reporting - could be replaced by run flows TODO
    end loop
"""

def main ():
    mylog('none', ['[MAIN] Setting up ...']) # has to be level 'none' as user config not loaded yet

    mylog('none', [f'[conf.tz] Setting up ...{conf.tz}'])
    
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

    # Header + init app state
    updateState("Initializing")    

    while True:

        # re-load user configuration and plugins   
        importConfigs(db)

        # update time started
        conf.loop_start_time = timeNowTZ()       
        
        loop_start_time = conf.loop_start_time # TODO fix                      

        # Handle plugins executed ONCE
        if conf.plugins_once_run == False:
            pluginsState = run_plugin_scripts(db, 'once')  
            conf.plugins_once_run = True

        # check if there is a front end initiated event which needs to be executed
        pluginsState = check_and_run_user_event(db, pluginsState)

        # Update API endpoints              
        update_api(db)
        
        # proceed if 1 minute passed
        if conf.last_scan_run + datetime.timedelta(minutes=1) < conf.loop_start_time :

             # last time any scan or maintenance/upkeep was run
            conf.last_scan_run = loop_start_time            

            # Header
            updateState("Process: Start")      

            # Timestamp
            startTime = loop_start_time
            startTime = startTime.replace (microsecond=0) 

            # Check if any plugins need to run on schedule
            pluginsState = run_plugin_scripts(db,'schedule', pluginsState) 

            # determine run/scan type based on passed time
            # --------------------------------------------
           
            # Runs plugin scripts which are set to run every timne after a scans finished            
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

            # Notification handling
            # ----------------------------------------

            # send all configured notifications
            final_json = get_notifications(db)

            # Write the notifications into the DB
            notification    = Notification_obj(db)
            notificationObj = notification.create(final_json, "")

            # run all enabled publisher gateways 
            if notificationObj.HasNotifications:
                pluginsState = run_plugin_scripts(db, 'on_notification', pluginsState) 
                notification.setAllProcessed()
                notification.clearPendingEmailFlag()

                
            else:
                mylog('verbose', ['[Notification] No changes to report'])

            # Commit SQL
            db.commitDB()          
            
            # Footer
            updateState("Process: Wait")
            mylog('verbose', ['[MAIN] Process: Wait'])            
        else:
            # do something            
            mylog('verbose', ['[MAIN] waiting to start next loop'])

        #loop     
        time.sleep(5) # wait for N seconds      








#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    mylog('debug', ['[__main__] Welcome to Pi.Alert'])
    sys.exit(main())       
