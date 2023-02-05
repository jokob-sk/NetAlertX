#!/usr/bin/env python
from __future__ import unicode_literals
from time import sleep, time, strftime
import requests
import io
#import smtplib
import sys
#from smtp_config import sender, password, receivers, host, port
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import sqlite3
import pwd
import os

con = sqlite3.connect("monitoring.db")
cur = con.cursor()

#DELAY = 60  # Delay between site queries
EMAIL_INTERVAL = 1800  # Delay between alert emails

last_email_time = {}  # Monitored sites and timestamp of last alert sent

# Message template for alert
MESSAGE = """From: {sender}
To: {receivers}
Subject: Monitor Service Notification

You are being notified that {site} is experiencing a {status} status!
"""

# Workflow

def main():
    global cur
    global con

    prepare_service_monitoring_env()
    service_monitoring()
    print_service_monitoring_changes()
    # prepare_service_monitoring_notification()

# -----------------------------------------------------------------------------
def prepare_service_monitoring_env ():
    global con
    global cur

    sql_create_table = """ CREATE TABLE IF NOT EXISTS Services_Events(
                                moneve_URL TEXT NOT NULL,
                                moneve_DateTime TEXT NOT NULL,
                                moneve_StatusCode NUMERIC NOT NULL,
                                moneve_Latency TEXT NOT NULL
                            ); """
    cur.execute(sql_create_table)

    sql_create_table = """ CREATE TABLE IF NOT EXISTS Services_CurrentScan(
                                cur_URL TEXT NOT NULL,
                                cur_DateTime TEXT NOT NULL,
                                cur_StatusCode NUMERIC NOT NULL,
                                cur_Latency TEXT NOT NULL,
                                cur_AlertEvents INTEGER DEFAULT 0,
                                cur_AlertDown INTEGER DEFAULT 0,
                                cur_StatusChanged INTEGER DEFAULT 0,
                                cur_LatencyChanged INTEGER DEFAULT 0
                            ); """
    cur.execute(sql_create_table)

    sql_create_table = """  CREATE TABLE IF NOT EXISTS Services(
                                mon_URL TEXT NOT NULL,
                                mon_MAC TEXT,
                                mon_LastStatus NUMERIC NOT NULL,
                                mon_LastLatency TEXT NOT NULL,
                                mon_LastScan TEXT NOT NULL,
                                mon_Tags TEXT,
                                mon_AlertEvents INTEGER DEFAULT 0,
                                mon_AlertDown INTEGER DEFAULT 0,
                                PRIMARY KEY(mon_URL)
                            ); """
    cur.execute(sql_create_table)

# Update Service with lastLatence, lastScan and lastStatus
# -----------------------------------------------------------------------------
def set_service_update(_mon_URL, _mon_lastScan, _mon_lastStatus, _mon_lastLatence,):
    global con
    global cur

    sqlite_insert = """UPDATE Services SET mon_LastScan=?, mon_LastStatus=?, mon_LastLatency=? WHERE mon_URL=?;"""

    table_data = (_mon_lastScan, _mon_lastStatus, _mon_lastLatence, _mon_URL)
    cur.execute(sqlite_insert, table_data)
    con.commit()

# Insert Services_Events with moneve_URL, moneve_DateTime, moneve_StatusCode and moneve_Latency
# -----------------------------------------------------------------------------
def set_services_events(_moneve_URL, _moneve_DateTime, _moneve_StatusCode, _moneve_Latency):
    global con
    global cur

    sqlite_insert = """INSERT INTO Services_Events
                     (moneve_URL, moneve_DateTime, moneve_StatusCode, moneve_Latency) 
                     VALUES (?, ?, ?, ?);"""

    table_data = (_moneve_URL, _moneve_DateTime, _moneve_StatusCode, _moneve_Latency)
    cur.execute(sqlite_insert, table_data)
    con.commit()

# Insert Services_Events with moneve_URL, moneve_DateTime, moneve_StatusCode and moneve_Latency
# -----------------------------------------------------------------------------
def set_services_current_scan(_cur_URL, _cur_DateTime, _cur_StatusCode, _cur_Latency):
    global con
    global cur

    cur.execute("SELECT * FROM Services WHERE mon_URL = ?", [_cur_URL])
    rows = cur.fetchall()
    for row in rows:
        _mon_AlertEvents = row[6]
        _mon_AlertDown = row[7]
        _mon_StatusCode = row[2]
        _mon_Latency = row[3]

    if _mon_StatusCode != _cur_StatusCode:
        _cur_StatusChanged = 1
    else:
        _cur_StatusChanged = 0

    if _mon_Latency == "99999" and _mon_Latency != _cur_Latency:
        _cur_LatencyChanged = 1
    elif _cur_Latency == "99999" and _mon_Latency != _cur_Latency:
        _cur_LatencyChanged = 1
    else:
        _cur_LatencyChanged = 0

    sqlite_insert = """INSERT INTO Services_CurrentScan
                     (cur_URL, cur_DateTime, cur_StatusCode, cur_Latency, cur_AlertEvents, cur_AlertDown, cur_StatusChanged, cur_LatencyChanged) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?);"""

    table_data = (_cur_URL, _cur_DateTime, _cur_StatusCode, _cur_Latency, _mon_AlertEvents, _mon_AlertDown, _cur_StatusChanged, _cur_LatencyChanged)
    cur.execute(sqlite_insert, table_data)
    con.commit()

