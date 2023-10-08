#!/usr/bin/env python
import json
import subprocess
import argparse
import os
import pathlib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import socket

# Replace these paths with the actual paths to your Pi.Alert directories
sys.path.extend(["/home/pi/pialert/front/plugins", "/home/pi/pialert/pialert"])

# PiAlert modules
import conf
from plugin_helper import Plugin_Objects
from logger import mylog, append_line_to_file, print_log
from helper import timeNowTZ, noti_obj, get_setting_value, hide_email
from notification import Notification_obj
from database import DB


CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

pluginName = 'SMTP'

def main():
    
    mylog('verbose', [f'[{pluginName}](publisher) In script'])    
    
    # Check if basic config settings supplied
    if check_config() == False:
        mylog('none', [f'[{pluginName}] Error: Publisher notification gateway not set up correctly. Check your pialert.conf {pluginName}_* variables.'])
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

    # Process the new notifications
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
            foreignKey  = 'null'
        )

    plugin_objects.write_result_file()

#-------------------------------------------------------------------------------
def check_config ():
    if get_setting_value('SMTP_SERVER') == '' or get_setting_value('REPORT_FROM') == '' or get_setting_value('REPORT_TO') == '':
        mylog('none', ['[Email Check Config] Error: Email service not set up correctly. Check your pialert.conf SMTP_*, REPORT_FROM and REPORT_TO variables.'])
        return False
    else:
        return True
    
#-------------------------------------------------------------------------------
def send(pHTML, pText):

    mylog('debug', [f'[{pluginName}] REPORT_TO: {hide_email(str(get_setting_value('REPORT_TO')))} SMTP_USER: {hide_email(str(get_setting_value('SMTP_USER')))}'])

    # Compose email
    msg             = MIMEMultipart('alternative')
    msg['Subject']  = 'Pi.Alert Report'
    msg['From']     = get_setting_value('REPORT_FROM')
    msg['To']       = get_setting_value('REPORT_TO')
    msg.attach (MIMEText (pText, 'plain'))
    msg.attach (MIMEText (pHTML, 'html'))

    failedAt = ''

    failedAt = print_log ('SMTP try')

    try:
        # Send mail
        failedAt = print_log('Trying to open connection to ' + str(get_setting_value('SMTP_SERVER')) + ':' + str(get_setting_value('SMTP_PORT')))

        # Set a timeout for the SMTP connection (in seconds)
        smtp_timeout = 30

        if get_setting_value('SMTP_FORCE_SSL'):
            failedAt = print_log('SMTP_FORCE_SSL == True so using .SMTP_SSL()')
            if get_setting_value('SMTP_PORT') == 0:
                failedAt = print_log('SMTP_PORT == 0 so sending .SMTP_SSL(SMTP_SERVER)')
                smtp_connection = smtplib.SMTP_SSL(get_setting_value('SMTP_SERVER'))
            else:
                failedAt = print_log('SMTP_PORT == 0 so sending .SMTP_SSL(SMTP_SERVER, SMTP_PORT)')
                smtp_connection = smtplib.SMTP_SSL(get_setting_value('SMTP_SERVER'), get_setting_value('SMTP_PORT'), timeout=smtp_timeout)

        else:
            failedAt = print_log('SMTP_FORCE_SSL == False so using .SMTP()')
            if get_setting_value('SMTP_PORT') == 0:
                failedAt = print_log('SMTP_PORT == 0 so sending .SMTP(SMTP_SERVER)')
                smtp_connection = smtplib.SMTP (get_setting_value('SMTP_SERVER'))
            else:
                failedAt = print_log('SMTP_PORT == 0 so sending .SMTP(SMTP_SERVER, SMTP_PORT)')
                smtp_connection = smtplib.SMTP (get_setting_value('SMTP_SERVER'), get_setting_value('SMTP_PORT'))

        failedAt = print_log('Setting SMTP debug level')

        # Log level set to debug of the communication between SMTP server and client
        if get_setting_value('LOG_LEVEL') == 'debug':
            smtp_connection.set_debuglevel(1)

        failedAt = print_log( 'Sending .ehlo()')
        smtp_connection.ehlo()

        if not get_setting_value('SMTP_SKIP_TLS'):
            failedAt = print_log('SMTP_SKIP_TLS == False so sending .starttls()')
            smtp_connection.starttls()
            failedAt = print_log('SMTP_SKIP_TLS == False so sending .ehlo()')
            smtp_connection.ehlo()
        if not get_setting_value('SMTP_SKIP_LOGIN'):
            failedAt = print_log('SMTP_SKIP_LOGIN') == False so sending .login()')
            smtp_connection.login (get_setting_value('SMTP_USER'), get_setting_value('SMTP_PASS'))

        failedAt = print_log('Sending .sendmail()')
        smtp_connection.sendmail (get_setting_value('REPORT_FROM'), get_setting_value('REPORT_TO'), msg.as_string())
        smtp_connection.quit()
    except smtplib.SMTPAuthenticationError as e:
        mylog('none', ['      ERROR: Failed at - ', failedAt])
        mylog('none', ['      ERROR: Couldn\'t connect to the SMTP server (SMTPAuthenticationError), skipping Email (enable LOG_LEVEL=debug for more logging)'])
        mylog('none', ['      ERROR: ', str(e)])
    except smtplib.SMTPServerDisconnected as e:
        mylog('none', ['      ERROR: Failed at - ', failedAt])
        mylog('none', ['      ERROR: Couldn\'t connect to the SMTP server (SMTPServerDisconnected), skipping Email (enable LOG_LEVEL=debug for more logging)'])
        mylog('none', ['      ERROR: ', str(e)])
    except socket.gaierror as e:
        mylog('none', ['      ERROR: Failed at - ', failedAt])
        mylog('none', ['      ERROR: Could not resolve hostname (socket.gaierror), skipping Email (enable LOG_LEVEL=debug for more logging)'])
        mylog('none', ['      ERROR: ', str(e)])                

    mylog('debug', [f'[{pluginName}] Last executed - {str(failedAt)}'])

if __name__ == '__main__':
    sys.exit(main())
