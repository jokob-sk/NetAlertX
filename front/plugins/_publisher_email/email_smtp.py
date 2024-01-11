#!/usr/bin/env python
import json
import subprocess
import argparse
import os
import pathlib
import sys
import re
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import parseaddr
import smtplib
import socket
import ssl

sys.path.extend(["/home/pi/pialert/front/plugins", "/home/pi/pialert/pialert"])

# PiAlert modules
import conf
from plugin_helper import Plugin_Objects
from logger import mylog, append_line_to_file, print_log
from helper import timeNowTZ, get_setting_value, hide_email
from notification import Notification_obj
from database import DB


CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

pluginName = 'SMTP'

def main():
    
    mylog('verbose', [f'[{pluginName}](publisher) In script'])    
    
    # Check if basic config settings supplied
    if check_config() == False:
        mylog('none', [f'[{pluginName}] ⚠ ERROR: Publisher notification gateway not set up correctly. Check your pialert.conf {pluginName}_* variables.'])
        return

    # Create a database connection
    db = DB()  # instance of class DB
    db.open()

    # Initialize the Plugin obj output file
    plugin_objects = Plugin_Objects(RESULT_FILE)

    # Create a Notification_obj instance
    notifications = Notification_obj(db)

    # Retrieve new notifications
    new_notifications = notifications.getNew()

    # Process the new notifications (see the Notifications DB table for structure or check the /api/table_notifications.json endpoint)
    for notification in new_notifications:

        # Send notification
        result = send(notification["HTML"], notification["Text"])    

        # Log result
        plugin_objects.add_object(
            primaryId   = pluginName,
            secondaryId = timeNowTZ(),            
            watched1    = notification["GUID"],
            watched2    = result,            
            watched3    = 'null',
            watched4    = 'null',
            extra       = 'null',
            foreignKey  = notification["GUID"]
        )

    plugin_objects.write_result_file()

#-------------------------------------------------------------------------------
def check_config ():

    server      = get_setting_value('SMTP_SERVER')
    report_to   = get_setting_value("SMTP_REPORT_TO")
    report_from = get_setting_value("SMTP_REPORT_FROM")
    
    if server == '' or report_from == '' or report_to == '':
        mylog('none', ['[Email Check Config] ⚠ ERROR: Email service not set up correctly. Check your pialert.conf SMTP_*, SMTP_REPORT_FROM and SMTP_REPORT_TO variables.'])
        return False
    else:
        return True
    
#-------------------------------------------------------------------------------
def send(pHTML, pText):

    mylog('debug', [f'[{pluginName}] SMTP_REPORT_TO: {hide_email(str(get_setting_value("SMTP_REPORT_TO")))} SMTP_USER: {hide_email(str(get_setting_value("SMTP_USER")))}'])


    subject, from_email, to_email, message_html, message_text = sanitize_email_content('Pi.Alert Report', get_setting_value("SMTP_REPORT_FROM"), get_setting_value("SMTP_REPORT_TO"), pHTML, pText)

    # Compose email
    msg             = MIMEMultipart('alternative')
    msg['Subject']  = subject
    msg['From']     = from_email
    msg['To']       = to_email
    msg.attach (MIMEText (message_text, 'plain'))
    msg.attach (MIMEText (message_html, 'html'))

    # Set a timeout for the SMTP connection (in seconds)
    smtp_timeout = 30

    mylog('debug', ['Trying to open connection to ' + str(get_setting_value('SMTP_SERVER')) + ':' + str(get_setting_value('SMTP_PORT'))])

    if get_setting_value("LOG_LEVEL") == 'debug':

        send_email(msg,smtp_timeout)

    else:

        try:
            send_email(msg,smtp_timeout)
            
        except smtplib.SMTPAuthenticationError as e:            
            mylog('none', ['      ERROR: Couldn\'t connect to the SMTP server (SMTPAuthenticationError)'])
            mylog('none', ['      ERROR: Double-check your SMTP_USER and SMTP_PASS settings.)'])
            mylog('none', ['      ERROR: ', str(e)])
        except smtplib.SMTPServerDisconnected as e:            
            mylog('none', ['      ERROR: Couldn\'t connect to the SMTP server (SMTPServerDisconnected)'])
            mylog('none', ['      ERROR: ', str(e)])
        except socket.gaierror as e:            
            mylog('none', ['      ERROR: Could not resolve hostname (socket.gaierror)'])
            mylog('none', ['      ERROR: ', str(e)])      
        except ssl.SSLError as e:                        
            mylog('none', ['      ERROR: Could not establish SSL connection (ssl.SSLError)'])
            mylog('none', ['      ERROR: Are you sure you need SMTP_FORCE_SSL enabled? Check your SMTP provider docs.'])
            mylog('none', ['      ERROR: ', str(e)])      

