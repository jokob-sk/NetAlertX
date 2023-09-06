#!/usr/bin/env python
# test script by running python script.py devices=test,dummy

import os
import pathlib
import argparse
import sys
import hashlib
import csv
from io import StringIO

sys.path.append("/home/pi/pialert/front/plugins")
sys.path.append('/home/pi/pialert/pialert') 

import database
from plugin_helper import Plugin_Object, Plugin_Objects, decodeBase64
from logger import mylog, append_line_to_file
from helper import timeNowTZ
from const import logPath, pialertPath


CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
LOG_FILE = os.path.join(CUR_PATH, 'script.log')
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

def main():

    # the script expects a parameter in the format of devices=device1,device2,...
    parser = argparse.ArgumentParser(description='TBC')
    parser.add_argument('location',  action="store",  help="TBC")
    parser.add_argument('overwrite',  action="store",  help="TBC")
    values = parser.parse_args()

    mylog('verbose', ['[CSVBCKP] In script'])     

    # plugin_objects = Plugin_Objects( RESULT_FILE )

    # if values.devices:
    #     for fake_dev in values.devices.split('=')[1].split(','):

    #         fake_mac = string_to_mac_hash(fake_dev)

    #         plugin_objects.add_object(
    #             primaryId=fake_dev,    # MAC (Device Name)
    #             secondaryId="0.0.0.0", # IP Address (always 0.0.0.0)
    #             watched1=fake_dev,     # Device Name
    #             watched2="",
    #             watched3="",
    #             watched4="",
    #             extra="",
    #             foreignKey=fake_mac)

    # plugin_objects.write_result_file()

    # # Execute your SQL query
    # cursor.execute("SELECT * FROM Devices")

    # # Get column names
    # columns = [desc[0] for desc in cursor.description]

    # # Initialize the CSV writer
    # csv_writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # # Write the header row
    # csv_writer.writerow(columns)

    # # Fetch and write data rows
    # for row in cursor.fetchall():
    #     csv_writer.writerow(row)

    # # Close the database connection
    # conn.close()

    # # Prepare the CSV data for download
    # csv_data = output.getvalue()

    return 0


#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    main()