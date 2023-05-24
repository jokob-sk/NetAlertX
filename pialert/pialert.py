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
import subprocess
import os
import re
import time
import decimal
import datetime
from datetime import timedelta
import sqlite3
import socket
import io
import smtplib
import csv
import json
import requests
import threading
from pathlib import Path
from cron_converter import Cron

from json2table import convert
import hashlib
import multiprocessing


# pialert modules
import conf
from const import *
from logger import  mylog
from helper import  filePermissions, isNewVersion,  timeNow, updateState
from api import update_api
from files import get_file_content
from networkscan import scan_network
from initialise import importConfigs
from mac_vendor import update_devices_MAC_vendors
from database import DB, get_all_devices, upgradeDB, sql_new_devices
from reporting import send_apprise, send_email, send_notifications, send_ntfy, send_pushsafer, send_webhook
from plugin import run_plugin_scripts 

# different scanners
from pholusscan import performPholusScan
from nmapscan import performNmapScan
from internet import check_internet_IP


# Global variables
changedPorts_json_struc = None
time_started = datetime.datetime.now()
cron_instance = Cron()
log_timestamp = time_started
lastTimeImported = 0
sql_connection = None




#===============================================================================
#===============================================================================
#                              MAIN
#===============================================================================
#===============================================================================
cycle = ""
check_report = [1, "internet_IP", "update_vendors_silent"]
conf.plugins_once_run = False

# timestamps of last execution times
startTime = time_started
now_minus_24h = time_started - datetime.timedelta(hours = 24)

last_network_scan = now_minus_24h
last_internet_IP_scan = now_minus_24h
last_run = now_minus_24h
last_cleanup = now_minus_24h
last_update_vendors = time_started - datetime.timedelta(days = 6) # update vendors 24h after first run and then once a week

# indicates, if a new version is available
newVersionAvailable = False

def main ():
    # Initialize global variables
    global time_started, cycle, last_network_scan, last_internet_IP_scan, last_run, last_cleanup, last_update_vendors
    # second set of global variables
    global startTime, log_timestamp, plugins_once_run 
    

    # check file permissions and fix if required
    filePermissions()

    # Open DB once and keep open
    # Opening / closing DB frequently actually casues more issues
    db = DB()  # instance of class DB
    db.openDB()

    # To-Do replace the following to lines with the db class
    # sql_connection = db.sql_connection
    sql = db.sql

    # Upgrade DB if needed
    upgradeDB(db)


    #===============================================================================
    # This is the main loop of Pi.Alert 
    #===============================================================================

    while True:

        # update time started
        time_started = datetime.datetime.now()
        mylog('debug', ['[', timeNow(), '] [MAIN] Stating loop'])

        # re-load user configuration and plugins
        mylog('debug', "tz before config : " + str(conf.tz))        
        importConfigs(db)       
        mylog('debug', "tz after config : " + str(conf.tz))  

        # check if new version is available
        conf.newVersionAvailable = isNewVersion(False)

        # Handle plugins executed ONCE
        if conf.ENABLE_PLUGINS and conf.plugins_once_run == False:
            run_plugin_scripts(db, 'once')  
            plugins_once_run = True

        # check if there is a front end initiated event which needs to be executed
        check_and_run_event(db)

        # Update API endpoints              
        update_api()
        
        # proceed if 1 minute passed
        if last_run + datetime.timedelta(minutes=1) < time_started :

             # last time any scan or maintenance/upkeep was run
            last_run = time_started

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
                cycle = 'internet_IP'                
                last_internet_IP_scan = time_started
                check_internet_IP(db)

            # Update vendors once a week
            if last_update_vendors + datetime.timedelta(days = 7) < time_started:
                last_update_vendors = time_started
                cycle = 'update_vendors'
                mylog('verbose', ['[', timeNow(), '] cycle:',cycle])                  
                update_devices_MAC_vendors()

            # Execute scheduled or one-off Pholus scan if enabled and run conditions fulfilled
            if conf.PHOLUS_RUN == "schedule" or conf.PHOLUS_RUN == "once":

                mylog('debug', "PHOLUS_RUN_SCHD: " + conf.PHOLUS_RUN_SCHD)
                mylog('debug', "schedules : " + str(conf.mySchedules))

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
                if conf.NMAP_RUN == "once" and conf.nmapSchedule.last_run == 0:
                    run = True

                # run if overdue scheduled time
                if conf.NMAP_RUN == "schedule":
                    run = nmapSchedule.runScheduleCheck()                    

                if run:
                    conf.nmapSchedule.last_run = datetime.datetime.now(conf.tz).replace(microsecond=0)
                    performNmapScan(db, get_all_devices(db))
            
            # Perform a network scan via arp-scan or pihole
            if last_network_scan + datetime.timedelta(minutes=conf.SCAN_CYCLE_MINUTES) < time_started:
                last_network_scan = time_started
                cycle = 1 # network scan
                mylog('verbose', ['[', timeNow(), '] cycle:',cycle])
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
                    print("DEBUG scan_network running too long - let\'s kill it")
                    mylog('info', ['    DEBUG scan_network running too long - let\'s kill it'])

                    # Terminate - may not work if process is stuck for good
                    p.terminate()
                    # OR Kill - will work for sure, no chance for process to finish nicely however
                    # p.kill()

                    p.join()

                #  DEBUG end ++++++++++++++++++++++++++++++++++++++++++++++++++++++
                # Run splugin scripts which are set to run every timne after a scan finished
                if conf.ENABLE_PLUGINS:
                    run_plugin_scripts(db,'always_after_scan')

            
            # Reporting   
            if cycle in check_report:
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
                cycle = 'cleanup'  
                mylog('verbose', ['[', timeNow(), '] cycle:',cycle])
                db.cleanup_database(startTime, conf.DAYS_TO_KEEP_EVENTS, conf.PHOLUS_DAYS_DATA)   

            # Commit SQL
            db.commitDB()          
            
            # Final message
            if cycle != "":
                action = str(cycle)
                if action == "1":
                    action = "network_scan"
                mylog('verbose', ['[', timeNow(), '] Last action: ', action])
                cycle = ""
                mylog('verbose', ['[', timeNow(), '] cycle:',cycle])
            
            # Footer
            updateState(db,"Process: Wait")
            mylog('verbose', ['[', timeNow(), '] Process: Wait'])            
        else:
            # do something
            cycle = "" 
            mylog('verbose', ['[', timeNow(), '] [MAIN] waiting to start next loop'])          

        #loop     
        time.sleep(5) # wait for N seconds      







