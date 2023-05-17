#!/usr/bin/env python
# test script by running python script.py devices=test,dummy

import os
import pathlib
import argparse

from plugin_helper import Plugin_Objects

curPath = str(pathlib.Path(__file__).parent.resolve())
log_file = os.path.join(curPath , 'script.log')
result_file = os.path.join(curPath , 'last_result.log')



def main():

  parser = argparse.ArgumentParser(description='Import devices from dhcp.leases files')
  parser.add_argument('devices',  action="store",  help="absolute dhcp.leases file paths to check separated by ','")  
  values = parser.parse_args()

  undis_devices = Plugin_Objects( result_file )
  
  if values.devices:
        for fake_dev in values.devices.split('=')[1].split(','):
            undis_devices.add_object(
                primaryId=fake_dev,    # MAC 
                secondaryId="0.0.0.0", # IP Address 
                watched1=fake_dev,     # Device Name
                watched2="",
                watched3="",
                watched4="UNDIS",      # used as ScanMethod
                extra="1",             # used as dummy ScanCycle
                foreignKey="")

  undis_devices.write_result_file()

  return 0
    

#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    main()