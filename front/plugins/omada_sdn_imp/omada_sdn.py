#!/usr/bin/env python
__author__ = "ffsb"
__version__ = "0.1"  #initial
__version__ = "0.2"  # added logic to retry omada api call once as it seems to sometimes fail for some reasons, and error handling logic...
# query OMADA SDN to populate NetAlertX witch omada switches, access points, clients.
# try to identify and populate their connections by switch/accesspoints and ports/SSID
# try to differentiate root bridges from accessory 


#
# sample code to update unbound on opnsense - for reference...
# curl -X POST -d '{"host":{"enabled":"1","hostname":"test","domain":"testdomain.com","rr":"A","mxprio":"","mx":"","server":"10.0.1.1","description":""}}' -H "Content-Type: application/json" -k -u $OPNS_KEY:$OPNS_SECRET https://$IPFW/api/unbound/settings/AddHostOverride
#
import os
import pathlib
import sys
import json
import sqlite3
import tplink_omada_client
import importlib.util
import time
import io
import re
#import netifaces

# Define the installation path and extend the system path for plugin imports
INSTALL_PATH = "/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from plugin_helper import Plugin_Object, Plugin_Objects, decodeBase64
from plugin_utils import get_plugins_configs
from logger import mylog
from const import pluginsPath, fullDbPath
from helper import timeNowTZ, get_setting_value 
from notification import write_notification

# Define the current path and log file paths
CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
LOG_FILE = os.path.join(CUR_PATH, 'script.log')
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

# Initialize the Plugin obj output file
plugin_objects = Plugin_Objects(RESULT_FILE)

pluginName = 'OMDSDN'
# sample target output:
#    0)MAC,              1)IP,            2)Name,   3)switch/AP,      4)port/SSID, 5)TYPE    
# "['9C-04-A0-82-67-45', '192.168.0.217', 'foo',   '40-AE-30-A5-A7-50, '17',  'Switch']"
# constants:
MAC = 0 
IP = 1
NAME = 2
SWITCH_AP = 3
PORT_SSID = 4
TYPE = 5
OMDLOGLEVEL='debug'
#
# translate MAC address from standard ieee model to ietf draft
# AA-BB-CC-DD-EE-FF to aa:bb:cc:dd:ee:ff
# tplink adheres to ieee,  Nax adheres to ietf
def ieee2ietf_mac_formater(inputmac):
    return(inputmac.lower().replace('-',':'))

def ietf2ieee_mac_formater(inputmac):
    return(inputmac.upper().replace(':','-'))

def get_mac_from_IP(target_IP):
    from scapy.all import ARP, Ether, srp
    try:
        arp_request = ARP(pdst=target_IP)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether/arp_request
        result = srp(packet, timeout=3, verbose=0)[0]
        if result:
            return result[0][1].hwsrc
        else:
            return None
    except Exception as e:
        mylog('minimal', [f'[{pluginName}] get_mac_from_IP ERROR:{e}'])
        return None
    
    

#
# wrapper to call the omada python library's own wrapper 
# it returns the output as a multiline python string 
#
def callomada(myargs):
    arguments=" ".join(myargs)
    mylog('verbose', [f'[{pluginName}] callomada:{arguments}'])
    from tplink_omada_client.cli    import main as omada 
    from contextlib import redirect_stdout
    omada_output = ''
    retries = 2
    while omada_output == '' and retries > 1:
        retries = retries - 1
        try:
            mf = io.StringIO()
            with redirect_stdout(mf):
                bar = omada(myargs)
            omada_output = mf.getvalue()
        except Exception as e:
            mylog('minimal', [f'[{pluginName}] ERROR WHILE CALLING callomada:{arguments}\n {mf}'])
            omada_output= ''
    return(omada_output)

#
# extract all the mac addresses from a multilines text...
# return a list of MAC as 'string' 
#
def extract_mac_addresses(text):
    mac_pattern = r"([0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2})"
    mac_addresses = re.findall(mac_pattern, text)
    return ["".join(parts) for parts in mac_addresses]

def find_default_gateway_ip ():
    #import netifaces
    #gw = netifaces.gateways()
    #return(gw['default'][netifaces.AF_INET][0])
    from scapy.all import conf, Route, sr1, IP, ICMP
    default_route = conf.route.route("0.0.0.0")
    return default_route[2] if default_route[2] else None


    return('192.168.0.1')

