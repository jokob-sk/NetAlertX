#!/usr/bin/env python
# Based on the work of https://github.com/stevehoek/Pi.Alert

# Example call
# python3 /home/pi/pialert/front/plugins/unifi_import/script.py username=pialert password=passw0rd  host=192.168.1.1 site=default  protocol=https:// port=8443

from __future__ import unicode_literals
from time import sleep, time, strftime
import requests
from requests                               import Request, Session, packages
import pathlib
import threading
import subprocess
import socket
import json
import argparse
import io
import sys
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import pwd
import os
from unificontrol   import UnifiClient
from pyunifi.controller import Controller


curPath = str(pathlib.Path(__file__).parent.resolve())
log_file = curPath + '/script.log'
last_run = curPath + '/last_result.log'

# Workflow

def main():    

    # init global variables
    global UNIFI_USERNAME, UNIFI_PASSWORD, UNIFI_HOST
    global UNIFI_REQUIRE_PRIVATE_IP, UNIFI_SKIP_NAMED_GUESTS, UNIFI_SKIP_GUESTS, UNIFI_SITES, PORT, PROTOCOL

    last_run_logfile = open(last_run, 'a') 

    # empty file
    last_run_logfile.write("")

    parser = argparse.ArgumentParser(description='Import devices from an UNIFI controller')

    parser.add_argument('username',  action="store",  help="Username used to login into the UNIFI controller")  
    parser.add_argument('password',  action="store",  help="Password used to login into the UNIFI controller")  
    parser.add_argument('host',  action="store",  help="Host url or IP address where the UNIFI controller is hosted (excluding http://)")  
    parser.add_argument('sites',  action="store",  help="Name of the sites (usually 'default', check the URL in your UniFi controller UI). Separated by comma (,) if passing multiple sites")      
    parser.add_argument('protocol',  action="store",  help="https:// or http://")  
    parser.add_argument('port',  action="store",  help="Usually 8443")  

    values = parser.parse_args()

    # parse output
    newEntries = []

    if values.username and values.password and values.host and values.sites:
        
        UNIFI_USERNAME = values.username.split('=')[1] 
        UNIFI_PASSWORD = values.password.split('=')[1]
        UNIFI_HOST = values.host.split('=')[1]  
        UNIFI_SITES = values.sites.split('=')[1]  
        PROTOCOL = values.protocol.split('=')[1]
        PORT = values.port.split('=')[1]
        
        newEntries = get_entries(newEntries)  

   
    for e in newEntries:        
        # Insert list into the log            
        service_monitoring_log(e.primaryId, e.secondaryId, e.created, e.watched1, e.watched2, e.watched3, e.watched4, e.extra, e.foreignKey )



# -----------------------------------------------------------------------------
def get_entries(newEntries):

    sites = []

    if ',' in UNIFI_SITES:
        sites = UNIFI_SITES.split(',')
    
    else:
        sites.append(UNIFI_SITES)


    for site in sites:

        c = Controller(UNIFI_HOST, UNIFI_USERNAME, UNIFI_PASSWORD, ssl_verify=False, site_id=site )

        for ap in c.get_aps():

            # print(f'{json.dumps(ap)}')

            deviceType = ''
            if (ap['type'] == 'udm'):
                deviceType = 'Router'
            elif (ap['type'] == 'usg'):
                deviceType = 'Router'
            elif (ap['type'] == 'usw'):
                deviceType = 'Switch'
            elif (ap['type'] == 'uap'):
                deviceType = 'AP'

            name = get_unifi_val(ap, 'name')
            hostName = get_unifi_val(ap, 'hostname')

            if name == 'null' and hostName != 'null':
                name = hostName

            tmpPlugObj = plugin_object_class(
                ap['mac'], 
                ap['ip'], 
                name, 
                'Ubiquiti Networks Inc.', 
                deviceType, 
                ap['state'], 
                get_unifi_val(ap, 'connection_network_name')
                )        

            newEntries.append(tmpPlugObj)

        # print(f'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')

        for cl in c.get_clients():

            # print(f'{json.dumps(cl)}')

            name = get_unifi_val(cl, 'name')
            hostName = get_unifi_val(cl, 'hostname')

            if name == 'null' and hostName != 'null':
                name = hostName

            tmpPlugObj = plugin_object_class(
                cl['mac'], 
                cl['ip'], 
                name, 
                get_unifi_val(cl, 'oui'), 
                'Other', 
                1, 
                get_unifi_val(cl, 'connection_network_name')
            )     

        # print(f'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')

        for us in c.get_clients():

            # print(f'{json.dumps(us)}')

            name = get_unifi_val(us, 'name')
            hostName = get_unifi_val(us, 'hostname')

            if name == 'null' and hostName != 'null':
                name = hostName

            tmpPlugObj = plugin_object_class(
                us['mac'], 
                us['ip'], 
                name, 
                get_unifi_val(us, 'oui'), 
                'Other', 
                1, 
                get_unifi_val(us, 'connection_network_name')
            )         

            newEntries.append(tmpPlugObj)

    return newEntries


# -----------------------------------------------------------------------------
def get_unifi_val(obj, key):

    res = ''

    if key in obj:
        res = obj[key]

    if res not in ['','None']:
        return res
    
    if obj.get(key) is not None:
        res = obj.get(key)

    if res not in ['','None']:
        return res

    return 'null'

# -------------------------------------------------------------------
class plugin_object_class:
    def __init__(self, primaryId = '',secondaryId = '', watched1 = '',watched2 = '',watched3 = '',watched4 = '',extra = '',foreignKey = ''):        
        self.pluginPref   = ''
        self.primaryId    = primaryId
        self.secondaryId  = secondaryId
        self.created      = strftime("%Y-%m-%d %H:%M:%S")
        self.changed      = ''
        self.watched1     = watched1
        self.watched2     = watched2
        self.watched3     = watched3
        self.watched4     = watched4
        self.status       = ''
        self.extra        = extra
        self.userData     = ''
        self.foreignKey   = foreignKey

# -----------------------------------------------------------------------------
def service_monitoring_log(primaryId, secondaryId, created, watched1, watched2 = 'null', watched3 = 'null', watched4 = 'null', extra ='null', foreignKey ='null'  ):
    
    if watched1 == '':
        watched1 = 'null'
    if watched2 == '':
        watched2 = 'null'
    if watched3 == '':
        watched3 = 'null'
    if watched4 == '':
        watched4 = 'null'
    if extra == '':
        extra = 'null'
    if foreignKey == '':
        foreignKey = 'null'

    with open(last_run, 'a') as last_run_logfile:
        # https://www.duckduckgo.com|192.168.0.1|2023-01-02 15:56:30|200|0.9898|null|null|Best search engine|null
        last_run_logfile.write("{}|{}|{}|{}|{}|{}|{}|{}|{}\n".format(
                                                primaryId,
                                                secondaryId,
                                                created,                                                
                                                watched1,
                                                watched2,
                                                watched3,
                                                watched4,
                                                extra,
                                                foreignKey
                                                )
                             )


#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':    
    main()  

