from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import datetime
import json
import smtplib
import socket
from base64 import b64encode
import subprocess
import requests
from json2table import convert

from const import pialertPath, logPath
# from pialert.api import update_api
from conf import *
from database import get_table_as_json, updateState
from files import write_file
from helper import generate_mac_links, isNewVersion, removeDuplicateNewLines, timeNow, hide_email
from logger import logResult, mylog, print_log
from mqtt import mqtt_start




#===============================================================================
# REPORTING
#===============================================================================
# create a json for webhook and mqtt notifications to provide further integration options  


json_final = []

#-------------------------------------------------------------------------------
class noti_struc:
    def __init__(self, json, text, html):
        self.json = json
        self.text = text
        self.html = html


#-------------------------------------------------------------------------------
def construct_notifications(sqlQuery, tableTitle, skipText = False, suppliedJsonStruct = None):

    if suppliedJsonStruct is None and sqlQuery == "":
        return noti_struc("", "", "")

    table_attributes = {"style" : "border-collapse: collapse; font-size: 12px; color:#70707", "width" : "100%", "cellspacing" : 0, "cellpadding" : "3px", "bordercolor" : "#C0C0C0", "border":"1"}
    headerProps = "width='120px' style='color:blue; font-size: 16px;' bgcolor='#909090' "
    thProps = "width='120px' style='color:#F0F0F0' bgcolor='#909090' "

    build_direction = "TOP_TO_BOTTOM"
    text_line = '{}\t{}\n'

    if suppliedJsonStruct is None:
        json_struc = get_table_as_json(sqlQuery)
    else:
        json_struc = suppliedJsonStruct

    jsn  = json_struc.json
    html = ""    
    text = ""

    if len(jsn["data"]) > 0:
        text = tableTitle + "\n---------\n"

        html = convert(jsn, build_direction=build_direction, table_attributes=table_attributes)
        html = format_table(html, "data", headerProps, tableTitle).replace('<ul>','<ul style="list-style:none;padding-left:0">')

        headers = json_struc.columnNames

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

    return noti_struc(jsn, text, html)




