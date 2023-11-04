#!/usr/bin/env python

import os
import pathlib
import argparse
import sys
import re
import base64
import subprocess
from time import strftime

sys.path.append("/home/pi/pialert/front/plugins")
sys.path.append('/home/pi/pialert/pialert') 

from plugin_helper import Plugin_Object, Plugin_Objects, decodeBase64
from logger import mylog, append_line_to_file
from helper import timeNowTZ
from const import logPath, pialertPath

CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
LOG_FILE = os.path.join(CUR_PATH, 'script.log')
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

#-------------------------------------------------------------------------------
def main():
    # sample
    # /home/pi/pialert/front/plugins/nmap_scan/script.py ips=192.168.1.66,192.168.1.9'    
    parser = argparse.ArgumentParser(description='Scan ports of devices specified by IP addresses')
    parser.add_argument('ips', nargs='+', help="list of IPs to scan")
    parser.add_argument('macs', nargs='+', help="list of MACs related to the supplied IPs in the same order")
    parser.add_argument('timeout', nargs='+', help="timeout")
    parser.add_argument('args', nargs='+', help="args")
    values = parser.parse_args()

    # Plugin_Objects is a class that reads data from the RESULT_FILE
    # and returns a list of results.
    plugin_objects = Plugin_Objects(RESULT_FILE)

    # Print a message to indicate that the script is starting.
    mylog('debug', ['[NMAP Scan] In script ']) 

    # Printing the params list to check its content.
    mylog('debug', ['[NMAP Scan] values.ips: ', values.ips]) 
    mylog('debug', ['[NMAP Scan] values.macs: ', values.macs]) 
    mylog('debug', ['[NMAP Scan] values.timeout: ', values.timeout]) 
    mylog('debug', ['[NMAP Scan] values.args: ', values.args]) 

    argsDecoded = decodeBase64(values.args[0].split('=b')[1]) 

    mylog('debug', ['[NMAP Scan] argsDecoded: ', argsDecoded]) 

    entries = performNmapScan(values.ips[0].split('=')[1].split(','), values.macs[0].split('=')[1].split(',') , values.timeout[0].split('=')[1], argsDecoded)

    mylog('verbose', ['[NMAP Scan] Total number of ports found by NMAP: ', len(entries)])

    for entry in entries:        

        plugin_objects.add_object(
            primaryId   = entry.mac,    # MAC (Device Name)
            secondaryId = entry.port,   # IP Address (always 0.0.0.0)
            watched1    = entry.state,  # Device Name
            watched2    = entry.service,
            watched3    = entry.ip + ":" + entry.port,
            watched4    = "",
            extra       = entry.extra,            
            foreignKey  = entry.mac           
        )

    # generate last_result.log file
    plugin_objects.write_result_file()
        
#-------------------------------------------------------------------------------

class nmap_entry:
    def __init__(self, ip, mac, time, port, state, service, name = '', extra = '', index = 0):
        self.ip = ip
        self.mac = mac
        self.time = time
        self.port = port
        self.state = state
        self.service = service        
        self.extra = extra
        self.index = index
        self.hash = str(mac) + str(port)+ str(state)+ str(service)


#-------------------------------------------------------------------------------
def performNmapScan(deviceIPs, deviceMACs, timeoutSec, args):
    """
    run nmap scan on a list of devices
    discovers open ports and keeps track existing and new open ports
    """

    # collect ports / new Nmap Entries
    newEntriesTmp = []


    if len(deviceIPs) > 0:        

        devTotal = len(deviceIPs)
        

        mylog('verbose', ['[NMAP Scan] Scan: Nmap for max ', str(timeoutSec), 's ('+ str(round(int(timeoutSec) / 60, 1)) +'min) per device'])  
        mylog('verbose', ["[NMAP Scan] Estimated max delay: ", (devTotal * int(timeoutSec)), 's ', '(', round((devTotal * int(timeoutSec))/60,1) , 'min)' ])


        devIndex = 0
        for ip in deviceIPs:
            # Execute command
            output = ""
            # prepare arguments from user supplied ones
            nmapArgs = ['nmap'] + args.split() + [ip]

            progress = ' (' + str(devIndex+1) + '/' + str(devTotal) + ')'

            try:
                # try runnning a subprocess with a forced (timeout)  in case the subprocess hangs
                output = subprocess.check_output (nmapArgs, universal_newlines=True,  stderr=subprocess.STDOUT, timeout=(float(timeoutSec)))
            except subprocess.CalledProcessError as e:
                # An error occured, handle it
                mylog('none', ["[NMAP Scan] " ,e.output])
                mylog('none', ["[NMAP Scan] ⚠ ERROR - Nmap Scan - check logs", progress])            
            except subprocess.TimeoutExpired as timeErr:
                mylog('verbose', ['[NMAP Scan] Nmap TIMEOUT - the process forcefully terminated as timeout reached for ', ip, progress]) 

            if output == "": # check if the subprocess failed                    
                mylog('minimal', ['[NMAP Scan] Nmap FAIL for ', ip, progress ,' check logs for details']) 
            else: 
                mylog('verbose', ['[NMAP Scan] Nmap SUCCESS for ', ip, progress])

            
            
            #  check the last run output        
            newLines = output.split('\n')

            # regular logging
            for line in newLines:
                append_line_to_file (logPath + '/pialert_nmap.log', line +'\n')     


            index = 0
            startCollecting = False
            duration = "" 
            newPortsPerDevice = 0
            for line in newLines:            
                if 'Starting Nmap' in line:
                    if len(newLines) > index+1 and 'Note: Host seems down' in newLines[index+1]:
                        break # this entry is empty
                elif 'PORT' in line and 'STATE' in line and 'SERVICE' in line:
                    startCollecting = True
                elif 'PORT' in line and 'STATE' in line and 'SERVICE' in line:    
                    startCollecting = False # end reached
                elif startCollecting and len(line.split()) == 3:                                    
                    newEntriesTmp.append(nmap_entry(ip, deviceMACs[devIndex], timeNowTZ(), line.split()[0], line.split()[1], line.split()[2]))
                    newPortsPerDevice += 1
                elif 'Nmap done' in line:
                    duration = line.split('scanned in ')[1]            
            
            mylog('verbose', [f'[NMAP Scan] {newPortsPerDevice} ports found on {deviceMACs[devIndex]}'])

            index += 1
            devIndex += 1

            
            
        #end for loop       

        return newEntriesTmp

#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    main()



