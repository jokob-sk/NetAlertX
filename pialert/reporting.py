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
import socket
import subprocess
import requests
from json2table import convert

# pialert modules
import conf
import const
from const import pialertPath, logPath, apiPath
from helper import noti_obj, generate_mac_links, removeDuplicateNewLines, timeNowTZ, hide_email,  updateState, get_file_content, write_file
from logger import logResult, mylog, print_log

from publishers.ntfy  import (check_config as ntfy_check_config,
                              send as send_ntfy )
from publishers.webhook import (check_config as webhook_check_config,
                                send as send_webhook) 
from publishers.pushsafer import (check_config as pushsafer_check_config,
                                send as send_pushsafer) 
from publishers.mqtt import (check_config as mqtt_check_config,
                             mqtt_start )


#===============================================================================
# REPORTING
#===============================================================================
# create a json of the notifications to provide further integration options (e.g. used in webhook, mqtt notifications)


json_final = []


#-------------------------------------------------------------------------------
def construct_notifications(db, sqlQuery, tableTitle, skipText = False, suppliedJsonStruct = None):

    if suppliedJsonStruct is None and sqlQuery == "":
        return noti_obj("", "", "")

    table_attributes = {"style" : "border-collapse: collapse; font-size: 12px; color:#70707", "width" : "100%", "cellspacing" : 0, "cellpadding" : "3px", "bordercolor" : "#C0C0C0", "border":"1"}
    headerProps = "width='120px' style='color:white; font-size: 16px;' bgcolor='#64a0d6' "
    thProps = "width='120px' style='color:#F0F0F0' bgcolor='#64a0d6' "

    build_direction = "TOP_TO_BOTTOM"
    text_line = '{}\t{}\n'

    if suppliedJsonStruct is None:
        json_obj = db.get_table_as_json(sqlQuery)
    else:
        json_obj = suppliedJsonStruct

    jsn  = json_obj.json
    html = ""
    text = ""

    if len(jsn["data"]) > 0:
        text = tableTitle + "\n---------\n"

        # Convert a JSON into an HTML table
        html = convert(jsn, build_direction=build_direction, table_attributes=table_attributes)
        
        # Cleanup the generated HTML table notification
        html = format_table(html, "data", headerProps, tableTitle).replace('<ul>','<ul style="list-style:none;padding-left:0">').replace("<td>null</td>", "<td></td>")

        headers = json_obj.columnNames

        # prepare text-only message
        if skipText == False:

            for device in jsn["data"]:
                for header in headers:
                    padding = ""
                    if len(header) < 4:
                        padding = "\t"
                    text += text_line.format ( header + ': ' + padding, device[header])
                text += '\n'

        #  Format HTML table headers
        for header in headers:
            html = format_table(html, header, thProps)

    notiStruc = noti_obj(jsn, text, html)

    
    if not notiStruc.json['data'] and not notiStruc.text and not notiStruc.html:
        mylog('debug', '[Notification] notiStruc is empty')
    else:
        mylog('debug', ['[Notification] notiStruc:', json.dumps(notiStruc.__dict__, indent=4)])

    return notiStruc