def send_notifications (db):
    sql = db.sql  #TO-DO
    global mail_text, mail_html, json_final, changedPorts_json_struc, partial_html, partial_txt, partial_json

    deviceUrl              = REPORT_DASHBOARD_URL + '/deviceDetails.php?mac='
    plugins_report         = False

    # Reporting section
    mylog('verbose', ['  Check if something to report'])    

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
    template_file = open(pialertPath + '/back/report_template.txt', 'r') 
    mail_text = template_file.read() 
    template_file.close() 

    # Open html Template
    template_file = open(pialertPath + '/back/report_template.html', 'r') 
    if isNewVersion(db):
        template_file = open(pialertPath + '/back/report_template_new_version.html', 'r') 

    mail_html = template_file.read() 
    template_file.close() 

    # Report Header & footer
    timeFormated = timeNow().strftime ('%Y-%m-%d %H:%M')
    mail_text = mail_text.replace ('<REPORT_DATE>', timeFormated)
    mail_html = mail_html.replace ('<REPORT_DATE>', timeFormated)

    mail_text = mail_text.replace ('<SERVER_NAME>', socket.gethostname() )
    mail_html = mail_html.replace ('<SERVER_NAME>', socket.gethostname() )

    if 'internet' in INCLUDED_SECTIONS:
        # Compose Internet Section
        sqlQuery = """SELECT eve_MAC as MAC,  eve_IP as IP, eve_DateTime as Datetime, eve_EventType as "Event Type", eve_AdditionalInfo as "More info" FROM Events
                        WHERE eve_PendingAlertEmail = 1 AND eve_MAC = 'Internet'
                        ORDER BY eve_DateTime"""

        notiStruc = construct_notifications(sqlQuery, "Internet IP change")

        # collect "internet" (IP changes) for the webhook json          
        json_internet = notiStruc.json["data"]

        mail_text = mail_text.replace ('<SECTION_INTERNET>', notiStruc.text + '\n')
        mail_html = mail_html.replace ('<INTERNET_TABLE>', notiStruc.html)

    if 'new_devices' in INCLUDED_SECTIONS:
        # Compose New Devices Section 
        sqlQuery = """SELECT eve_MAC as MAC, eve_DateTime as Datetime, dev_LastIP as IP, eve_EventType as "Event Type", dev_Name as "Device name", dev_Comments as Comments  FROM Events_Devices
                        WHERE eve_PendingAlertEmail = 1
                        AND eve_EventType = 'New Device'
                        ORDER BY eve_DateTime"""

        notiStruc = construct_notifications(sqlQuery, "New devices")

        # collect "new_devices" for the webhook json         
        json_new_devices = notiStruc.json["data"]

        mail_text = mail_text.replace ('<SECTION_NEW_DEVICES>', notiStruc.text + '\n')
        mail_html = mail_html.replace ('<NEW_DEVICES_TABLE>', notiStruc.html)

    if 'down_devices' in INCLUDED_SECTIONS:
        # Compose Devices Down Section   
        sqlQuery = """SELECT eve_MAC as MAC, eve_DateTime as Datetime, dev_LastIP as IP, eve_EventType as "Event Type", dev_Name as "Device name", dev_Comments as Comments  FROM Events_Devices
                        WHERE eve_PendingAlertEmail = 1
                        AND eve_EventType = 'Device Down'
                        ORDER BY eve_DateTime"""

        notiStruc = construct_notifications(sqlQuery, "Down devices")

        # collect "new_devices" for the webhook json         
        json_down_devices = notiStruc.json["data"]

        mail_text = mail_text.replace ('<SECTION_DEVICES_DOWN>', notiStruc.text + '\n')
        mail_html = mail_html.replace ('<DOWN_DEVICES_TABLE>', notiStruc.html)

    if 'events' in INCLUDED_SECTIONS:
        # Compose Events Section   
        sqlQuery = """SELECT eve_MAC as MAC, eve_DateTime as Datetime, dev_LastIP as IP, eve_EventType as "Event Type", dev_Name as "Device name", dev_Comments as Comments  FROM Events_Devices
                        WHERE eve_PendingAlertEmail = 1
                        AND eve_EventType IN ('Connected','Disconnected',
                            'IP Changed')
                        ORDER BY eve_DateTime"""

        notiStruc = construct_notifications(sqlQuery, "Events")

        # collect "events" for the webhook json         
        json_events = notiStruc.json["data"]

        mail_text = mail_text.replace ('<SECTION_EVENTS>', notiStruc.text + '\n')
        mail_html = mail_html.replace ('<EVENTS_TABLE>', notiStruc.html)
    
    if 'ports' in INCLUDED_SECTIONS:  
        # collect "ports" for the webhook json 
        if changedPorts_json_struc is not None:          
            json_ports =  changedPorts_json_struc.json["data"]       

        notiStruc = construct_notifications("", "Ports", True, changedPorts_json_struc)

        mail_html = mail_html.replace ('<PORTS_TABLE>', notiStruc.html)

        portsTxt = ""
        if changedPorts_json_struc is not None:
            portsTxt = "Ports \n---------\n Ports changed! Check PiAlert for details!\n"        

        mail_text = mail_text.replace ('<PORTS_TABLE>', portsTxt )

    if 'plugins' in INCLUDED_SECTIONS and ENABLE_PLUGINS:  
        # Compose Plugins Section           
        sqlQuery = """SELECT Plugin, Object_PrimaryId, Object_SecondaryId, DateTimeChanged, Watched_Value1, Watched_Value2, Watched_Value3, Watched_Value4, Status from Plugins_Events"""

        notiStruc = construct_notifications(sqlQuery, "Plugins")

        # collect "plugins" for the webhook json 
        json_plugins = notiStruc.json["data"]

        mail_text = mail_text.replace ('<PLUGINS_TABLE>', notiStruc.text + '\n')
        mail_html = mail_html.replace ('<PLUGINS_TABLE>', notiStruc.html)

        # check if we need to report something
        plugins_report = len(json_plugins) > 0


    json_final = {
                    "internet": json_internet,                        
                    "new_devices": json_new_devices,
                    "down_devices": json_down_devices,                        
                    "events": json_events,
                    "ports": json_ports,
                    "plugins": json_plugins,
                    }    

    mail_text = removeDuplicateNewLines(mail_text)
    
    # Create clickable MAC links 
    mail_html = generate_mac_links (mail_html, deviceUrl)

    #  Write output emails for debug    
    write_file (logPath + '/report_output.json', json.dumps(json_final)) 
    write_file (logPath + '/report_output.txt', mail_text) 
    write_file (logPath + '/report_output.html', mail_html) 

    # Send Mail
    if json_internet != [] or json_new_devices != [] or json_down_devices != [] or json_events != [] or json_ports != [] or debug_force_notification or plugins_report:        

        # update_api(True) # TO-DO

        mylog('none', ['    Changes detected, sending reports'])

        if REPORT_MAIL and check_config('email'):  
            updateState(db,"Send: Email")
            mylog('info', ['      Sending report by Email'])
            send_email (mail_text, mail_html)
        else :
            mylog('verbose', ['      Skip email'])
        if REPORT_APPRISE and check_config('apprise'):
            updateState(db,"Send: Apprise")
            mylog('info', ['      Sending report by Apprise'])
            send_apprise (mail_html, mail_text)
        else :
            mylog('verbose', ['      Skip Apprise'])
        if REPORT_WEBHOOK and check_config('webhook'):
            updateState(db,"Send: Webhook")
            mylog('info', ['      Sending report by Webhook'])
            send_webhook (json_final, mail_text)
        else :
            mylog('verbose', ['      Skip webhook'])
        if REPORT_NTFY and check_config('ntfy'):
            updateState(db,"Send: NTFY")
            mylog('info', ['      Sending report by NTFY'])
            send_ntfy (mail_text)
        else :
            mylog('verbose', ['      Skip NTFY'])
        if REPORT_PUSHSAFER and check_config('pushsafer'):
            updateState(db,"Send: PUSHSAFER")
            mylog('info', ['      Sending report by PUSHSAFER'])
            send_pushsafer (mail_text)
        else :
            mylog('verbose', ['      Skip PUSHSAFER'])
        # Update MQTT entities
        if REPORT_MQTT and check_config('mqtt'):
            updateState(db,"Send: MQTT")
            mylog('info', ['      Establishing MQTT thread'])                          
            mqtt_start()        
        else :
            mylog('verbose', ['      Skip MQTT'])
    else :
        mylog('verbose', ['    No changes to report'])

    # Clean Pending Alert Events
    sql.execute ("""UPDATE Devices SET dev_LastNotification = ?
                    WHERE dev_MAC IN (SELECT eve_MAC FROM Events
                                      WHERE eve_PendingAlertEmail = 1)
                 """, (datetime.datetime.now(),) )
    sql.execute ("""UPDATE Events SET eve_PendingAlertEmail = 0
                    WHERE eve_PendingAlertEmail = 1""")

    # clear plugin events
    sql.execute ("DELETE FROM Plugins_Events")
    
    changedPorts_json_struc = None

    # DEBUG - print number of rows updated    
    mylog('info', ['[', timeNow(), '] Notifications: ', sql.rowcount])

    # Commit changes    
    db.commitDB()


