#!/usr/bin/env python
# Based on the work of https://github.com/leiweibau/Pi.Alert

# /home/pi/pialert/front/plugins/website_monitoring/script.py urls=http://google.com,http://bing.com
from __future__ import unicode_literals
from time import sleep, time, strftime
import requests
import pathlib

import argparse
import io
#import smtplib
import sys
#from smtp_config import sender, password, receivers, host, port
from requests.packages.urllib3.exceptions import InsecureRequestWarning

import pwd
import os

curPath = str(pathlib.Path(__file__).parent.resolve())
log_file = curPath + '/script.log'
last_run = curPath + '/last_result.log'

print(last_run)

# Workflow

def main():      
    parser = argparse.ArgumentParser(description='Simple URL monitoring tool')
    parser.add_argument('urls',  action="store",  help="urls to check separated by ','")  
    values = parser.parse_args()

    if values.urls:
        with open(last_run, 'w') as last_run_logfile:
            # empty file
            last_run_logfile.write("")
            service_monitoring(values.urls.split('=')[1].split(','))        
    else:
        return

# -----------------------------------------------------------------------------
def service_monitoring_log(site, status, latency):
    # global monitor_logfile

    # Log status message to log file
    with open(log_file, 'a') as monitor_logfile:
        monitor_logfile.write("{} | {} | {} | {}\n".format(strftime("%Y-%m-%d %H:%M:%S"),
                                                site,
                                                status,
                                                latency,
                                                )
                             )
    with open(last_run, 'a') as last_run_logfile:
        # https://www.duckduckgo.com|192.168.0.1|2023-01-02 15:56:30|200|0.9898|null|null|Best search engine
        last_run_logfile.write("{}|{}|{}|{}|{}|{}|{}|{}\n".format(
                                                site,
                                                'null',
                                                strftime("%Y-%m-%d %H:%M:%S"),                                                
                                                status,
                                                latency,
                                                'null',
                                                'null',
                                                'null',
                                                )
                             )
        



# -----------------------------------------------------------------------------
def check_services_health(site):
    # Enable self signed SSL
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    """Send GET request to input site and return status code"""
    try:
        resp = requests.get(site, verify=False, timeout=10)
        latency = resp.elapsed
        latency_str = str(latency)
        latency_str_seconds = latency_str.split(":")
        format_latency_str = latency_str_seconds[2]
        if format_latency_str[0] == "0" and format_latency_str[1] != "." :
            format_latency_str = format_latency_str[1:]
        return resp.status_code, format_latency_str
    except requests.exceptions.SSLError:
        pass
    except:
        latency = "99999"
        return 503, latency

# ----------------------------------------------------------------------------- 
def get_username():

    return pwd.getpwuid(os.getuid())[0]


# -----------------------------------------------------------------------------
def service_monitoring(urls):
    
    # Empty Log and write new header
    print("Prepare Services Monitoring")
    print("... Prepare Logfile")
    with open(log_file, 'w') as monitor_logfile:
        monitor_logfile.write("Pi.Alert [Prototype]:\n---------------------------------------------------------\n")
        monitor_logfile.write("Current User: %s \n\n" % get_username())
        monitor_logfile.write("Monitor Web-Services\n")
        monitor_logfile.write("Timestamp: " + strftime("%Y-%m-%d %H:%M:%S") + "\n")
        monitor_logfile.close()

    print("... Get Services List")
    sites = urls


    print("Start Services Monitoring")
    with open(log_file, 'a') as monitor_logfile:
        monitor_logfile.write("\nStart Services Monitoring\n\n| Timestamp | URL | StatusCode | ResponseTime |\n-----------------------------------------------\n") 
        monitor_logfile.close()

    while sites:
        for site in sites:
            status,latency = check_services_health(site)
            scantime = strftime("%Y-%m-%d %H:%M:%S")

            # Debugging 
            # print("{} - {} STATUS: {} ResponseTime: {}".format(strftime("%Y-%m-%d %H:%M:%S"),
            #                     site,
            #                     status,
            #                     latency)
            #      )

            # Write Logfile
            service_monitoring_log(site, status, latency)

            sys.stdout.flush()

        break

    else:
        with open(log_file, 'a') as monitor_logfile:
            monitor_logfile.write("\n\nNo site(s) to monitor!")
            monitor_logfile.close()

#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    sys.exit(main())       

