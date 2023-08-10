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
from helper import   filePermissions, isNewVersion,  timeNowTZ, updateState
from api import update_api
from networkscan import process_scan
from initialise import importConfigs
from mac_vendor import update_devices_MAC_vendors
from database import DB, get_all_devices
from reporting import check_and_run_event, send_notifications
from plugin import run_plugin_scripts 

# different scanners
from scanners.pholusscan import performPholusScan
from scanners.nmapscan import performNmapScan
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
        run scans
            run plugins (scheduled)
            check internet IP
            check vendor
            run PHOLUS
            run NMAP
            run "scan_network()"
                processing scan results
            run plugins (after Scan)
        reporting
        cleanup
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
        last_cleanup = conf.last_cleanup
        last_version_check = conf.last_version_check
        

        # check if new version is available / only check once an hour
        if conf.last_version_check  + datetime.timedelta(hours=1) < loop_start_time :
            # if newVersionAvailable is already true the function does nothing and returns true again
            mylog('debug', [f"[Version check] Last version check timestamp: {conf.last_version_check}"])
            conf.last_version_check = loop_start_time
            conf.newVersionAvailable = isNewVersion(conf.newVersionAvailable)

        # Handle plugins executed ONCE
        if conf.ENABLE_PLUGINS and conf.plugins_once_run == False:
            run_plugin_scripts(db, 'once')  
            conf.plugins_once_run = True

        # check if there is a front end initiated event which needs to be executed
        check_and_run_event(db)

        # Update API endpoints              
        update_api(db)
        
        # proceed if 1 minute passed
        if conf.last_scan_run + datetime.timedelta(minutes=1) < conf.loop_start_time :

             # last time any scan or maintenance/upkeep was run
            conf.last_scan_run = loop_start_time
            last_internet_IP_scan = conf.last_internet_IP_scan

            # Header
            updateState(db,"Process: Start")      

            # Timestamp
            startTime = loop_start_time
            startTime = startTime.replace (microsecond=0) 

            # Check if any plugins need to run on schedule
            if conf.ENABLE_PLUGINS:
                run_plugin_scripts(db,'schedule') 

            # determine run/scan type based on passed time
            # --------------------------------------------

            # check for changes in Internet IP
            if last_internet_IP_scan + datetime.timedelta(minutes=3) < loop_start_time:
                conf.cycle = 'internet_IP'                
                last_internet_IP_scan = loop_start_time
                check_internet_IP(db)

            # Update vendors once a week
            if last_update_vendors + datetime.timedelta(days = 7) < loop_start_time:
                last_update_vendors = loop_start_time
                conf.cycle = 'update_vendors'
                mylog('verbose', ['[MAIN] cycle:',conf.cycle])                  
                update_devices_MAC_vendors(db)

            # Execute scheduled or one-off Pholus scan if enabled and run conditions fulfilled
            if conf.PHOLUS_RUN == "schedule" or conf.PHOLUS_RUN == "once":

                pholusSchedule = [sch for sch in conf.mySchedules if sch.service == "pholus"][0]
                run = False

                # run once after application starts
                if conf.PHOLUS_RUN == "once" and pholusSchedule.last_run == 0:
                    run = True

                # run if overdue scheduled time
                if conf.PHOLUS_RUN == "schedule":
                    run = pholusSchedule.runScheduleCheck()                    

                if run:
                    pholusSchedule.last_run = datetime.datetime.now(conf.tz).replace(microsecond=0)
                    performPholusScan(db, conf.PHOLUS_RUN_TIMEOUT, conf.userSubnets)
            
            # Execute scheduled or one-off Nmap scan if enabled and run conditions fulfilled
            if conf.NMAP_RUN == "schedule" or conf.NMAP_RUN == "once":

                nmapSchedule = [sch for sch in conf.mySchedules if sch.service == "nmap"][0]
                run = False

                # run once after application starts
                if conf.NMAP_RUN == "once" and nmapSchedule.last_run == 0:
                    run = True

                # run if overdue scheduled time
                if conf.NMAP_RUN == "schedule":
                    run = nmapSchedule.runScheduleCheck()                    

                if run:
                    nmapSchedule.last_run = timeNowTZ()
                    performNmapScan(db, get_all_devices(db))
           
           
            # Run splugin scripts which are set to run every timne after a scans finished
            if conf.ENABLE_PLUGINS:
                run_plugin_scripts(db,'always_after_scan')

            
            # process all the scanned data into new devices
            if conf.currentScanNeedsProcessing == True:   
                mylog('debug', "[MAIN] start processig scan results")             
                process_scan(db)
                conf.currentScanNeedsProcessing = False                
            
            # Reporting   
            if conf.cycle in conf.check_report:
                # Check if new devices found
                sql.execute (sql_new_devices)
                newDevices = sql.fetchall()
                db.commitDB()
                
                #  new devices were found
                if len(newDevices) > 0:
                    #  run all plugins registered to be run when new devices are found
                    if conf.ENABLE_PLUGINS:
                        run_plugin_scripts(db, 'on_new_device')

                    #  Scan newly found devices with Nmap if enabled
                    if conf.NMAP_ACTIVE and len(newDevices) > 0:
                        performNmapScan( db, newDevices)

                # send all configured notifications
                send_notifications(db)

            # clean up the DB once an hour
            if last_cleanup + datetime.timedelta(hours = 1) < loop_start_time:
                last_cleanup = loop_start_time
                conf.cycle = 'cleanup'  
                mylog('verbose', ['[MAIN] cycle:',conf.cycle])
                db.cleanup_database(startTime, conf.DAYS_TO_KEEP_EVENTS, conf.PHOLUS_DAYS_DATA, conf.HRS_TO_KEEP_NEWDEV, conf.PLUGINS_KEEP_HIST)   

            # Commit SQL
            db.commitDB()          
            
            # Final message
            if conf.cycle != "":
                action = str(conf.cycle)
                if action == "1":
                    action = "network_scan"
                mylog('verbose', ['[MAIN] Last action: ', action])
                conf.cycle = ""
                mylog('verbose', ['[MAIN] cycle:',conf.cycle])
            
            # Footer
            updateState(db,"Process: Wait")
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
