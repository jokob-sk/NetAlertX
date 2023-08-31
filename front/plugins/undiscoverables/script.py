#!/usr/bin/env python
# test script by running python script.py devices=test,dummy

import os
import pathlib
import argparse
import sys

sys.path.append("/home/pi/pialert/front/plugins")
sys.path.append('/home/pi/pialert/pialert') 

from plugin_helper import Plugin_Object, Plugin_Objects, decodeBase64
from logger import mylog, append_line_to_file
from helper import timeNowTZ
from const import logPath, pialertPath

CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
LOG_FILE = os.path.join(CUR_PATH, 'script.log')
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

def main():

    # the script expects a parameter in the format of devices=device1,device2,...
    parser = argparse.ArgumentParser(description='Import devices from settings')
    parser.add_argument('devices',  action="store",  help="list of device names separated by ','")
    values = parser.parse_args()

    mylog('verbose', ['[UNDIS] In script'])     

    UNDIS_devices = Plugin_Objects( RESULT_FILE )

    if values.devices:
        for fake_dev in values.devices.split('=')[1].split(','):
            UNDIS_devices.add_object(
                primaryId=fake_dev,    # MAC (Device Name)
                secondaryId="0.0.0.0", # IP Address (always 0.0.0.0)
                watched1=fake_dev,     # Device Name
                watched2="",
                watched3="",
                watched4="",
                extra="",
                foreignKey="")

    UNDIS_devices.write_result_file()

    return 0

#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    main()