""" Pi.Alert module to send notification emails """

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib


import conf
from helper import hide_email, noti_struc
from logger import mylog, print_log

#-------------------------------------------------------------------------------
def check_config ():
    if conf.SMTP_SERVER == '' or conf.REPORT_FROM == '' or conf.REPORT_TO == '':
        mylog('none', ['[Email Check Config] Error: Email service not set up correctly. Check your pialert.conf SMTP_*, REPORT_FROM and REPORT_TO variables.'])
        return False
    else:
        return True
    
#-------------------------------------------------------------------------------
def send (msg: noti_struc):

    pText = msg.text
    pHTML = msg.html

    mylog('debug', '[Send Email] REPORT_TO: ' + hide_email(str(conf.REPORT_TO)) + '  SMTP_USER: ' + hide_email(str(conf.SMTP_USER)))

    # Compose email
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Pi.Alert Report'
    msg['From'] = conf.REPORT_FROM
    msg['To'] = conf.REPORT_TO
    msg.attach (MIMEText (pText, 'plain'))
    msg.attach (MIMEText (pHTML, 'html'))

    failedAt = ''

    failedAt = print_log ('SMTP try')

    try:
        # Send mail
        failedAt = print_log('Trying to open connection to ' + str(conf.SMTP_SERVER) + ':' + str(conf.SMTP_PORT))

        if conf.SMTP_FORCE_SSL:
            failedAt = print_log('SMTP_FORCE_SSL == True so using .SMTP_SSL()')
            if conf.SMTP_PORT == 0:
                failedAt = print_log('SMTP_PORT == 0 so sending .SMTP_SSL(SMTP_SERVER)')
                smtp_connection = smtplib.SMTP_SSL(conf.SMTP_SERVER)
            else:
                failedAt = print_log('SMTP_PORT == 0 so sending .SMTP_SSL(SMTP_SERVER, SMTP_PORT)')
                smtp_connection = smtplib.SMTP_SSL(conf.SMTP_SERVER, conf.SMTP_PORT)

        else:
            failedAt = print_log('SMTP_FORCE_SSL == False so using .SMTP()')
            if conf.SMTP_PORT == 0:
                failedAt = print_log('SMTP_PORT == 0 so sending .SMTP(SMTP_SERVER)')
                smtp_connection = smtplib.SMTP (conf.SMTP_SERVER)
            else:
                failedAt = print_log('SMTP_PORT == 0 so sending .SMTP(SMTP_SERVER, SMTP_PORT)')
                smtp_connection = smtplib.SMTP (conf.SMTP_SERVER, conf.SMTP_PORT)

        failedAt = print_log('Setting SMTP debug level')

        # Log level set to debug of the communication between SMTP server and client
        if conf.LOG_LEVEL == 'debug':
            smtp_connection.set_debuglevel(1)

        failedAt = print_log( 'Sending .ehlo()')
        smtp_connection.ehlo()

        if not conf.SMTP_SKIP_TLS:
            failedAt = print_log('SMTP_SKIP_TLS == False so sending .starttls()')
            smtp_connection.starttls()
            failedAt = print_log('SMTP_SKIP_TLS == False so sending .ehlo()')
            smtp_connection.ehlo()
        if not conf.SMTP_SKIP_LOGIN:
            failedAt = print_log('SMTP_SKIP_LOGIN == False so sending .login()')
            smtp_connection.login (conf.SMTP_USER, conf.SMTP_PASS)

        failedAt = print_log('Sending .sendmail()')
        smtp_connection.sendmail (conf.REPORT_FROM, conf.REPORT_TO, msg.as_string())
        smtp_connection.quit()
    except smtplib.SMTPAuthenticationError as e:
        mylog('none', ['      ERROR: Failed at - ', failedAt])
        mylog('none', ['      ERROR: Couldn\'t connect to the SMTP server (SMTPAuthenticationError), skipping Email (enable LOG_LEVEL=debug for more logging)'])
    except smtplib.SMTPServerDisconnected as e:
        mylog('none', ['      ERROR: Failed at - ', failedAt])
        mylog('none', ['      ERROR: Couldn\'t connect to the SMTP server (SMTPServerDisconnected), skipping Email (enable LOG_LEVEL=debug for more logging)'])

    mylog('debug', '[Send Email] Last executed - ' + str(failedAt))