#-------------------------------------------------------------------------------
def check_config(service):

    if service == 'email':
        if SMTP_SERVER == '' or REPORT_FROM == '' or REPORT_TO == '':
            mylog('none', ['    Error: Email service not set up correctly. Check your pialert.conf SMTP_*, REPORT_FROM and REPORT_TO variables.'])
            return False
        else:
            return True   

    if service == 'apprise':
        if APPRISE_URL == '' or APPRISE_HOST == '':
            mylog('none', ['    Error: Apprise service not set up correctly. Check your pialert.conf APPRISE_* variables.'])
            return False
        else:
            return True  

    if service == 'webhook':
        if WEBHOOK_URL == '':
            mylog('none', ['    Error: Webhook service not set up correctly. Check your pialert.conf WEBHOOK_* variables.'])
            return False
        else:
            return True 

    if service == 'ntfy':
        if NTFY_HOST == '' or NTFY_TOPIC == '':
            mylog('none', ['    Error: NTFY service not set up correctly. Check your pialert.conf NTFY_* variables.'])
            return False
        else:
            return True 

    if service == 'pushsafer':
        if PUSHSAFER_TOKEN == 'ApiKey':
            mylog('none', ['    Error: Pushsafer service not set up correctly. Check your pialert.conf PUSHSAFER_TOKEN variable.'])
            return False
        else:
            return True 

    if service == 'mqtt':
        if MQTT_BROKER == '' or MQTT_PORT == '' or MQTT_USER == '' or MQTT_PASSWORD == '':
            mylog('none', ['    Error: MQTT service not set up correctly. Check your pialert.conf MQTT_* variables.'])
            return False
        else:
            return True 