# ----------------------------------------------------------------------------------
def send_email(msg,smtp_timeout):
    # Send mail
    if get_setting_value('SMTP_FORCE_SSL'):
        mylog('debug', ['SMTP_FORCE_SSL == True so using .SMTP_SSL()'])
        if get_setting_value("SMTP_PORT") == 0:
            mylog('debug', ['SMTP_PORT == 0 so sending .SMTP_SSL(SMTP_SERVER)'])
            smtp_connection = smtplib.SMTP_SSL(get_setting_value('SMTP_SERVER'))
        else:
            mylog('debug', ['SMTP_PORT == 0 so sending .SMTP_SSL(SMTP_SERVER, SMTP_PORT)'])
            smtp_connection = smtplib.SMTP_SSL(get_setting_value('SMTP_SERVER'), get_setting_value('SMTP_PORT'), timeout=smtp_timeout)

    else:
        mylog('debug', ['SMTP_FORCE_SSL == False so using .SMTP()'])
        if get_setting_value("SMTP_PORT") == 0:
            mylog('debug', ['SMTP_PORT == 0 so sending .SMTP(SMTP_SERVER)'])
            smtp_connection = smtplib.SMTP (get_setting_value('SMTP_SERVER'))
        else:
            mylog('debug', ['SMTP_PORT == 0 so sending .SMTP(SMTP_SERVER, SMTP_PORT)'])
            smtp_connection = smtplib.SMTP (get_setting_value('SMTP_SERVER'), get_setting_value('SMTP_PORT'))

    mylog('debug', ['Setting SMTP debug level'])

    # Log level set to debug of the communication between SMTP server and client
    if get_setting_value('LOG_LEVEL') == 'debug':
        smtp_connection.set_debuglevel(1)

    mylog('debug', [ 'Sending .ehlo()'])
    smtp_connection.ehlo()

    if not get_setting_value('SMTP_SKIP_TLS'):
        mylog('debug', ['SMTP_SKIP_TLS == False so sending .starttls()'])
        smtp_connection.starttls()
        mylog('debug', ['SMTP_SKIP_TLS == False so sending .ehlo()'])
        smtp_connection.ehlo()
    if not get_setting_value('SMTP_SKIP_LOGIN'):
        mylog('debug', ['SMTP_SKIP_LOGIN == False so sending .login()'])
        smtp_connection.login (get_setting_value('SMTP_USER'), get_setting_value('SMTP_PASS'))

    mylog('debug', ['Sending .sendmail()'])
    smtp_connection.sendmail (get_setting_value("SMTP_REPORT_FROM"), get_setting_value("SMTP_REPORT_TO"), msg.as_string())
    smtp_connection.quit()

# ----------------------------------------------------------------------------------
def sanitize_email_content(subject, from_email, to_email, message_html, message_text):
    # Validate and sanitize subject
    subject = Header(subject, 'utf-8').encode()

    # Validate and sanitize sender's email address
    from_name, from_address = parseaddr(from_email)
    from_email = Header(from_name, 'utf-8').encode() + ' <' + from_address + '>'

    # Validate and sanitize recipient's email address
    to_name, to_address = parseaddr(to_email)
    to_email = Header(to_name, 'utf-8').encode() + ' <' + to_address + '>'

    # Validate and sanitize message content
    # Remove potentially problematic characters
    message_html = re.sub(r'[^\x00-\x7F]+', ' ', message_html)
    message_text = re.sub(r'[^\x00-\x7F]+', ' ', message_text)

    return subject, from_email, to_email, message_html, message_text

# ----------------------------------------------------------------------------------
if __name__ == '__main__':
    sys.exit(main())