def get_notifications (db):

    sql = db.sql  #TO-DO
    global mail_text, mail_html, json_final, partial_html, partial_txt, partial_json

    deviceUrl              = conf.REPORT_DASHBOARD_URL + '/deviceDetails.php?mac='
    plugins_report         = False

    # Reporting section
    mylog('verbose', ['[Notification] Check if something to report'])

    # prepare variables for JSON construction
    json_internet = []
    json_new_devices = []
    json_down_devices = []
    json_events = []
    json_ports = []
    json_plugins = []

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

    # Open text Template
    mylog('verbose', ['[Notification] Open text Template'])
    template_file = open(pialertPath + '/back/report_template.txt', 'r')
    mail_text = template_file.read()
    template_file.close()

    # Open html Template
    mylog('verbose', ['[Notification] Open html Template'])


    # select template type depoending if running latest version or an older one
    if conf.newVersionAvailable :
        template_file_path = '/back/report_template_new_version.html'
    else:
        template_file_path = '/back/report_template.html'

    mylog('verbose', ['[Notification] Using template', template_file_path])
    template_file = open(pialertPath + template_file_path, 'r')

    mail_html = template_file.read()
    template_file.close()

    # Report "REPORT_DATE" in Header & footer
    timeFormated = timeNowTZ().strftime ('%Y-%m-%d %H:%M')
    mail_text = mail_text.replace ('<REPORT_DATE>', timeFormated)
    mail_html = mail_html.replace ('<REPORT_DATE>', timeFormated)

    # Report "SERVER_NAME" in Header & footer
    mail_text = mail_text.replace ('<SERVER_NAME>', socket.gethostname() )
    mail_html = mail_html.replace ('<SERVER_NAME>', socket.gethostname() )

    # Report "VERSION" in Header & footer
    VERSIONFILE = subprocess.check_output(['php', pialertPath + '/front/php/templates/version.php']).decode('utf-8')
    mail_text = mail_text.replace ('<VERSION_PIALERT>', VERSIONFILE)
    mail_html = mail_html.replace ('<VERSION_PIALERT>', VERSIONFILE)	

    # Report "BUILD" in Header & footer
    BUILDFILE = subprocess.check_output(['php', pialertPath + '/front/php/templates/build.php']).decode('utf-8')
    mail_text = mail_text.replace ('<BUILD_PIALERT>', BUILDFILE)
    mail_html = mail_html.replace ('<BUILD_PIALERT>', BUILDFILE)
	
    mylog('verbose', ['[Notification] included sections: ', conf.INCLUDED_SECTIONS ])

    if 'new_devices' in conf.INCLUDED_SECTIONS :
        # Compose New Devices Section
        sqlQuery = """SELECT eve_MAC as MAC, eve_DateTime as Datetime, dev_LastIP as IP, eve_EventType as "Event Type", dev_Name as "Device name", dev_Comments as Comments  FROM Events_Devices
                        WHERE eve_PendingAlertEmail = 1
                        AND eve_EventType = 'New Device'
                        ORDER BY eve_DateTime"""

        notiStruc = construct_notifications(db, sqlQuery, "New devices")

        # collect "new_devices" for the webhook json
        json_new_devices = notiStruc.json["data"]

        mail_text = mail_text.replace ('<NEW_DEVICES_TABLE>', notiStruc.text + '\n')
        mail_html = mail_html.replace ('<NEW_DEVICES_TABLE>', notiStruc.html)
        mylog('verbose', ['[Notification] New Devices sections done.'])

    if 'down_devices' in conf.INCLUDED_SECTIONS :
        # Compose Devices Down Section
        sqlQuery = """SELECT eve_MAC as MAC, eve_DateTime as Datetime, dev_LastIP as IP, eve_EventType as "Event Type", dev_Name as "Device name", dev_Comments as Comments  FROM Events_Devices
                        WHERE eve_PendingAlertEmail = 1
                        AND eve_EventType = 'Device Down'
                        ORDER BY eve_DateTime"""

        notiStruc = construct_notifications(db, sqlQuery, "Down devices")

        # collect "down_devices" for the webhook json
        json_down_devices = notiStruc.json["data"]

        mail_text = mail_text.replace ('<DOWN_DEVICES_TABLE>', notiStruc.text + '\n')
        mail_html = mail_html.replace ('<DOWN_DEVICES_TABLE>', notiStruc.html)
        mylog('verbose', ['[Notification] Down Devices sections done.'])

    if 'events' in conf.INCLUDED_SECTIONS :
        # Compose Events Section
        sqlQuery = """SELECT eve_MAC as MAC, eve_DateTime as Datetime, dev_LastIP as IP, eve_EventType as "Event Type", dev_Name as "Device name", dev_Comments as Comments  FROM Events_Devices
                        WHERE eve_PendingAlertEmail = 1
                        AND eve_EventType IN ('Connected','Disconnected',
                            'IP Changed')
                        ORDER BY eve_DateTime"""

        notiStruc = construct_notifications(db, sqlQuery, "Events")

        # collect "events" for the webhook json
        json_events = notiStruc.json["data"]

        mail_text = mail_text.replace ('<EVENTS_TABLE>', notiStruc.text + '\n')
        mail_html = mail_html.replace ('<EVENTS_TABLE>', notiStruc.html)
        mylog('verbose', ['[Notification] Events sections done.'])    

    if 'plugins' in conf.INCLUDED_SECTIONS:
        # Compose Plugins Section
        sqlQuery = """SELECT Plugin, Object_PrimaryId, Object_SecondaryId, DateTimeChanged, Watched_Value1, Watched_Value2, Watched_Value3, Watched_Value4, Status from Plugins_Events"""

        notiStruc = construct_notifications(db, sqlQuery, "Plugins")

        # collect "plugins" for the webhook json
        json_plugins = notiStruc.json["data"]

        mail_text = mail_text.replace ('<PLUGINS_TABLE>', notiStruc.text + '\n')
        mail_html = mail_html.replace ('<PLUGINS_TABLE>', notiStruc.html)

        # check if we need to report something
        plugins_report = len(json_plugins) > 0
        mylog('verbose', ['[Notification] Plugins sections done.'])

    final_json = {
                    "internet": json_internet,
                    "new_devices": json_new_devices,
                    "down_devices": json_down_devices,
                    "events": json_events,                    
                    "plugins": json_plugins,
                    }

    final_text = removeDuplicateNewLines(mail_text)

    # Create clickable MAC links
    final_html = generate_mac_links (mail_html, deviceUrl)    

    #  Write output emails for debug
    write_file (logPath + '/report_output.json', json.dumps(final_json))
    write_file (logPath + '/report_output.txt', final_text)
    write_file (logPath + '/report_output.html', final_html)

    mylog('minimal', ['[Notification] Udating API files'])
    send_api()

    return noti_obj(final_json, final_text, final_html)   



    #     if conf.REPORT_MAIL and check_config('email'):
    #         updateState("Send: Email")
    #         mylog('minimal', ['[Notification] Sending report by Email'])
    #         send_email (msg )
    #     else :
    #         mylog('verbose', ['[Notification] Skip email'])
    #     
    
    #     if conf.REPORT_WEBHOOK and check_config('webhook'):
    #         updateState("Send: Webhook")
    #         mylog('minimal', ['[Notification] Sending report by Webhook'])
    #         send_webhook (msg)
    #     else :
    #         mylog('verbose', ['[Notification] Skip webhook'])
    #     if conf.REPORT_NTFY and check_config('ntfy'):
    #         updateState("Send: NTFY")
    #         mylog('minimal', ['[Notification] Sending report by NTFY'])
    #         send_ntfy (msg)
    #     else :
    #         mylog('verbose', ['[Notification] Skip NTFY'])
    #     if conf.REPORT_PUSHSAFER and check_config('pushsafer'):
    #         updateState("Send: PUSHSAFER")
    #         mylog('minimal', ['[Notification] Sending report by PUSHSAFER'])
    #         send_pushsafer (msg)
    #     else :
    #         mylog('verbose', ['[Notification] Skip PUSHSAFER'])
    #     # Update MQTT entities
    #     if conf.REPORT_MQTT and check_config('mqtt'):
    #         updateState("Send: MQTT")
    #         mylog('minimal', ['[Notification] Establishing MQTT thread'])
    #         mqtt_start(db)
    #     else :
    #         mylog('verbose', ['[Notification] Skip MQTT'])
    # else :
    #     mylog('verbose', ['[Notification] No changes to report'])


