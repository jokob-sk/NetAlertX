""" Colection of generic functions to support Pi.Alert """

import datetime
import os
import re
import subprocess
from cron_converter import Cron
from pytz import timezone
from datetime import timedelta
import json
import time
from pathlib import Path
import requests




from const import *
from conf import tz
from logger import mylog, logResult, print_log
# from api import update_api  # to avoid circular reference



#-------------------------------------------------------------------------------
def timeNow():
    return datetime.datetime.now().replace(microsecond=0)

#-------------------------------------------------------------------------------
def updateState(db, newState):    
    #sql = db.sql

    mylog('debug', '       [updateState] changing state to: "' + newState +'"')
    db.sql.execute ("UPDATE Parameters SET par_Value='"+ newState +"' WHERE par_ID='Back_App_State'")        

    db.commitDB()
#-------------------------------------------------------------------------------
def updateSubnets(SCAN_SUBNETS):

    #  remove old list
    userSubnets = []  

    # multiple interfaces
    if type(SCAN_SUBNETS) is list:        
        for interface in SCAN_SUBNETS :            
            userSubnets.append(interface)
    # one interface only
    else:        
        userSubnets.append(SCAN_SUBNETS)    



#-------------------------------------------------------------------------------
# check RW access of DB and config file
def checkPermissionsOK():
    #global confR_access, confW_access, dbR_access, dbW_access
    
    confR_access = (os.access(fullConfPath, os.R_OK))
    confW_access = (os.access(fullConfPath, os.W_OK))
    dbR_access = (os.access(fullDbPath, os.R_OK))
    dbW_access = (os.access(fullDbPath, os.W_OK))


    mylog('none', ['\n Permissions check (All should be True)'])
    mylog('none', ['------------------------------------------------'])
    mylog('none', [ "  " , confPath ,     " | " , " READ  | " , confR_access])
    mylog('none', [ "  " , confPath ,     " | " , " WRITE | " , confW_access])
    mylog('none', [ "  " , dbPath , "       | " , " READ  | " , dbR_access])
    mylog('none', [ "  " , dbPath , "       | " , " WRITE | " , dbW_access])
    mylog('none', ['------------------------------------------------'])

    #return dbR_access and dbW_access and confR_access and confW_access 
    return (confR_access, dbR_access) 
