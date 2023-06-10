import re
import subprocess

from logger import mylog

#-------------------------------------------------------------------------------
def execute_arpscan (userSubnets):

    # output of possible multiple interfaces
    arpscan_output = ""

    # scan each interface
    for interface in userSubnets :            
        arpscan_output += execute_arpscan_on_interface (interface)    
    
    # Search IP + MAC + Vendor as regular expresion
    re_ip = r'(?P<ip>((2[0-5]|1[0-9]|[0-9])?[0-9]\.){3}((2[0-5]|1[0-9]|[0-9])?[0-9]))'
    re_mac = r'(?P<mac>([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2}))'
    re_hw = r'(?P<hw>.*)'
    re_pattern = re.compile (re_ip + '\s+' + re_mac + '\s' + re_hw)

    # Create Userdict of devices
    devices_list = [device.groupdict()
        for device in re.finditer (re_pattern, arpscan_output)]
    
    # Delete duplicate MAC
    unique_mac = [] 
    unique_devices = [] 

    for device in devices_list :
        if device['mac'] not in unique_mac: 
            unique_mac.append(device['mac'])
            unique_devices.append(device)    

    # return list
    mylog('debug', ['[ARP Scan] Completed found ', len(unique_devices) ,' devices ' ])    
    return unique_devices

#-------------------------------------------------------------------------------
def execute_arpscan_on_interface (interface):    
    # Prepare command arguments
    subnets = interface.strip().split()
    # Retry is 6 to avoid false offline devices
    mylog('debug', ['[ARP Scan] - arpscan command: sudo arp-scan --ignoredups --retry=6 ', str(subnets)])
    arpscan_args = ['sudo', 'arp-scan', '--ignoredups', '--retry=6'] + subnets

    # Execute command
    try:
        # try runnning a subprocess
        result = subprocess.check_output (arpscan_args, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        mylog('none', ['[ARP Scan]', e.output])
        result = ""

    mylog('debug', ['[ARP Scan] on Interface Completed with results: ', result])
    return result
