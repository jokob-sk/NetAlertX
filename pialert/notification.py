import datetime
import json
import uuid
import socket
import subprocess
from json2table import convert

# PiAlert modules
import conf
import const
from const import pialertPath, logPath, apiPath
from logger import logResult, mylog, print_log
from helper import generate_mac_links, removeDuplicateNewLines, timeNowTZ, get_file_content, write_file, get_setting_value, get_timezone_offset

#-------------------------------------------------------------------------------
# Notification object handling
#-------------------------------------------------------------------------------
class Notification_obj:
    def __init__(self, db):
        self.db = db

        # Create Notifications table if missing        
        self.db.sql.execute("""CREATE TABLE IF NOT EXISTS "Notifications" (
            "Index"           INTEGER,
            "GUID"            TEXT UNIQUE,
            "DateTimeCreated" TEXT,
            "DateTimePushed"  TEXT,
            "Status"          TEXT,
            "JSON"            TEXT,
            "Text"            TEXT,
            "HTML"            TEXT,
            "PublishedVia"    TEXT,
            "Extra"           TEXT,
            PRIMARY KEY("Index" AUTOINCREMENT)
        );
        """)

        self.save()

    # Create a new DB entry if new notiifcations available, otherwise skip
    def create(self, JSON, Extra=""):        

        #  Write output data for debug
        write_file (logPath + '/report_output.json', json.dumps(JSON))
        
        # Check if nothing to report, end
        if JSON["new_devices"] == [] and JSON["down_devices"] == [] and JSON["events"] == [] and JSON["plugins"] == []:
            self.HasNotifications = False
        else:            
            self.HasNotifications = True 

        self.GUID               = str(uuid.uuid4())
        self.DateTimeCreated    = timeNowTZ()
        self.DateTimePushed     = ""
        self.Status             = "new"
        self.JSON               = JSON
        self.Text               = ""
        self.HTML               = ""
        self.PublishedVia       = ""
        self.Extra              = Extra

        if self.HasNotifications:


            # if not notiStruc.json['data'] and not notiStruc.text and not notiStruc.html:
            #     mylog('debug', '[Notification] notiStruc is empty')
            # else:
            #     mylog('debug', ['[Notification] notiStruc:', json.dumps(notiStruc.__dict__, indent=4)])
            
            Text = ""
            HTML = ""                        


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

            # Start generating the TEXT & HTML notification messages
            html, text = construct_notifications(self.JSON, "new_devices")

            mail_text = mail_text.replace ('<NEW_DEVICES_TABLE>', text + '\n')
            mail_html = mail_html.replace ('<NEW_DEVICES_TABLE>', html)
            mylog('verbose', ['[Notification] New Devices sections done.'])

            html, text = construct_notifications(self.JSON, "down_devices")


            mail_text = mail_text.replace ('<DOWN_DEVICES_TABLE>', text + '\n')
            mail_html = mail_html.replace ('<DOWN_DEVICES_TABLE>', html)
            mylog('verbose', ['[Notification] Down Devices sections done.'])

            html, text = construct_notifications(self.JSON, "events")           
            

            mail_text = mail_text.replace ('<EVENTS_TABLE>', text + '\n')
            mail_html = mail_html.replace ('<EVENTS_TABLE>', html)
            mylog('verbose', ['[Notification] Events sections done.'])    


            html, text = construct_notifications(self.JSON, "plugins")

            mail_text = mail_text.replace ('<PLUGINS_TABLE>', text + '\n')
            mail_html = mail_html.replace ('<PLUGINS_TABLE>', html)
            
            mylog('verbose', ['[Notification] Plugins sections done.'])

            final_text = removeDuplicateNewLines(mail_text)

            # Create clickable MAC links            
            final_html = generate_mac_links (mail_html, conf.REPORT_DASHBOARD_URL + '/deviceDetails.php?mac=')    

            send_api(self.JSON, mail_text, mail_html)

            #  Write output data for debug            
            write_file (logPath + '/report_output.txt', final_text)
            write_file (logPath + '/report_output.html', final_html)

            mylog('minimal', ['[Notification] Udating API files'])

            self.Text               = final_text
            self.HTML               = final_html

            self.upsert()
        
        return self

    # Only updates the status
    def updateStatus(self, newStatus):
        self.Status = newStatus
        self.upsert()

    # Updates the Published properties
    def updatePublishedVia(self, newPublishedVia):
        self.PublishedVia = newPublishedVia
        self.DateTimePushed = timeNowTZ()
        self.upsert()        

    # create or update a notification 
    def upsert(self):
        self.db.sql.execute("""
            INSERT OR REPLACE INTO Notifications (GUID, DateTimeCreated, DateTimePushed, Status, JSON, Text, HTML, PublishedVia, Extra)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (self.GUID, self.DateTimeCreated, self.DateTimePushed, self.Status, json.dumps(self.JSON), self.Text, self.HTML, self.PublishedVia, self.Extra))

        self.save()

    # Remove notification object by GUID
    def remove(self, GUID):
        # Execute an SQL query to delete the notification with the specified GUID
        self.db.sql.execute("""
            DELETE FROM Notifications
            WHERE GUID = ?
        """, (GUID,))
        self.save()

    # Get all with the "new" status
    def getNew(self):
        self.db.sql.execute("""
            SELECT * FROM Notifications
            WHERE Status = "new"
        """)
        return self.db.sql.fetchall()

    # Set all to "processed" status
    def setAllProcessed(self):

        # Execute an SQL query to update the status of all notifications
        self.db.sql.execute("""
            UPDATE Notifications
            SET Status = "processed"
            WHERE Status = "new"
        """)

        self.save()

    def clearPendingEmailFlag(self):

        # Clean Pending Alert Events
        self.db.sql.execute ("""UPDATE Devices SET dev_LastNotification = ?
                            WHERE dev_MAC IN (
                                SELECT eve_MAC FROM Events
                                    WHERE eve_PendingAlertEmail = 1
                            )
                        """, (timeNowTZ(),) )

        self.db.sql.execute ("""UPDATE Events SET eve_PendingAlertEmail = 0
                                    WHERE eve_PendingAlertEmail = 1 
                                    AND eve_EventType !='Device Down' """)

        # Clear down events flag after the reporting window passed
        self.db.sql.execute (f"""UPDATE Events SET eve_PendingAlertEmail = 0
                                    WHERE eve_PendingAlertEmail = 1 
                                    AND eve_EventType =='Device Down' 
                                    AND eve_DateTime < datetime('now', '-{get_setting_value('NTFPRCS_alert_down_time')} minutes', '{get_timezone_offset()}')
                            """)

        # clear plugin events
        self.db.sql.execute ("DELETE FROM Plugins_Events")

        # DEBUG - print number of rows updated
        mylog('minimal', ['[Notification] Notifications changes: ', self.db.sql.rowcount])    

        self.save()

    def save(self):
        # Commit changes
        self.db.commitDB()

#-------------------------------------------------------------------------------
# Reporting
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
def construct_notifications(JSON, section):

    jsn         = JSON[section]

    # Return if empty
    if jsn == []:
        return '',''

    tableTitle  = JSON[section + "_meta"]["title"]
    headers     = JSON[section + "_meta"]["columnNames"]

    html = ''
    text = ''

    table_attributes = {"style" : "border-collapse: collapse; font-size: 12px; color:#70707", "width" : "100%", "cellspacing" : 0, "cellpadding" : "3px", "bordercolor" : "#C0C0C0", "border":"1"}
    headerProps = "width='120px' style='color:white; font-size: 16px;' bgcolor='#64a0d6' "
    thProps = "width='120px' style='color:#F0F0F0' bgcolor='#64a0d6' "

    build_direction = "TOP_TO_BOTTOM"
    text_line = '{}\t{}\n'


    if len(jsn) > 0:
        text = tableTitle + "\n---------\n"

        # Convert a JSON into an HTML table
        html = convert({"data": jsn}, build_direction=build_direction, table_attributes=table_attributes)
        
        # Cleanup the generated HTML table notification
        html = format_table(html, "data", headerProps, tableTitle).replace('<ul>','<ul style="list-style:none;padding-left:0">').replace("<td>null</td>", "<td></td>")        

        # prepare text-only message
        for device in jsn:
            for header in headers:
                padding = ""
                if len(header) < 4:
                    padding = "\t"
                text += text_line.format ( header + ': ' + padding, device[header])
            text += '\n'

        #  Format HTML table headers
        for header in headers:
            html = format_table(html, header, thProps)

    return html, text

#-------------------------------------------------------------------------------
def send_api(json_final, mail_text, mail_html):
        mylog('verbose', ['[Send API] Updating notification_* files in ', apiPath])

        write_file(apiPath + 'notification_text.txt'  , mail_text)
        write_file(apiPath + 'notification_text.html'  , mail_html)
        write_file(apiPath + 'notification_json_final.json'  , json.dumps(json_final))



#-------------------------------------------------------------------------------
# Replacing table headers
def format_table (html, thValue, props, newThValue = ''):

    if newThValue == '':
        newThValue = thValue

    return html.replace("<th>"+thValue+"</th>", "<th "+props+" >"+newThValue+"</th>" )



