import re
import subprocess
import conf

from logger import mylog
from helper import write_file
from const import logPath

#-------------------------------------------------------------------------------
def execute_arpscan (userSubnets):

    # output of possible multiple interfaces
    arpscan_output = ""

    # scan each interface
    index = 0
    for interface in userSubnets :   
        arpscan_output += execute_arpscan_on_interface (interface)    
        index += 1         
    
    # Search IP + MAC + Vendor as regular expresion
    re_ip = r'(?P<ip>((2[0-5]|1[0-9]|[0-9])?[0-9]\.){3}((2[0-5]|1[0-9]|[0-9])?[0-9]))'
    re_mac = r'(?P<mac>([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2}))'
    re_hw = r'(?P<hw>.*)'
    re_pattern = re.compile (re_ip + '\s+' + re_mac + '\s' + re_hw)

    # Create Userdict of devices
    devices_list = [device.groupdict()
        for device in re.finditer (re_pattern, arpscan_output)]

    mylog('debug', ['[ARP Scan] Found: Devices including duplicates ', len(devices_list) ]) 
    
    # Delete duplicate MAC
    unique_mac = [] 
    unique_devices = [] 

    for device in devices_list :
        if device['mac'] not in unique_mac: 
            unique_mac.append(device['mac'])
            unique_devices.append(device)    

    # return list
    mylog('debug', ['[ARP Scan] Found: Devices without duplicates ', len(unique_devices)  ]) 

    return unique_devices

#-------------------------------------------------------------------------------
def execute_arpscan_on_interface (interface):    
    # Prepare command arguments
    subnets = interface.strip().split()
    # Retry is 6 to avoid false offline devices
    mylog('debug', ['[ARP Scan] - arpscan command: sudo arp-scan --ignoredups --retry=6 ', str(subnets)])
    arpscan_args = ['sudo', 'arp-scan', '--ignoredups', '--retry=6'] + subnets

    # Execute command
    if conf.LOG_LEVEL == 'debug':
        # try runnning a subprocess
        result = subprocess.check_output (arpscan_args, universal_newlines=True)
    else:
        try:
            # try runnning a subprocess safely
            result = subprocess.check_output (arpscan_args, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            # An error occured, handle it
            error_type = type(e).__name__  # Capture the error type

            mylog('none', [f'[ARP Scan] Error type  : {error_type}'])
            mylog('none', [f'[ARP Scan] Error output: {e.output}'])

            result = ""

    mylog('debug', ['[ARP Scan] on Interface Completed with results: ', result])
    return result