""" 
def find_port_of_uplink_switch(switch_mac, uplink_mac):
    mylog(OMDLOGLEVEL, [f'[{pluginName}] find_port uplink="{uplink_mac}" on switch="{switch_mac}"'])
    myport = []
    switchdump = callomada(['-t','myomada','switch','-d',switch_mac])
    port_pattern = r"(?:{[^}]*\"port\"\: )([0-9]+)(?=[^}]*"+re.escape(uplink_mac)+r")"
    myport = re.findall(port_pattern, switchdump,re.DOTALL)
    # print("myswitch=",mymac, "- link_switch=", mylink, "myport=", myport) 
    mylog(OMDLOGLEVEL, [f'[{pluginName}] finding port="{myport}" of uplink switch="{uplink_mac}" on switch="{switch_mac}"'])    
    try:
        myport2=myport[0]    
    except IndexError:
        myport2 = 'defaultGateWay'
    return(myport2)

 """


def add_uplink (uplink_mac, switch_mac, device_data_bymac, sadevices_linksbymac,port_byswitchmac_byclientmac):
    mylog(OMDLOGLEVEL, [f'[{pluginName}] trying to add uplink="{uplink_mac}" to switch="{switch_mac}"'])
    mylog(OMDLOGLEVEL, [f'[{pluginName}] before adding:"{device_data_bymac[switch_mac]}"'])
    if device_data_bymac[switch_mac][SWITCH_AP] == 'null': 
        device_data_bymac[switch_mac][SWITCH_AP] = uplink_mac
        if device_data_bymac[switch_mac][TYPE] == 'Switch' and device_data_bymac[uplink_mac][TYPE] == 'Switch':
            port_to_uplink = port_byswitchmac_byclientmac[switch_mac][uplink_mac] 
            #find_port_of_uplink_switch(switch_mac, uplink_mac)
        else:
            port_to_uplink=device_data_bymac[uplink_mac][PORT_SSID]
        device_data_bymac[switch_mac][PORT_SSID] = port_to_uplink
        mylog(OMDLOGLEVEL, [f'[{pluginName}] after adding:"{device_data_bymac[switch_mac]}"'])    
    for link  in sadevices_linksbymac[switch_mac]:
        if device_data_bymac[link][SWITCH_AP] == 'null' and device_data_bymac[switch_mac][TYPE] == 'Switch':
            add_uplink(switch_mac, link, device_data_bymac, sadevices_linksbymac,port_byswitchmac_byclientmac)



