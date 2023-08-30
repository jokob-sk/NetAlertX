#!/usr/bin/env python
# Inspired by https://github.com/stevehoek/Pi.Alert

# Example call

# python3 /home/pi/pialert/front/plugins/unifi_import/script.py username=pialert password=passw0rd  host=192.168.1.1 site=default  protocol=https:// port=8443 version='UDMP-unifiOS'
# python3 /home/pi/pialert/front/plugins/unifi_import/script.py username=pialert password=passw0rd host=192.168.1.1 sites=sdefault port=8443 verifyssl=false version=v5


from __future__ import unicode_literals
from time import sleep, time, strftime
import requests
from requests import Request, Session, packages
import pathlib
import threading
import subprocess
import socket
import json
import argparse
import logging
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from pyunifi.controller import Controller


curPath = str(pathlib.Path(__file__).parent.resolve())
log_file = curPath + '/script.log'
last_run = curPath + '/last_result.log'

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s'
)
unifi_logger = logging.getLogger('[UNIFI]')
unifi_logger.setLevel(logging.INFO)


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)




# Workflow

def main():    

    unifi_logger.info('Start scan')
    # init global variables
    global UNIFI_USERNAME, UNIFI_PASSWORD, UNIFI_HOST, UNIFI_SITES, PORT, VERIFYSSL, VERSION


    # empty file
    unifi_logger.debug('Purging old values')
    with open(last_run, 'w') as last_run_logfile:
        last_run_logfile.write("")

    parser = argparse.ArgumentParser(description='Import devices from an UNIFI controller')

    parser.add_argument('username',  action="store",  help="Username used to login into the UNIFI controller")  
    parser.add_argument('password',  action="store",  help="Password used to login into the UNIFI controller")  
    parser.add_argument('host',  action="store",  help="Host url or IP address where the UNIFI controller is hosted (excluding http://)")  
    parser.add_argument('sites',  action="store",  help="Name of the sites (usually 'default', check the URL in your UniFi controller UI). Separated by comma (,) if passing multiple sites")      
    parser.add_argument('port',  action="store",  help="Usually 8443")  
    parser.add_argument('verifyssl',  action="store",  help="verify SSL certificate [true|false]")  
    parser.add_argument('version',  action="store",  help="The base version of the controller API [v4|v5|unifiOS|UDMP-unifiOS]")  

    values = parser.parse_args()

    # parse output
    newEntries = []

    unifi_logger.debug(f'Check if all login information is available: {values}')
    if values.username and values.password and values.host and values.sites:
        
        UNIFI_USERNAME = values.username.split('=')[1] 
        UNIFI_PASSWORD = values.password.split('=')[1]
        UNIFI_HOST = values.host.split('=')[1]  
        UNIFI_SITES = values.sites.split('=')[1]  
        PORT = values.port.split('=')[1]
        VERIFYSSL = values.verifyssl.split('=')[1]
        VERSION = values.version.split('=')[1]

        newEntries = get_entries(newEntries)  

    unifi_logger.debug(f'Print {len(newEntries)} to monitoring log')
    for e in newEntries:        
        # Insert list into the log            
        service_monitoring_log(e.primaryId, e.secondaryId, e.created, e.watched1, e.watched2, e.watched3, e.watched4, e.extra, e.foreignKey )

    unifi_logger.info(f'Scan finished, found {len(newEntries)} devices')

# -----------------------------------------------------------------------------
def get_entries(newEntries):
    global VERIFYSSL

    sites = []

    if ',' in UNIFI_SITES:
        sites = UNIFI_SITES.split(',')
    
    else:
        sites.append(UNIFI_SITES)

    if (VERIFYSSL.upper() == "TRUE"):
        VERIFYSSL = True
    else:
        VERIFYSSL = False

    for site in sites:

        c = Controller(UNIFI_HOST, UNIFI_USERNAME, UNIFI_PASSWORD, port=PORT, version=VERSION, ssl_verify=VERIFYSSL, site_id=site )

        unifi_logger.debug('identify Unifi Devices')
        # get all Unifi devices
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

            name = set_name(name, hostName)

            tmpPlugObj = plugin_object_class(
                ap['mac'], 
                get_unifi_val(ap, 'ip'), 
                name, 
                'Ubiquiti Networks Inc.', 
                deviceType, 
                ap['state'], 
                get_unifi_val(ap, 'connection_network_name')
                )        

            newEntries.append(tmpPlugObj)

        unifi_logger.debug(f'Found {len(newEntries)} Unifi Devices')
        # print(f'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')

        online_macs = set()

        # get_clients() returns all clients which are currently online.
        for cl in c.get_clients():

            # print(f'{json.dumps(cl)}')
            online_macs.add(cl['mac'])

        unifi_logger.debug(f'Found {len(online_macs)} Online Clients')

        # print(f'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')

        # get_users() returns all clients known by the controller
        for user in c.get_users():

            # print(f'{json.dumps(user)}')

            name = get_unifi_val(user, 'name')
            hostName = get_unifi_val(user, 'hostname')

            name = set_name(name, hostName)

            status = 1 if user['mac'] in online_macs else 0

            if status == 1:

                tmpPlugObj = plugin_object_class(
                    user['mac'],
                    get_unifi_val(user, 'last_ip'),
                    name,
                    get_unifi_val(user, 'oui'),
                    'Other',
                    status,
                    get_unifi_val(user, 'last_connection_network_name')
                )

                newEntries.append(tmpPlugObj)

    unifi_logger.debug(f'Found {len(newEntries)} Clients overall')
    return newEntries


# -----------------------------------------------------------------------------
def get_unifi_val(obj, key):

    res = ''

    res = obj.get(key, None)

    if res not in ['','None', None]:
        return res


    return 'null'

# -----------------------------------------------------------------------------

def set_name(name: str, hostName: str) -> str:

    if name != 'null':
        return name

    elif name == 'null' and hostName != 'null':
        return hostName

    else:
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
def service_monitoring_log(primaryId, secondaryId, created, watched1, watched2 = 'null', watched3 = 'null', watched4 = 'null', extra ='null', foreignKey ='null'):
    
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

    unifi_logger.debug(f'Adding entry to monitoring log:\n{primaryId}, {secondaryId}, {created}, {watched1}, {watched2}, {watched3}, {watched4}, {extra}')
    with open(last_run, 'a') as last_run_logfile:        
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