#-------------------------------------------------------------------------------
def format_table (html, thValue, props, newThValue = ''):

    if newThValue == '':
        newThValue = thValue
        
    return html.replace("<th>"+thValue+"</th>", "<th "+props+" >"+newThValue+"</th>" )

#-------------------------------------------------------------------------------
def format_report_section (pActive, pSection, pTable, pText, pHTML):
    global mail_text
    global mail_html

    # Replace section text
    if pActive :
        mail_text = mail_text.replace ('<'+ pTable +'>', pText)
        mail_html = mail_html.replace ('<'+ pTable +'>', pHTML)       

        mail_text = remove_tag (mail_text, pSection)       
        mail_html = remove_tag (mail_html, pSection)
    else:
        mail_text = remove_section (mail_text, pSection)
        mail_html = remove_section (mail_html, pSection)

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
def send_email (pText, pHTML):

    # Print more info for debugging if LOG_LEVEL == 'debug' 
    if LOG_LEVEL == 'debug':
        print_log ('REPORT_TO: ' + hide_email(str(REPORT_TO)) + '  SMTP_USER: ' + hide_email(str(SMTP_USER))) 

    # Compose email
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Pi.Alert Report'
    msg['From'] = REPORT_FROM
    msg['To'] = REPORT_TO
    msg.attach (MIMEText (pText, 'plain'))
    msg.attach (MIMEText (pHTML, 'html'))

    failedAt = ''

    failedAt = print_log ('SMTP try')

    try:
        # Send mail
        failedAt = print_log('Trying to open connection to ' + str(SMTP_SERVER) + ':' + str(SMTP_PORT))

        if SMTP_FORCE_SSL:
            failedAt = print_log('SMTP_FORCE_SSL == True so using .SMTP_SSL()')
            if SMTP_PORT == 0:            
                failedAt = print_log('SMTP_PORT == 0 so sending .SMTP_SSL(SMTP_SERVER)')
                smtp_connection = smtplib.SMTP_SSL(SMTP_SERVER)
            else:
                failedAt = print_log('SMTP_PORT == 0 so sending .SMTP_SSL(SMTP_SERVER, SMTP_PORT)')
                smtp_connection = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
            
        else:
            failedAt = print_log('SMTP_FORCE_SSL == False so using .SMTP()')
            if SMTP_PORT == 0:
                failedAt = print_log('SMTP_PORT == 0 so sending .SMTP(SMTP_SERVER)')
                smtp_connection = smtplib.SMTP (SMTP_SERVER)
            else:
                failedAt = print_log('SMTP_PORT == 0 so sending .SMTP(SMTP_SERVER, SMTP_PORT)')
                smtp_connection = smtplib.SMTP (SMTP_SERVER, SMTP_PORT)

        failedAt = print_log('Setting SMTP debug level')

        # Log level set to debug of the communication between SMTP server and client
        if LOG_LEVEL == 'debug':
            smtp_connection.set_debuglevel(1) 
        
        failedAt = print_log( 'Sending .ehlo()')
        smtp_connection.ehlo()

        if not SMTP_SKIP_TLS:       
            failedAt = print_log('SMTP_SKIP_TLS == False so sending .starttls()')
            smtp_connection.starttls()
            failedAt = print_log('SMTP_SKIP_TLS == False so sending .ehlo()')
            smtp_connection.ehlo()
        if not SMTP_SKIP_LOGIN:
            failedAt = print_log('SMTP_SKIP_LOGIN == False so sending .login()')
            smtp_connection.login (SMTP_USER, SMTP_PASS)
            
        failedAt = print_log('Sending .sendmail()')
        smtp_connection.sendmail (REPORT_FROM, REPORT_TO, msg.as_string())
        smtp_connection.quit()
    except smtplib.SMTPAuthenticationError as e: 
        mylog('none', ['      ERROR: Failed at - ', failedAt])
        mylog('none', ['      ERROR: Couldn\'t connect to the SMTP server (SMTPAuthenticationError), skipping Email (enable LOG_LEVEL=debug for more logging)'])
    except smtplib.SMTPServerDisconnected as e: 
        mylog('none', ['      ERROR: Failed at - ', failedAt])
        mylog('none', ['      ERROR: Couldn\'t connect to the SMTP server (SMTPServerDisconnected), skipping Email (enable LOG_LEVEL=debug for more logging)'])

    print_log('      DEBUG: Last executed - ' + str(failedAt))

