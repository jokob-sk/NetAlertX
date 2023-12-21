#---------------------------------------------------------------------------------#
#  Pi.Alert                                                                       #
#  Open Source Network Guard / WIFI & LAN intrusion detector                      #  
#                                                                                 #
#  reporting.py - Pialert Back module. Template to email reporting in HTML format #
#---------------------------------------------------------------------------------#
#    Puche      2021        pi.alert.application@gmail.com   GNU GPLv3            #
#    jokob-sk   2022        jokob.sk@gmail.com               GNU GPLv3            #
#    leiweibau  2022        https://github.com/leiweibau     GNU GPLv3            #
#    cvc90      2023        https://github.com/cvc90         GNU GPLv3            #
#---------------------------------------------------------------------------------#

import datetime
import json

# pialert modules
import conf
import const
from const import pialertPath, logPath, apiPath
from helper import timeNowTZ, get_file_content, write_file, get_timezone_offset, get_setting_value
from logger import logResult, mylog, print_log


#===============================================================================
# REPORTING
#===============================================================================


#-------------------------------------------------------------------------------
def get_notifications (db):

    sql = db.sql  #TO-DO
    
    # Reporting section
    mylog('verbose', ['[Notification] Check if something to report'])

    # prepare variables for JSON construction    
    json_new_devices = []
    json_new_devices_meta = {}
    json_down_devices = []
    json_down_devices_meta = {}
    json_events = []    
    json_events_meta = {}
    json_plugins = []
    json_plugins_meta = {}

    # Disable reporting on events for devices where reporting is disabled based on the MAC address
    sql.execute ("""UPDATE Events SET eve_PendingAlertEmail = 0
                    WHERE eve_PendingAlertEmail = 1 AND eve_EventType != 'Device Down' AND eve_MAC IN
                        (
                            SELECT dev_MAC FROM Devices WHERE dev_AlertEvents = 0
						)""")
    sql.execute ("""UPDATE Events SET eve_PendingAlertEmail = 0
                    WHERE eve_PendingAlertEmail = 1 AND eve_EventType = 'Device Down' AND eve_MAC IN
                        (
                            SELECT dev_MAC FROM Devices WHERE dev_AlertDeviceDown = 0
						)""")

	
    mylog('verbose', ['[Notification] included sections: ', conf.INCLUDED_SECTIONS ])

    if 'new_devices' in conf.INCLUDED_SECTIONS:
        # Compose New Devices Section
        sqlQuery = """SELECT eve_MAC as MAC, eve_DateTime as Datetime, dev_LastIP as IP, eve_EventType as "Event Type", dev_Name as "Device name", dev_Comments as Comments  FROM Events_Devices
                        WHERE eve_PendingAlertEmail = 1
                        AND eve_EventType = 'New Device'
                        ORDER BY eve_DateTime"""   

        # Get the events as JSON
        json_obj = db.get_table_as_json(sqlQuery)

        json_new_devices_meta = {
            "title": "New devices",
            "columnNames": json_obj.columnNames
        }
        json_new_devices = json_obj.json["data"]    

    if 'down_devices' in conf.INCLUDED_SECTIONS:
        # Compose Devices Down Section 
        # - select only Down Alerts with pending email of devices that didn't reconnect within the specified time window
        sqlQuery = f"""
                    SELECT *
                        FROM Events AS down_events
                        WHERE eve_PendingAlertEmail = 1 
                        AND down_events.eve_EventType = 'Device Down' 
                        AND eve_DateTime < datetime('now', '-{get_setting_value('NTFPRCS_alert_down_time')} minutes', '{get_timezone_offset()}')
                        AND NOT EXISTS (
                            SELECT 1
                            FROM Events AS connected_events
                            WHERE connected_events.eve_MAC = down_events.eve_MAC
                                AND connected_events.eve_EventType = 'Connected'
                                AND connected_events.eve_DateTime > down_events.eve_DateTime        
                        )
                        ORDER BY down_events.eve_DateTime;
                    """
        
        # Get the events as JSON        
        json_obj = db.get_table_as_json(sqlQuery)

        json_down_devices_meta = {
            "title": "Down devices",
            "columnNames": json_obj.columnNames
        }
        json_down_devices = json_obj.json["data"]     

    if 'events' in conf.INCLUDED_SECTIONS:
        # Compose Events Section
        sqlQuery = """SELECT eve_MAC as MAC, eve_DateTime as Datetime, dev_LastIP as IP, eve_EventType as "Event Type", dev_Name as "Device name", dev_Comments as Comments  FROM Events_Devices
                        WHERE eve_PendingAlertEmail = 1
                        AND eve_EventType IN ('Connected','Disconnected',
                            'IP Changed')
                        ORDER BY eve_DateTime"""        
        
        # Get the events as JSON        
        json_obj = db.get_table_as_json(sqlQuery)

        json_events_meta = {
            "title": "Events",
            "columnNames": json_obj.columnNames
        }
        json_events = json_obj.json["data"]     

    if 'plugins' in conf.INCLUDED_SECTIONS:
        # Compose Plugins Section
        sqlQuery = """SELECT Plugin, Object_PrimaryId, Object_SecondaryId, DateTimeChanged, Watched_Value1, Watched_Value2, Watched_Value3, Watched_Value4, Status from Plugins_Events"""        
        
        # Get the events as JSON        
        json_obj = db.get_table_as_json(sqlQuery)

        json_plugins_meta = {
            "title": "Plugins",
            "columnNames": json_obj.columnNames
        }
        json_plugins = json_obj.json["data"]   


    final_json = {                    
                    "new_devices": json_new_devices,
                    "new_devices_meta": json_new_devices_meta,
                    "down_devices": json_down_devices,
                    "down_devices_meta": json_down_devices_meta,
                    "events": json_events,                    
                    "events_meta": json_events_meta,                    
                    "plugins": json_plugins,
                    "plugins_meta": json_plugins_meta,
                }

    return final_json



#-------------------------------------------------------------------------------
def skip_repeated_notifications (db):

    # Skip repeated notifications
    # due strfime : Overflow --> use  "strftime / 60"
    mylog('verbose','[Skip Repeated Notifications] Skip Repeated')
    
    db.sql.execute ("""UPDATE Events SET eve_PendingAlertEmail = 0
                    WHERE eve_PendingAlertEmail = 1 AND eve_MAC IN
                        (
                        SELECT dev_MAC FROM Devices
                        WHERE dev_LastNotification IS NOT NULL
                          AND dev_LastNotification <>""
                          AND (strftime("%s", dev_LastNotification)/60 +
                                dev_SkipRepeated * 60) >
                              (strftime('%s','now','localtime')/60 )
                        )
                 """ )
   

    db.commitDB()