# ----------------------------------------------
# Main initialization
def main():
    start_time = time.time()
    mylog('verbose', [f'[{pluginName}] starting execution']) 
    from database import DB
    from device import Device_obj
    db = DB()  # instance of class DB
    db.open()
     # Create a Device_obj instance
    device_handler = Device_obj(db)
    # Retrieve configuration settings
    # these should be self-explanatory
    omada_sites = [] 
    omada_username = get_setting_value('OMDSDN_username')
    omada_password = get_setting_value('OMDSDN_password')
    omada_sites = get_setting_value('OMDSDN_sites')
    omada_site = omada_sites[0]
    omada_url = get_setting_value('OMDSDN_url')
    
    omada_login = callomada(['-t','myomada','target','--url',omada_url,'--user',omada_username,
                             '--password',omada_password,'--site',omada_site,'--set-default'])
    mylog('verbose', [f'[{pluginName}] login to omada result is: {omada_login}'])    
        
    clients_list = callomada(['-t','myomada','clients'])
    mylog('verbose', [f'[{pluginName}] clients found:"{clients_list.count("\n")}"\n{clients_list}'])    

    switches_and_aps = callomada(['-t','myomada','devices'])
    mylog('verbose', [f'[{pluginName}] omada devices (switches, access points) found:"{switches_and_aps.count("\n")}" \n  {switches_and_aps}'])    
    

    #some_setting = get_setting_value('OMDSDN_url')

    #mylog(OMDLOGLEVEL, [f'[{pluginName}] some_setting value {some_setting}'])
    mylog(OMDLOGLEVEL, [f'[{pluginName}] ffsb'])




    # retrieve data
    device_data = get_device_data(clients_list, switches_and_aps, device_handler)

    #  Process the data into native application tables
    mylog('verbose', [f'[{pluginName}] New entries to create: "{len(device_data)}"'])
    if len(device_data) > 0:

        # insert devices into the lats_result.log 
        # make sure the below mapping is mapped in config.json, for example: 
        #"database_column_definitions": [
        # {
        #   "column": "Object_PrimaryID",                 <--------- the value I save into primaryId
        #   "mapped_to_column": "cur_MAC",                <--------- gets unserted into the CurrentScan DB table column cur_MAC
        #  watched1    = 'null' ,
        #  figure a way to run my udpate script delayed

        for device in device_data:
                mylog(OMDLOGLEVEL, [f'[{pluginName}] main parsing device: "{device}"'])
                if device[PORT_SSID].isdigit():
                    myport = device[PORT_SSID]
                    myssid = 'null'
                else:
                    myssid = device[PORT_SSID]
                    myport = 'null'
                if device[SWITCH_AP] != 'Internet':
                    ParentNetworkNode = ieee2ietf_mac_formater(device[SWITCH_AP])
                else:
                    ParentNetworkNode = device[SWITCH_AP]
                plugin_objects.add_object(
                    primaryId   = ieee2ietf_mac_formater(device[MAC]),    #  MAC
                    secondaryId = device[IP],    #  IP
                    watched1    = device[NAME],    #  NAME/HOSTNAME
                    watched2    = ParentNetworkNode,    #  PARENT NETWORK NODE MAC
                    watched3    = myport,    #  PORT
                    watched4    = myssid,    #  SSID
                    extra       = device[TYPE],
                    #omada_site,    #  SITENAME (cur_NetworkSite) or VENDOR (cur_Vendor) (PICK one and adjust config.json -> "column": "Extra")
                    foreignKey  = device[MAC].lower().replace('-',':'))    #  usually MAC
        mylog(OMDLOGLEVEL, [f'[{pluginName}] New entries: "{len(device_data)}"'])

    # log result
    plugin_objects.write_result_file()
    
    #mylog(OMDLOGLEVEL, [f'[{pluginName}] TEST name from MAC: {device_handler.getValueWithMac('dev_Name','00:e2:59:00:a0:8e')}'])  
    #mylog(OMDLOGLEVEL, [f'[{pluginName}] TEST MAC from IP: {get_mac_from_IP('192.168.0.1')} also {ietf2ieee_mac_formater(get_mac_from_IP('192.168.0.1'))}'])  
    

    return 0