#===============================================================================
# UTIL
#===============================================================================

#-------------------------------------------------------------------------------
def check_and_run_event(db):
    sql = db.sql # TO-DO
    sql.execute(""" select * from Parameters where par_ID = "Front_Event" """)
    rows = sql.fetchall()    

    event, param = ['','']
    if len(rows) > 0 and rows[0]['par_Value'] != 'finished':        
        event = rows[0]['par_Value'].split('|')[0]
        param = rows[0]['par_Value'].split('|')[1]
    else:
        return

    if event == 'test':
        handle_test(param)
    if event == 'run':
        handle_run(param)

    # clear event execution flag
    sql.execute ("UPDATE Parameters SET par_Value='finished' WHERE par_ID='Front_Event'")        

    # commit to DB  
    db.commitDB()

#-------------------------------------------------------------------------------
def handle_run(runType):
    global last_network_scan

    mylog('info', ['[', timeNow(), '] START Run: ', runType])  

    if runType == 'ENABLE_ARPSCAN':
        last_network_scan = now_minus_24h        

    mylog('info', ['[', timeNow(), '] END Run: ', runType])

#-------------------------------------------------------------------------------
def handle_test(testType):

    mylog('info', ['[', timeNow(), '] START Test: ', testType])    

    # Open text sample    
    sample_txt = get_file_content(pialertPath + '/back/report_sample.txt')

    # Open html sample     
    sample_html = get_file_content(pialertPath + '/back/report_sample.html')

    # Open json sample and get only the payload part      
    sample_json_payload = json.loads(get_file_content(pialertPath + '/back/webhook_json_sample.json'))[0]["body"]["attachments"][0]["text"]      
    
    if testType == 'REPORT_MAIL':
        send_email(sample_txt, sample_html)
    if testType == 'REPORT_WEBHOOK':
        send_webhook (sample_json_payload, sample_txt)
    if testType == 'REPORT_APPRISE':
        send_apprise (sample_html, sample_txt) 
    if testType == 'REPORT_NTFY':
        send_ntfy (sample_txt)
    if testType == 'REPORT_PUSHSAFER':
        send_pushsafer (sample_txt)

    mylog('info', ['[', timeNow(), '] END Test: ', testType])









#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# Plugins
#-------------------------------------------------------------------------------


#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    sys.exit(main())       