#-------------------------------------------------------------------------------
def send_ntfy (_Text):
    headers = {
        "Title": "Pi.Alert Notification",
        "Actions": "view, Open Dashboard, "+ REPORT_DASHBOARD_URL,
        "Priority": "urgent",
        "Tags": "warning"
    }
    # if username and password are set generate hash and update header
    if NTFY_USER != "" and NTFY_PASSWORD != "":
	# Generate hash for basic auth
        usernamepassword = "{}:{}".format(NTFY_USER,NTFY_PASSWORD)
        basichash = b64encode(bytes(NTFY_USER + ':' + NTFY_PASSWORD, "utf-8")).decode("ascii")

	# add authorization header with hash
        headers["Authorization"] = "Basic {}".format(basichash)

    requests.post("{}/{}".format( NTFY_HOST, NTFY_TOPIC),
    data=_Text,
    headers=headers)

def send_pushsafer (_Text):
    url = 'https://www.pushsafer.com/api'
    post_fields = {
        "t" : 'Pi.Alert Message',
        "m" : _Text,
        "s" : 11,
        "v" : 3,
        "i" : 148,
        "c" : '#ef7f7f',
        "d" : 'a',
        "u" : REPORT_DASHBOARD_URL,
        "ut" : 'Open Pi.Alert',
        "k" : PUSHSAFER_TOKEN,
        }
    requests.post(url, data=post_fields)