# -----------------------------------------------------------------------------
def service_monitoring_log(site, status, latency):
    # global monitor_logfile

    # Log status message to log file
    with open('monitor.log', 'a') as monitor_logfile:
        monitor_logfile.write("{} | {} | {} | {}\n".format(strftime("%Y-%m-%d %H:%M:%S"),
                                                site,
                                                status,
                                                latency,
                                                )
                             )

# -----------------------------------------------------------------------------
def send_alert(site, status):
    """If more than EMAIL_INTERVAL seconds since last email, resend email"""
    if (time() - last_email_time[site]) > EMAIL_INTERVAL:
        try:
            smtpObj = smtplib.SMTP(host, port)  # Set up SMTP object
            smtpObj.starttls()
            smtpObj.login(sender, password)
            smtpObj.sendmail(sender,
                             receivers,
                             MESSAGE.format(sender=sender,
                                            receivers=", ".join(receivers),
                                            site=site,
                                            status=status
                                            )
                             )
            last_email_time[site] = time()  # Update time of last email
            print("Successfully sent email")
        except smtplib.SMTPException:
            print("Error sending email ({}:{})".format(host, port))

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

# ----------------------------------------------------------------------------- Duplicat
def get_username():

    return pwd.getpwuid(os.getuid())[0]

# -----------------------------------------------------------------------------
def get_services_list():
    global cur
    global con

    with open('monitor.log', 'a') as monitor_logfile:
        monitor_logfile.write("... Get Services List\n")
        monitor_logfile.close()

    cur.execute("SELECT mon_URL FROM Services")
    rows = cur.fetchall()

    sites = []
    for row in rows:
        sites.append(row[0])

    return sites

# -----------------------------------------------------------------------------
def flush_services_current_scan():
    global cur
    global con

    with open('monitor.log', 'a') as monitor_logfile:
        monitor_logfile.write("... Flush previous scan results\n")
        monitor_logfile.close()

    cur.execute("DELETE FROM Services_CurrentScan")
    con.commit()

# -----------------------------------------------------------------------------
def print_service_monitoring_changes():
    global cur
    global con    

    print("Services Monitoring Changes")
    changedStatusCode = cur.execute("SELECT COUNT() FROM Services_CurrentScan WHERE cur_StatusChanged = 1").fetchone()[0]
    print("... Changed StatusCodes: ", str(changedStatusCode))
    changedLatency = cur.execute("SELECT COUNT() FROM Services_CurrentScan WHERE cur_LatencyChanged = 1").fetchone()[0]
    print("... Changed Reachability: ", str(changedLatency))
    with open('monitor.log', 'a') as monitor_logfile:
        monitor_logfile.write("\nServices Monitoring Changes:\n")
        monitor_logfile.write("... Changed StatusCodes: " + str(changedStatusCode))
        monitor_logfile.write("\n... Changed Reachability: " + str(changedLatency))
        monitor_logfile.write("\n")
        monitor_logfile.close()

# -----------------------------------------------------------------------------
# def prepare_service_monitoring_notification():
#     global cur
#     global con


# -----------------------------------------------------------------------------
def service_monitoring():
    global cur
    global con
    
    # Empty Log and write new header
    print("Prepare Services Monitoring")
    print("... Prepare Logfile")
    with open('monitor.log', 'w') as monitor_logfile:
        monitor_logfile.write("Pi.Alert [Prototype]:\n---------------------------------------------------------\n")
        monitor_logfile.write("Current User: %s \n\n" % get_username())
        monitor_logfile.write("Monitor Web-Services\n")
        monitor_logfile.write("Timestamp: " + strftime("%Y-%m-%d %H:%M:%S") + "\n")
        monitor_logfile.close()

    print("... Get Services List")
    sites = get_services_list()

    print("... Flush previous scan results")
    flush_services_current_scan()

    print("Start Services Monitoring")
    with open('monitor.log', 'a') as monitor_logfile:
        monitor_logfile.write("\nStart Services Monitoring\n\n| Timestamp | URL | StatusCode | ResponseTime |\n-----------------------------------------------\n") 
        monitor_logfile.close()

    for site in sites:
        last_email_time[site] = 0  # Initialize timestamp as 0

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
            # Insert Services_Events with moneve_URL, moneve_DateTime, moneve_StatusCode and moneve_Latency
            set_services_events(site, scantime, status, latency)
            # Insert Services_CurrentScan with moneve_URL, moneve_DateTime, moneve_StatusCode and moneve_Latency
            set_services_current_scan(site, scantime, status, latency)

            sys.stdout.flush()

            # Update Service with lastLatence, lastScan and lastStatus after compare with services_current_scan
            set_service_update(site, scantime, status, latency)

        break

    else:
        with open('monitor.log', 'a') as monitor_logfile:
            monitor_logfile.write("\n\nNo site(s) to monitor!")
            monitor_logfile.close()

#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    sys.exit(main())       

