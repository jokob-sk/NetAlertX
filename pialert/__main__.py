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
from __future__ import print_function

import sys
from collections import namedtuple
import time
import datetime
import multiprocessing

# pialert modules
import conf
from const import *
from logger import  mylog
from helper import   filePermissions, isNewVersion,  timeNow, timeNowTZ, updateState
from api import update_api
from networkscan import process_scan, scan_network
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
                ARP Scan
                PiHole copy db
                PiHole DHCP leases
                processing scan results
            run plugins (after Scan)
        reporting
        cleanup
    end loop
"""

def main ():
    
    conf.time_started = datetime.datetime.now()
    conf.cycle = ""
    conf.check_report = [1, "internet_IP", "update_vendors_silent"]
    conf.plugins_once_run = False
    
    pialert_start_time = timeNow()


    # to be deleted if not used 
    conf.log_timestamp = conf.time_started
    #cron_instance = Cron()

    # timestamps of last execution times
    startTime = conf.time_started
    now_minus_24h = conf.time_started - datetime.timedelta(hours = 24)

    # set these times to the past to force the first run 
    last_network_scan = now_minus_24h
    last_internet_IP_scan = now_minus_24h
    last_scan_run = now_minus_24h
    last_cleanup = now_minus_24h
    last_update_vendors = conf.time_started - datetime.timedelta(days = 6) # update vendors 24h after first run and then once a week
    last_version_check = now_minus_24h  

    # indicates, if a new version is available
    conf.newVersionAvailable = False
    
    # check file permissions and fix if required
    filePermissions()

    # Open DB once and keep open
    # Opening / closing DB frequently actually casues more issues
    db = DB()  # instance of class DB
    db.openDB()
    sql = db.sql  # To-Do replace with the db class

    # Upgrade DB if needed
    db.upgradeDB()


    #===============================================================================
    # This is the main loop of Pi.Alert 
    #===============================================================================

    while True:

        # update time started
        time_started = datetime.datetime.now()  # not sure why we need this ...
        loop_start_time = timeNow()
        mylog('debug', '[MAIN] Stating loop')

        # re-load user configuration and plugins   
        importConfigs(db)

        # check if new version is available / only check once an hour
        # if newVersionAvailable is already true the function does nothing and returns true again
        if last_version_check  + datetime.timedelta(hours=1) < loop_start_time :
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
        if last_scan_run + datetime.timedelta(minutes=1) < loop_start_time :

             # last time any scan or maintenance/upkeep was run
            last_scan_run = time_started

            # Header
            updateState(db,"Process: Start")      

            # Timestamp
            startTime = time_started
            startTime = startTime.replace (microsecond=0) 

            # Check if any plugins need to run on schedule
            if conf.ENABLE_PLUGINS:
                run_plugin_scripts(db,'schedule') 

            # determine run/scan type based on passed time
            # --------------------------------------------

            # check for changes in Internet IP
            if last_internet_IP_scan + datetime.timedelta(minutes=3) < time_started:
                conf.cycle = 'internet_IP'                
                last_internet_IP_scan = time_started
                check_internet_IP(db)

            # Update vendors once a week
            if last_update_vendors + datetime.timedelta(days = 7) < time_started:
                last_update_vendors = time_started
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
                    nmapSchedule.last_run = timeNow()
                    performNmapScan(db, get_all_devices(db))
            
            # Perform a network scan via arp-scan or pihole
            if last_network_scan + datetime.timedelta(minutes=conf.SCAN_CYCLE_MINUTES) < time_started:
                last_network_scan = time_started
                conf.cycle = 1 # network scan
                mylog('verbose', ['[MAIN] cycle:',conf.cycle])
                updateState(db,"Scan: Network")

                # scan_network() 

                #  DEBUG start ++++++++++++++++++++++++++++++++++++++++++++++++++++++
                # Start scan_network as a process                

                p = multiprocessing.Process(target=scan_network(db))
                p.start()

                # Wait for 3600 seconds (max 1h) or until process finishes
                p.join(3600)

                # If thread is still active
                if p.is_alive():
                    mylog('none', "[MAIN]  scan_network running too long - let\'s kill it")

                    # Terminate - may not work if process is stuck for good
                    p.terminate()
                    # OR Kill - will work for sure, no chance for process to finish nicely however
                    # p.kill()

                    p.join()

                #  DEBUG end ++++++++++++++++++++++++++++++++++++++++++++++++++++++
                # Run splugin scripts which are set to run every timne after a scan finished
                if conf.ENABLE_PLUGINS:
                    run_plugin_scripts(db,'always_after_scan')

            # --------------------------------------------------
            # process all the scanned data into new devices
            mylog('debug', "[MAIN] start processig scan results")
            process_scan (db, conf.arpscan_devices )
            
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

            # clean up the DB once a day
            if last_cleanup + datetime.timedelta(hours = 24) < time_started:
                last_cleanup = time_started
                conf.cycle = 'cleanup'  
                mylog('verbose', ['[MAIN] cycle:',conf.cycle])
                db.cleanup_database(startTime, conf.DAYS_TO_KEEP_EVENTS, conf.PHOLUS_DAYS_DATA)   

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
    sys.exit(main())       