#-------------------------------------------------------------------------------
def fixPermissions():
    # Try fixing access rights if needed
    chmodCommands = []
    
    chmodCommands.append(['sudo', 'chmod', 'a+rw', '-R', fullDbPath])    
    chmodCommands.append(['sudo', 'chmod', 'a+rw', '-R', fullConfPath])

    for com in chmodCommands:
        # Execute command
        mylog('none', ["[Setup] Attempting to fix permissions."])
        try:
            # try runnning a subprocess
            result = subprocess.check_output (com, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            # An error occured, handle it
            mylog('none', ["[Setup] Fix Failed. Execute this command manually inside of the container: ", ' '.join(com)]) 
            mylog('none', [e.output])


#-------------------------------------------------------------------------------
def initialiseFile(pathToCheck, defaultFile):
    # if file not readable (missing?) try to copy over the backed-up (default) one
    if str(os.access(pathToCheck, os.R_OK)) == "False":
        mylog('none', ["[Setup] ("+ pathToCheck +") file is not readable or missing. Trying to copy over the default one."])
        try:
            # try runnning a subprocess
            p = subprocess.Popen(["cp", defaultFile , pathToCheck], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            stdout, stderr = p.communicate()

            if str(os.access(pathToCheck, os.R_OK)) == "False":
                mylog('none', ["[Setup] Error copying ("+defaultFile+") to ("+pathToCheck+"). Make sure the app has Read & Write access to the parent directory."])
            else:
                mylog('none', ["[Setup] ("+defaultFile+") copied over successfully to ("+pathToCheck+")."])

            # write stdout and stderr into .log files for debugging if needed
            logResult (stdout, stderr)  # TO-DO should be changed to mylog
            
        except subprocess.CalledProcessError as e:
            # An error occured, handle it
            mylog('none', ["[Setup] Error copying ("+defaultFile+"). Make sure the app has Read & Write access to " + pathToCheck])
            mylog('none', [e.output])


def filePermissions():
    # check and initialize pialert.conf
    (confR_access, dbR_access) = checkPermissionsOK() # Initial check

    if confR_access == False:
        initialiseFile(fullConfPath, "/home/pi/pialert/back/pialert.conf_bak" )

    # check and initialize pialert.db
    if dbR_access == False:
        initialiseFile(fullDbPath, "/home/pi/pialert/back/pialert.db_bak")

    # last attempt
    fixPermissions()            

#-------------------------------------------------------------------------------
class schedule_class:
    def __init__(self, service, scheduleObject, last_next_schedule, was_last_schedule_used, last_run = 0):
        self.service = service
        self.scheduleObject = scheduleObject
        self.last_next_schedule = last_next_schedule
        self.last_run = last_run
        self.was_last_schedule_used = was_last_schedule_used          
    def runScheduleCheck(self):

        result = False 

        # Initialize the last run time if never run before
        if self.last_run == 0:
            self.last_run =  (datetime.datetime.now(tz) - timedelta(days=365)).replace(microsecond=0)

        # get the current time with the currently specified timezone
        nowTime = datetime.datetime.now(tz).replace(microsecond=0)

        # Run the schedule if the current time is past the schedule time we saved last time and 
        #               (maybe the following check is unnecessary:)
        # if the last run is past the last time we run a scheduled Pholus scan
        if nowTime > self.last_next_schedule and self.last_run < self.last_next_schedule:
            print_log(f'Scheduler run for {self.service}: YES')
            self.was_last_schedule_used = True
            result = True
        else:
            print_log(f'Scheduler run for {self.service}: NO')
        
        if self.was_last_schedule_used:
            self.was_last_schedule_used = False
            self.last_next_schedule = self.scheduleObject.next()            

        return result
    
  


#-------------------------------------------------------------------------------

def bytes_to_string(value):
    # if value is of type bytes, convert to string
    if isinstance(value, bytes):
        value = value.decode('utf-8')
    return value        

#-------------------------------------------------------------------------------

def if_byte_then_to_str(input):
    if isinstance(input, bytes):
        input = input.decode('utf-8')
        input = bytes_to_string(re.sub('[^a-zA-Z0-9-_\s]', '', str(input)))
    return input

#-------------------------------------------------------------------------------
def collect_lang_strings(db, json, pref):

    for prop in json["localized"]:                   
        for language_string in json[prop]:
            import_language_string(db, language_string["language_code"], pref + "_" + prop, language_string["string"])       






     

#-------------------------------------------------------------------------------
#  Creates a JSON object from a DB row
def row_to_json(names, row):  
    
    rowEntry = {}

    index = 0
    for name in names:
        rowEntry[name]= if_byte_then_to_str(row[name])
        index += 1

    return rowEntry

#-------------------------------------------------------------------------------
def import_language_string(db, code, key, value, extra = ""):

    db.sql.execute ("""INSERT INTO Plugins_Language_Strings ("Language_Code", "String_Key", "String_Value", "Extra") VALUES (?, ?, ?, ?)""", (str(code), str(key), str(value), str(extra))) 

    db.commitDB()



#-------------------------------------------------------------------------------
# Make a regular expression
# for validating an Ip-address
ipRegex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"

# Define a function to
# validate an Ip address
def checkIPV4(ip):
    # pass the regular expression
    # and the string in search() method
    if(re.search(ipRegex, ip)):
        return True
    else:
        return False


#-------------------------------------------------------------------------------
def isNewVersion(db):   
    global newVersionAvailable

    if newVersionAvailable == False:    

        f = open(pialertPath + '/front/buildtimestamp.txt', 'r') 
        buildTimestamp = int(f.read().strip())
        f.close() 

        data = ""

        try:
            url = requests.get("https://api.github.com/repos/jokob-sk/Pi.Alert/releases")
            text = url.text
            data = json.loads(text)
        except requests.exceptions.ConnectionError as e:
            mylog('info', ["    Couldn't check for new release."]) 
            data = ""
        
        # make sure we received a valid response and not an API rate limit exceeded message
        if data != "" and len(data) > 0 and isinstance(data, list) and "published_at" in data[0]:        

            dateTimeStr = data[0]["published_at"]            

            realeaseTimestamp = int(datetime.datetime.strptime(dateTimeStr, '%Y-%m-%dT%H:%M:%SZ').strftime('%s'))            

            if realeaseTimestamp > buildTimestamp + 600:        
                mylog('none', ["    New version of the container available!"])
                newVersionAvailable = True 
                # updateState(db, 'Back_New_Version_Available', str(newVersionAvailable))     ## TO DO add this back in but avoid circular ref with database

    return newVersionAvailable

#-------------------------------------------------------------------------------
def hide_email(email):
    m = email.split('@')

    if len(m) == 2:
        return f'{m[0][0]}{"*"*(len(m[0])-2)}{m[0][-1] if len(m[0]) > 1 else ""}@{m[1]}'

    return email    

#-------------------------------------------------------------------------------
def removeDuplicateNewLines(text):
    if "\n\n\n" in text:
        return removeDuplicateNewLines(text.replace("\n\n\n", "\n\n"))
    else:
        return text

#-------------------------------------------------------------------------------

def add_json_list (row, list):
    new_row = []
    for column in row :        
        column = bytes_to_string(column)

        new_row.append(column)

    list.append(new_row)    

    return list        

#-------------------------------------------------------------------------------

def sanitize_string(input):
    if isinstance(input, bytes):
        input = input.decode('utf-8')
    value = bytes_to_string(re.sub('[^a-zA-Z0-9-_\s]', '', str(input)))
    return value


#-------------------------------------------------------------------------------
def generate_mac_links (html, deviceUrl):

    p = re.compile(r'(?:[0-9a-fA-F]:?){12}')

    MACs = re.findall(p, html)

    for mac in MACs:        
        html = html.replace('<td>' + mac + '</td>','<td><a href="' + deviceUrl + mac + '">' + mac + '</a></td>')

    return html



#-------------------------------------------------------------------------------
def initOrSetParam(db, parID, parValue):    
    sql = db.sql

    sql.execute ("INSERT INTO Parameters(par_ID, par_Value) VALUES('"+str(parID)+"', '"+str(parValue)+"') ON CONFLICT(par_ID) DO UPDATE SET par_Value='"+str(parValue)+"' where par_ID='"+str(parID)+"'")        

    db.commitDB()    

#-------------------------------------------------------------------------------
class json_struc:
    def __init__(self, jsn, columnNames):        
        self.json = jsn
        self.columnNames = columnNames     