#-------------------------------------------------------------------------------
# Replacing table headers
def format_table (html, thValue, props, newThValue = ''):

    if newThValue == '':
        newThValue = thValue

    return html.replace("<th>"+thValue+"</th>", "<th "+props+" >"+newThValue+"</th>" )

#-------------------------------------------------------------------------------
def format_report_section (pActive, pSection, pTable, pText, pHTML):


    # Replace section text
    if pActive :
        conf.mail_text = conf.mail_text.replace ('<'+ pTable +'>', pText)
        conf.mail_html = conf.mail_html.replace ('<'+ pTable +'>', pHTML)

        conf.mail_text = remove_tag (conf.mail_text, pSection)
        conf.mail_html = remove_tag (conf.mail_html, pSection)
    else:
        conf.mail_text = remove_section (conf.mail_text, pSection)
        conf.mail_html = remove_section (conf.mail_html, pSection)

#-------------------------------------------------------------------------------
def remove_section (pText, pSection):
    # Search section into the text
    if pText.find ('<'+ pSection +'>') >=0 \
    and pText.find ('</'+ pSection +'>') >=0 :
        # return text without the section
        return pText[:pText.find ('<'+ pSection+'>')] + \
               pText[pText.find ('</'+ pSection +'>') + len (pSection) +3:]
    else :
        # return all text
        return pText

#-------------------------------------------------------------------------------
def remove_tag (pText, pTag):
    # return text without the tag
    return pText.replace ('<'+ pTag +'>','').replace ('</'+ pTag +'>','')


#-------------------------------------------------------------------------------
# Reporting
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
def send_api():
        mylog('verbose', ['[Send API] Updating notification_* files in ', apiPath])

        write_file(apiPath + 'notification_text.txt'  , mail_text)
        write_file(apiPath + 'notification_text.html'  , mail_html)
        write_file(apiPath + 'notification_json_final.json'  , json.dumps(json_final))


#-------------------------------------------------------------------------------
def skip_repeated_notifications (db):

    # Skip repeated notifications
    # due strfime : Overflow --> use  "strftime / 60"
    mylog('verbose','[Skip Repeated Notifications] Skip Repeated start')
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
    mylog('verbose','[Skip Repeated Notifications] Skip Repeated end')

    db.commitDB()





