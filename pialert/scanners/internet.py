""" internet related functions to support Pi.Alert """

import subprocess
import re

# pialert modules

import conf
from helper import timeNowTZ, updateState
from logger import append_line_to_file, mylog
from const import logPath


# need to find a better way to deal with settings !
#global DDNS_ACTIVE, DDNS_DOMAIN, DDNS_UPDATE_URL, DDNS_USER, DDNS_PASSWORD 


#===============================================================================
# INTERNET IP CHANGE
#===============================================================================
def check_internet_IP ( db ):   

    # Header
    updateState(db,"Scan: Internet IP")
    mylog('verbose', ['[Internet IP] Check Internet IP started'])    

    # Get Internet IP
    mylog('verbose', ['[Internet IP] - Retrieving Internet IP'])
    internet_IP = get_internet_IP(conf.DIG_GET_IP_ARG)
    # TESTING - Force IP
        # internet_IP = "1.2.3.4"

    # Check result = IP
    if internet_IP == "" :
        mylog('none', ['[Internet IP]    Error retrieving Internet IP'])
        mylog('none', ['[Internet IP]    Exiting...'])
        return False
    mylog('verbose', ['[Internet IP] IP:      ', internet_IP])

    # Get previous stored IP
    mylog('verbose', ['[Internet IP]    Retrieving previous IP:'])    
    previous_IP = get_previous_internet_IP (db)
    mylog('verbose', ['[Internet IP]      ', previous_IP])

    # Check IP Change
    if internet_IP != previous_IP :
        mylog('minimal', ['[Internet IP]    New internet IP: ', internet_IP])
        save_new_internet_IP (db, internet_IP)
        
    else :
        mylog('verbose', ['[Internet IP]    No changes to perform'])    

    # Get Dynamic DNS IP
    if conf.DDNS_ACTIVE :
        mylog('verbose', ['[DDNS]    Retrieving Dynamic DNS IP'])
        dns_IP = get_dynamic_DNS_IP()

        # Check Dynamic DNS IP
        if dns_IP == "" or dns_IP == "0.0.0.0" :
            mylog('none', ['[DDNS]     Error retrieving Dynamic DNS IP'])            
        mylog('none', ['[DDNS]    ', dns_IP])

        # Check DNS Change
        if dns_IP != internet_IP :
            mylog('none', ['[DDNS]     Updating Dynamic DNS IP'])
            message = set_dynamic_DNS_IP ()
            mylog('none', ['[DDNS]        ', message])            
        else :
            mylog('verbose', ['[DDNS]     No changes to perform'])
    else :
        mylog('verbose', ['[DDNS]     Skipping Dynamic DNS update'])



#-------------------------------------------------------------------------------
def get_internet_IP (DIG_GET_IP_ARG):
    # BUGFIX #46 - curl http://ipv4.icanhazip.com repeatedly is very slow
    # Using 'dig'
    dig_args = ['dig', '+short'] + DIG_GET_IP_ARG.strip().split()
    try:
        cmd_output = subprocess.check_output (dig_args, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        mylog('none', [e.output])
        cmd_output = '' # no internet

    # Check result is an IP
    IP = check_IP_format (cmd_output)

    # Handle invalid response
    if IP == '':
        IP = '0.0.0.0'

    return IP

#-------------------------------------------------------------------------------
def get_previous_internet_IP (db):
    
    previous_IP = '0.0.0.0'

    # get previous internet IP stored in DB
    db.sql.execute ("SELECT dev_LastIP FROM Devices WHERE dev_MAC = 'Internet' ")
    result = db.sql.fetchone()

    db.commitDB()

    if  result is not None and len(result) > 0 :
        previous_IP = result[0]

    # return previous IP
    return previous_IP



#-------------------------------------------------------------------------------
def save_new_internet_IP (db, pNewIP):
    # Log new IP into logfile
    append_line_to_file (logPath + '/IP_changes.log',
        '['+str(timeNowTZ()) +']\t'+ pNewIP +'\n')

    prevIp = get_previous_internet_IP(db)     
    # Save event
    db.sql.execute ("""INSERT INTO Events (eve_MAC, eve_IP, eve_DateTime,
                        eve_EventType, eve_AdditionalInfo,
                        eve_PendingAlertEmail)
                    VALUES ('Internet', ?, ?, 'Internet IP Changed',
                        'Previous Internet IP: '|| ?, 1) """,
                    (pNewIP, timeNowTZ(), prevIp) )

    # Save new IP
    db.sql.execute ("""UPDATE Devices SET dev_LastIP = ?
                    WHERE dev_MAC = 'Internet' """,
                    (pNewIP,) )

    # commit changes    
    db.commitDB()
    
#-------------------------------------------------------------------------------
def check_IP_format (pIP):
    # Check IP format
    IPv4SEG  = r'(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])'
    IPv4ADDR = r'(?:(?:' + IPv4SEG + r'\.){3,3}' + IPv4SEG + r')'
    IP = re.search(IPv4ADDR, pIP)

    # Return error if not IP
    if IP is None :
        return ""

    # Return IP
    return IP.group(0)



#-------------------------------------------------------------------------------
def get_dynamic_DNS_IP ():
    # Using OpenDNS server
        # dig_args = ['dig', '+short', DDNS_DOMAIN, '@resolver1.opendns.com']

    # Using default DNS server
    dig_args = ['dig', '+short', conf.DDNS_DOMAIN]

    try:
        # try runnning a subprocess
        dig_output = subprocess.check_output (dig_args, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        mylog('none', ['[DDNS] ERROR - ', e.output])
        dig_output = '' # probably no internet

    # Check result is an IP
    IP = check_IP_format (dig_output)

    # Handle invalid response
    if IP == '':
        IP = '0.0.0.0'

    return IP

#-------------------------------------------------------------------------------
def set_dynamic_DNS_IP ():
    try:
        # try runnning a subprocess
        # Update Dynamic IP
        curl_output = subprocess.check_output (['curl', '-s',
            conf.DDNS_UPDATE_URL +
            'username='  + conf.DDNS_USER +
            '&password=' + conf.DDNS_PASSWORD +
            '&hostname=' + conf.DDNS_DOMAIN],
            universal_newlines=True)
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        mylog('none', ['[DDNS] ERROR - ',e.output])
        curl_output = ""    
    
    return curl_output