# ----------------------------------------------
#  retrieve data
def get_device_data(omada_clients_output,switches_and_aps,device_handler):
    
    
    # sample omada devices input format:
    #  0.MAC                    1.IP    2.type  3.status           4.name              5.model
    #40-AE-30-A5-A7-50    192.168.0.11      ap CONNECTED        ompapaoffice         EAP773(US) v1.0
    #B0-95-75-46-0C-39     192.168.0.4  switch CONNECTED        pantry12             T1600G-52PS v4.0
    #
    # sample target output:
    #  0 MAC, 1 IP, 2 Name, 3 switch/AP, 4 port/SSID, 5 TYPE    
    #17:27:10 [<unique_prefix>] token: "['9C-04-A0-82-67-45', '192.168.0.217', '9C-04-A0-82-67-45', '17', '40-AE-30-A5-A7-50, 'Switch']"
    #constants
    dMAC = 0
    dIP = 1
    dTYPE = 2
    dSTATUS = 3
    dNAME = 4
    dMODEL = 5
    sadevices_macbyname = {}
    sadevices_macbymac = {}
    sadevices_linksbymac = {}
    port_byswitchmac_byclientmac = {}
    device_data_bymac = {}
    device_data_mac_byip = {}
    omada_force_overwrite = get_setting_value('OMDSDN_force_overwrite')
   
    sadevices = switches_and_aps.splitlines()
    mylog(OMDLOGLEVEL, [f'[{pluginName}] switches_and_aps rows: "{len(sadevices)}"'])
    for sadevice in sadevices:
        sadevice_data = sadevice.split()
        thisswitch = sadevice_data[dMAC]
        sadevices_macbyname[sadevice_data[4]] = thisswitch
        if sadevice_data[dTYPE] == 'ap':
            sadevice_type = 'AP'
            sadevice_details = callomada(['access-point', thisswitch])
            if sadevice_details == '':
                sadevice_links = [thisswitch]
            else:
                sadevice_links = extract_mac_addresses(sadevice_details)
            sadevices_linksbymac[thisswitch] = sadevice_links[1:]
            mylog(OMDLOGLEVEL, [f'[{pluginName}]adding switch details: "{sadevice_details}"'])
            mylog(OMDLOGLEVEL, [f'[{pluginName}]links are: "{sadevice_links}"'])
            mylog(OMDLOGLEVEL, [f'[{pluginName}]linksbymac are: "{sadevices_linksbymac[thisswitch]}"'])
        elif sadevice_data[dTYPE] == 'switch':
            sadevice_type = 'Switch'
            sadevice_details=callomada(['switch', thisswitch])
            if sadevice_details == '':
                sadevice_links = [thisswitch]
            else:
                sadevice_links=extract_mac_addresses(sadevice_details)
            sadevices_linksbymac[thisswitch] = sadevice_links[1:]
            # recovering the list of switches connected to sadevice switch and on which port...
            switchdump = callomada(['-t','myomada','switch','-d',thisswitch])
            port_byswitchmac_byclientmac[thisswitch]  = {}
            for link in sadevices_linksbymac[thisswitch]:
                port_pattern = r"(?:{[^}]*\"port\"\: )([0-9]+)(?=[^}]*"+re.escape(link)+r")"
                myport = re.findall(port_pattern, switchdump,re.DOTALL)
                port_byswitchmac_byclientmac[thisswitch][link] = myport[0]
            mylog(OMDLOGLEVEL, [f'[{pluginName}]links are: "{sadevice_links}"'])
            mylog(OMDLOGLEVEL, [f'[{pluginName}]linksbymac are: "{sadevices_linksbymac[thisswitch]}"'])
            mylog(OMDLOGLEVEL, [f'[{pluginName}]ports of each links  are: "{port_byswitchmac_byclientmac[thisswitch]}"'])
            mylog(OMDLOGLEVEL, [f'[{pluginName}]adding switch details: "{sadevice_details}"'])
        else:
            sadevice_type = 'null'
            sadevice_details='null'
        device_data_bymac[thisswitch] = [thisswitch, sadevice_data[dIP], sadevice_data[dNAME], 'null', 'null',sadevice_type]
        device_data_mac_byip[sadevice_data[dIP]] = thisswitch
        foo=[thisswitch, sadevice_data[1], sadevice_data[4], 'null', 'null']
        mylog(OMDLOGLEVEL, [f'[{pluginName}]adding switch: "{foo}"'])
        
    
        

    #    sadevices_macbymac[thisswitch] = thisswitch
    
    mylog(OMDLOGLEVEL, [f'[{pluginName}] switch_macbyname: "{sadevices_macbyname}"'])
    mylog(OMDLOGLEVEL, [f'[{pluginName}] switches: "{device_data_bymac}"'])


    # do some processing, call exteranl APIs, and return a device list
    #  ...
    """  MAC = 0
    IP = 1
    NAME = 2
    SWITCH_AP = 3
    PORT_SSID = 4
    TYPE = 5 """
    # sample omada clients input format:
    #  0 MAC, 1 IP, 2 Name, 3 switch/AP, 4 port/SSID, 
    #17:27:10 [<unique_prefix>] token: "['9C-04-A0-82-67-45', '192.168.0.217', '9C-04-A0-82-67-45', 'froggies2', '(ompapaoffice)']"
    #17:27:10 [<unique_prefix>] token: "['50-02-91-29-E7-53', '192.168.0.153', 'frontyard_ESP_29E753', 'pantry12', '(48)']"
    #17:27:10 [<unique_prefix>] token: "['00-E2-59-00-A0-8E', '192.168.0.1', 'bastion', 'office24', '(23)']"
    #17:27:10 [<unique_prefix>] token: "['60-DD-8E-CA-A4-B3', '192.168.0.226', 'brick', 'froggies3', '(ompapaoffice)']"
    cMAC = 0
    cIP = 1
    cNAME = 2
    cSWITCH_AP = 3
    cPORT_SSID = 4

    # sample target output:
    #  0 MAC, 1 IP, 2 Name, 3 MAC of switch/AP, 4 port/SSID, 5 TYPE    
    #17:27:10 [<unique_prefix>] token: "['9C-04-A0-82-67-45', '192.168.0.217', 'brick', 'ompapaoffice','froggies2', , 'Switch']"

    odevices = omada_clients_output.splitlines()
    mylog(OMDLOGLEVEL, [f'[{pluginName}] omada_clients_outputs rows: "{len(odevices)}"'])
    for odevice in odevices:
        odevice_data = odevice.split()
        odevice_data_reordered = [ MAC, IP, NAME, SWITCH_AP, PORT_SSID, TYPE]
        odevice_data_reordered[MAC]=odevice_data[cMAC]
        odevice_data_reordered[IP]=odevice_data[cIP]
        real_naxname = device_handler.getValueWithMac('dev_Name',ieee2ietf_mac_formater(odevice_data[cMAC]))

        #
        # if the name stored in Nax for a device is empty or the MAC addres or has some parenthhesis or is the same as in omada
        # don't bother updating omada's name at all.
        #
        if real_naxname == None or ietf2ieee_mac_formater(real_naxname) == odevice_data[cMAC] or '('in real_naxname or  real_naxname == odevice_data[cNAME] or  real_naxname == 'null':
            naxname = None
        else:
            naxname = real_naxname
        mylog('debug', [f'[{pluginName}] TEST name from MAC: {naxname}'])    
        if odevice_data[cMAC] == odevice_data[cNAME]:
            if naxname != None:
                callomada(['set-client-name', odevice_data[cMAC], naxname])
                odevice_data_reordered[NAME] = naxname
            else:
                odevice_data_reordered[NAME] = real_naxname
        else:
            if omada_force_overwrite and naxname != None:
                callomada(['set-client-name', odevice_data[cMAC], naxname])
            odevice_data_reordered[NAME] = odevice_data[cNAME]
        mightbeport = odevice_data[cPORT_SSID].lstrip('(')
        mightbeport = mightbeport.rstrip(')')
        if mightbeport.isdigit():
            odevice_data_reordered[SWITCH_AP] = odevice_data[cSWITCH_AP]
            odevice_data_reordered[PORT_SSID] = mightbeport
        else:
            odevice_data_reordered[SWITCH_AP] = mightbeport
            odevice_data_reordered[PORT_SSID] = odevice_data[cSWITCH_AP]
        
        # replacing the switch name with its MAC...
        try:
            mightbemac = sadevices_macbyname[odevice_data_reordered[SWITCH_AP]]
            odevice_data_reordered[SWITCH_AP] = mightbemac
        except KeyError:
            mylog(OMDLOGLEVEL, [f'[{pluginName}] could not find the mac adddress for: "{odevice_data_reordered[SWITCH_AP]}"'])
        # adding the type
        odevice_data_reordered[TYPE] = 'null'
        device_data_bymac[odevice_data_reordered[MAC]]  = odevice_data_reordered
        device_data_mac_byip[odevice_data_reordered[IP]] = odevice_data_reordered[MAC]
        mylog(OMDLOGLEVEL, [f'[{pluginName}] tokens: "{odevice_data}"'])
        mylog(OMDLOGLEVEL, [f'[{pluginName}] tokens_reordered: "{odevice_data_reordered}"'])
    # populating the uplinks nodes of the omada switches and access points manually 
    # since OMADA SDN makes is unreliable if the gateway is not their own tplink hardware...

    
    # step1 let's find the the default router
    # 
    default_router_ip =  find_default_gateway_ip()
    default_router_mac = ietf2ieee_mac_formater(get_mac_from_IP(default_router_ip))
    device_data_bymac[default_router_mac][TYPE] = 'Firewall'           
    # step2 let's find the first switch and set the default router parent to internet
    first_switch=device_data_bymac[default_router_mac][SWITCH_AP]
    device_data_bymac[default_router_mac][SWITCH_AP] = 'Internet'             
    # step3 let's set the switch connected to the default gateway uplink to the default gateway and hardcode port to 1 for now:
    #device_data_bymac[first_switch][SWITCH_AP]=default_router_mac                
    #device_data_bymac[first_switch][SWITCH_AP][PORT_SSID] = '1'                
    # step4, let's go recursively through switches other links to mark update their uplinks
    #  and pray it ends one day... 
    # 
    add_uplink(default_router_mac,first_switch, device_data_bymac,sadevices_linksbymac,port_byswitchmac_byclientmac)                       
    return device_data_bymac.values()

if __name__ == '__main__':
    main()
