#!/usr/bin/env python
# Based on the work of https://github.com/leiweibau/Pi.Alert

# python3 /home/pi/pialert/front/plugins/website_monitor/script.py urls=http://google.com,http://bing.com

import sys
import pathlib

from plugin_helper import Plugin_Objects, Plugin_Object

sys.dont_write_bytecode = True

curPath = str(pathlib.Path(__file__).parent.resolve())
log_file = curPath + '/script.log'
result_file = curPath + '\last_result.log'

FAKE_DEVICES = ["routerXX","hubZZ"]


def main():
  print("Hello")

  devices = Plugin_Objects( result_file )
  

  for fake_dev in FAKE_DEVICES:
    devices.add_object(fake_dev, fake_dev, fake_dev, fake_dev, "", "", "", "")

  devices.write_result_file()

  return devices
    

#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    d = main()