#-------------------------------------------------------------------------------
def send_webhook (_json, _html):

    # use data type based on specified payload type
    if WEBHOOK_PAYLOAD == 'json':
        payloadData = _json        
    if WEBHOOK_PAYLOAD == 'html':
        payloadData = _html
    if WEBHOOK_PAYLOAD == 'text':
        payloadData = to_text(_json)

    # Define slack-compatible payload
    _json_payload = { "text": payloadData } if WEBHOOK_PAYLOAD == 'text' else {
    "username": "Pi.Alert",
    "text": "There are new notifications",
    "attachments": [{
      "title": "Pi.Alert Notifications",
      "title_link": REPORT_DASHBOARD_URL,
      "text": payloadData
    }]
    } 

    # DEBUG - Write the json payload into a log file for debugging
    write_file (logPath + '/webhook_payload.json', json.dumps(_json_payload))    

    # Using the Slack-Compatible Webhook endpoint for Discord so that the same payload can be used for both
    if(WEBHOOK_URL.startswith('https://discord.com/api/webhooks/') and not WEBHOOK_URL.endswith("/slack")):
        _WEBHOOK_URL = f"{WEBHOOK_URL}/slack"
        curlParams = ["curl","-i","-H", "Content-Type:application/json" ,"-d", json.dumps(_json_payload), _WEBHOOK_URL]
    else:
        _WEBHOOK_URL = WEBHOOK_URL
        curlParams = ["curl","-i","-X", WEBHOOK_REQUEST_METHOD ,"-H", "Content-Type:application/json" ,"-d", json.dumps(_json_payload), _WEBHOOK_URL]

    # execute CURL call
    try:
        # try runnning a subprocess
        mylog('debug', curlParams) 
        p = subprocess.Popen(curlParams, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        stdout, stderr = p.communicate()

        # write stdout and stderr into .log files for debugging if needed
        logResult (stdout, stderr)     # TO-DO should be changed to mylog
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        mylog('none', [e.output])

#-------------------------------------------------------------------------------
def send_apprise (html, text):
    #Define Apprise compatible payload (https://github.com/caronc/apprise-api#stateless-solution)
    payload = html

    if APPRISE_PAYLOAD == 'text':
        payload = text

    _json_payload={
    "urls": APPRISE_URL,
    "title": "Pi.Alert Notifications",    
    "format": APPRISE_PAYLOAD,
    "body": payload    
    }

    try:
        # try runnning a subprocess        
        p = subprocess.Popen(["curl","-i","-X", "POST" ,"-H", "Content-Type:application/json" ,"-d", json.dumps(_json_payload), APPRISE_HOST], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = p.communicate()
        # write stdout and stderr into .log files for debugging if needed
        logResult (stdout, stderr)      # TO-DO should be changed to mylog
    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        mylog('none', [e.output])    


def to_text(_json):
    payloadData = ""
    if len(_json['internet']) > 0 and 'internet' in INCLUDED_SECTIONS:
        payloadData += "INTERNET\n"
        for event in _json['internet']:
            payloadData += event[3] + ' on ' + event[2] + '. ' + event[4] + '. New address:' + event[1] + '\n'

    if len(_json['new_devices']) > 0 and 'new_devices' in INCLUDED_SECTIONS:
        payloadData += "NEW DEVICES:\n"
        for event in _json['new_devices']:
            if event[4] is None:
                event[4] = event[11]
            payloadData += event[1] + ' - ' + event[4] + '\n'

    if len(_json['down_devices']) > 0 and 'down_devices' in INCLUDED_SECTIONS:
        write_file (logPath + '/down_devices_example.log', _json['down_devices'])
        payloadData += 'DOWN DEVICES:\n'
        for event in _json['down_devices']:
            if event[4] is None:
                event[4] = event[11]
            payloadData += event[1] + ' - ' + event[4] + '\n'
    
    if len(_json['events']) > 0 and 'events' in INCLUDED_SECTIONS:
        payloadData += "EVENTS:\n"
        for event in _json['events']:
            if event[8] != "Internet":
                payloadData += event[8] + " on " + event[1] + " " + event[3] + " at " + event[2] + "\n"

    return payloadData



#-------------------------------------------------------------------------------
def skip_repeated_notifications (db):    

    # Skip repeated notifications
    # due strfime : Overflow --> use  "strftime / 60"
    print_log ('Skip Repeated')
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
    print_log ('Skip Repeated end')

    db.commitDB()    