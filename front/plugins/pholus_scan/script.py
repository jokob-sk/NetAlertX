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

from logger import mylog
from plugin_helper import Plugin_Object, Plugin_Objects
from helper import timeNowTZ
from const import logPath, pialertPath

CUR_PATH        = str(pathlib.Path(__file__).parent.resolve())
LOG_FILE        = os.path.join(CUR_PATH, 'script.log')
RESULT_FILE     = os.path.join(CUR_PATH, 'last_result.log')
fullPholusPath  = os.path.join(CUR_PATH, 'pholus/pholus3.py')


def main():
    # sample
    # /home/pi/pialert/front/plugins/pholus_scan/script.py userSubnets=b'MTkyLjE2OC4xLjAvMjQgLS1pbnRlcmZhY2U9ZXRoMQ==' timeoutSec=10
    # sudo docker exec pialert /home/pi/pialert/front/plugins/pholus_scan/script.py userSubnets=b'MTkyLjE2OC4xLjAvMjQgLS1pbnRlcmZhY2U9ZXRoMQ==' timeoutSec=10
    
    # the script expects a parameter in the format of userSubnets=subnet1,subnet2,...
    parser = argparse.ArgumentParser(description='Import devices from settings')
    parser.add_argument('userSubnets', nargs='+', help="list of subnets with options")
    parser.add_argument('timeoutSec', nargs='+', help="timeout")
    values = parser.parse_args()

    # Assuming Plugin_Objects is a class or function that reads data from the RESULT_FILE
    # and returns a list of objects called 'devices'.
    plugin_objects = Plugin_Objects(RESULT_FILE)

    # Print a message to indicate that the script is starting.
    mylog('verbose',['[PHOLUS] In script'])

    # Assuming 'values' is a dictionary or object that contains a key 'userSubnets'
    # which holds a list of user-submitted subnets.
    # Printing the userSubnets list to check its content.
    mylog('verbose',['[PHOLUS] Subnets: ', values.userSubnets])
    mylog('verbose',['[PHOLUS] len Subnets: ', len(values.userSubnets)])

    # Extract the base64-encoded subnet information from the first element of the userSubnets list.
    # The format of the element is assumed to be like 'userSubnets=b<base64-encoded-data>'.
    userSubnetsParamBase64 = values.userSubnets[0].split('userSubnets=b')[1]
    timeoutSec = values.timeoutSec[0].split('=')[1]

    # Printing the extracted base64-encoded subnet information.
    mylog('verbose', [f'[PHOLUS] { userSubnetsParamBase64 }'])
    mylog('verbose', [f'[PHOLUS] { timeoutSec }'])

    # Decode the base64-encoded subnet information to get the actual subnet information in ASCII format.
    userSubnetsParam = base64.b64decode(userSubnetsParamBase64).decode('ascii')

    # Print the decoded subnet information.    
    mylog('verbose', [f'[PHOLUS] userSubnetsParam { userSubnetsParam } '])

    # Check if the decoded subnet information contains multiple subnets separated by commas.
    # If it does, split the string into a list of individual subnets.
    # Otherwise, create a list with a single element containing the subnet information.
    if ',' in userSubnetsParam:
        subnets_list = userSubnetsParam.split(',')
    else:
        subnets_list = [userSubnetsParam]

    # Execute the ARP scanning process on the list of subnets (whether it's one or multiple subnets).
    # The function 'execute_arpscan' is assumed to be defined elsewhere in the code.
    all_entries = execute_pholus_scan(subnets_list, timeoutSec)


    for entry in all_entries:
        plugin_objects.add_object(
            # "Info", "Time", "MAC", "IP_v4_or_v6", "Record_Type", "Value"
            primaryId   = entry[2],
            secondaryId = entry[3],
            watched1    = entry[0],
            watched2    = entry[4],
            watched3    = entry[5],
            watched4    = '',
            extra       = entry[0],
            foreignKey  = entry[2])

    plugin_objects.write_result_file()

    return 0


def execute_pholus_scan(userSubnets, timeoutSec):
    # output of possible multiple interfaces    
    result_list = []

    timeoutPerSubnet = float(timeoutSec) / len(userSubnets)

    mylog('verbose', [f'[PHOLUS] { timeoutPerSubnet } '])

    # scan each interface
    
    for interface in userSubnets:           

        temp = interface.split("--interface=")

        if len(temp) != 2:
            mylog('none', ["[PHOLUS] Skip scan (need interface in format '192.168.1.0/24 --inteface=eth0'), got: ", interface])
            return

        mask = temp[0].strip()
        interface = temp[1].strip()

        pholus_output_list = execute_pholus_on_interface (interface, timeoutPerSubnet, mask)        

        mylog('verbose', [f'[PHOLUS] { pholus_output_list } '])   
       

        result_list += pholus_output_list

    
    mylog('verbose', ["[PHOLUS] Pholus output number of entries:", len(result_list)])  
    mylog('verbose', ["[PHOLUS] List:", result_list])  

    return result_list

def execute_pholus_on_interface(interface, timeoutSec, mask):
    

    # logging & updating app state        
      
    mylog('verbose', ['[PHOLUS] Scan: Pholus for ', str(timeoutSec), 's ('+ str(round(int(timeoutSec) / 60, 1)) +'min)'])  
    mylog('verbose', ["[PHOLUS] Pholus scan on [interface] ", interface, " [mask] " , mask])
    
    # the scan always lasts 2x as long, so the desired user time from settings needs to be halved
    adjustedTimeout = str(round(int(timeoutSec) / 2, 0)) 

    #  python3 -m trace --trace /home/pi/pialert/pholus/pholus3.py eth1 -rdns_scanning  192.168.1.0/24 -stimeout 600
    pholus_args = ['python3', fullPholusPath, interface, "-rdns_scanning", mask, "-stimeout", adjustedTimeout]

    # Execute command
    output = ""

    try:
        # try runnning a subprocess with a forced (timeout + 30 seconds)  in case the subprocess hangs
        output = subprocess.check_output (pholus_args, universal_newlines=True,  stderr=subprocess.STDOUT, timeout=(timeoutSec + 30))
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        mylog('none', ['[PHOLUS]', e.output])
        mylog('none', ["[PHOLUS] ⚠ ERROR - Pholus Scan - check logs"])            
    except subprocess.TimeoutExpired as timeErr:
        mylog('none', ['[PHOLUS] Pholus TIMEOUT - the process forcefully terminated as timeout reached']) 

    if output == "": # check if the subprocess failed                    
        mylog('none', ['[PHOLUS] Scan: Pholus FAIL - check logs']) 
    else: 
        mylog('verbose', ['[PHOLUS] Scan: Pholus SUCCESS'])
    
    #  check the last run output
    f = open(logPath + '/pialert_pholus_lastrun.log', 'r+')
    newLines = f.read().split('\n')
    f.close()        

    # cleanup - select only lines containing a separator to filter out unnecessary data
    newLines = list(filter(lambda x: '|' in x, newLines))        
    
    # build SQL query parameters to insert into the DB
    params = []

    for line in newLines:
        columns = line.split("|")
        if len(columns) == 4:
            # "Info", "Time", "MAC", "IP_v4_or_v6", "Record_Type", "Value"
            params.append( [interface + " " + mask, timeNowTZ() , columns[0].replace(" ", ""), columns[1].replace(" ", ""), columns[2].replace(" ", ""), columns[3]])

    return params






#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    main()
