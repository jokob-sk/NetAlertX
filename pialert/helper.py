""" Colection of generic functions to support Pi.Alert """

import io
import sys
import datetime
# from datetime import strptime 
import os
import re
import subprocess
import pytz
from pytz import timezone
import json
import time
from pathlib import Path
import requests

import conf
from const import *
from logger import mylog, logResult

#-------------------------------------------------------------------------------
# DateTime
#-------------------------------------------------------------------------------
# Get the current time in the current TimeZone
def timeNowTZ():
    if conf.tz:
        return datetime.datetime.now(conf.tz).replace(microsecond=0)
    else:
        return datetime.datetime.now().replace(microsecond=0)
    # if isinstance(conf.TIMEZONE, str):
    #     tz = pytz.timezone(conf.TIMEZONE)
    # else:
    #     tz = conf.TIMEZONE

    # return datetime.datetime.now(tz).replace(microsecond=0)

def timeNow():
    return datetime.datetime.now().replace(microsecond=0)

def get_timezone_offset():    
    now = datetime.datetime.now(conf.tz)
    offset_hours = now.utcoffset().total_seconds() / 3600        
    offset_formatted =  "{:+03d}:{:02d}".format(int(offset_hours), int((offset_hours % 1) * 60))
    return offset_formatted


#-------------------------------------------------------------------------------
# App state
#-------------------------------------------------------------------------------
# A class to manage the application state and to provide a frontend accessible API point
class app_state_class:
    def __init__(self, currentState, settingsSaved=None, settingsImported=None, showSpinner=False):
        # json file containing the state to communicate with the frontend
        stateFile = apiPath + '/app_state.json'

        # if currentState == 'Initializing':
        #     checkNewVersion(False)

        # Update self
        self.currentState = currentState
        self.lastUpdated = str(timeNowTZ())

        # Check if the file exists and init values
        if os.path.exists(stateFile):
            with open(stateFile, 'r') as json_file:
                previousState               = json.load(json_file)
                self.settingsSaved          = previousState.get("settingsSaved", 0)
                self.settingsImported       = previousState.get("settingsImported", 0)
                self.showSpinner            = previousState.get("showSpinner", False)
                self.isNewVersion           = previousState.get("isNewVersion", False)
                self.isNewVersionChecked    = previousState.get("isNewVersionChecked", 0)
        else:
            self.settingsSaved          = 0
            self.settingsImported       = 0
            self.showSpinner            = False
            self.isNewVersion           = checkNewVersion()
            self.isNewVersionChecked    = int(timeNow().timestamp())

        # Overwrite with provided parameters if supplied
        if settingsSaved is not None:
            self.settingsSaved = settingsSaved
        if settingsImported is not None:
            self.settingsImported = settingsImported
        if showSpinner is not None:
            self.showSpinner = showSpinner

        # check for new version every hour and if currently not running new version
        if self.isNewVersion is False and self.isNewVersionChecked + 3600 < int(timeNow().timestamp()):
            self.isNewVersion           = checkNewVersion()
            self.isNewVersionChecked    = int(timeNow().timestamp())

        # Update .json file
        with open(stateFile, 'w') as json_file:
            json.dump(self, json_file, cls=AppStateEncoder, indent=4)

         
    def isSet(self):  

        result = False       

        if self.currentState != "":
            result = True

        return result


#-------------------------------------------------------------------------------
# method to update the state
def updateState(newState, settingsSaved = None, settingsImported = None, showSpinner = False):

    state = app_state_class(newState, settingsSaved, settingsImported, showSpinner)


#-------------------------------------------------------------------------------
def updateSubnets(scan_subnets):
    subnets = []

    # multiple interfaces
    if type(scan_subnets) is list:
        for interface in scan_subnets :
            subnets.append(interface)
    # one interface only
    else:
        subnets.append(scan_subnets)

    return subnets



#-------------------------------------------------------------------------------
# File system permission handling
#-------------------------------------------------------------------------------
# check RW access of DB and config file
def checkPermissionsOK():
    #global confR_access, confW_access, dbR_access, dbW_access

    confR_access = (os.access(fullConfPath, os.R_OK))
    confW_access = (os.access(fullConfPath, os.W_OK))
    dbR_access = (os.access(fullDbPath, os.R_OK))
    dbW_access = (os.access(fullDbPath, os.W_OK))

    mylog('none', ['\n'])
    mylog('none', ['The container restarted (started). If this is unexpected check https://bit.ly/PiAlertDebug for troubleshooting tips.'])
    mylog('none', ['\n'])
    mylog('none', ['Permissions check (All should be True)'])
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
                mylog('none', ["[Setup] ⚠ ERROR copying ("+defaultFile+") to ("+pathToCheck+"). Make sure the app has Read & Write access to the parent directory."])
            else:
                mylog('none', ["[Setup] ("+defaultFile+") copied over successfully to ("+pathToCheck+")."])

            # write stdout and stderr into .log files for debugging if needed
            logResult (stdout, stderr)  # TO-DO should be changed to mylog

        except subprocess.CalledProcessError as e:
            # An error occured, handle it
            mylog('none', ["[Setup] ⚠ ERROR copying ("+defaultFile+"). Make sure the app has Read & Write access to " + pathToCheck])
            mylog('none', [e.output])

#-------------------------------------------------------------------------------
def filePermissions():
    # check and initialize pialert.conf
    (confR_access, dbR_access) = checkPermissionsOK() # Initial check

    if confR_access == False:
        initialiseFile(fullConfPath, "/home/pi/pialert/back/pialert.conf" )

    # check and initialize pialert.db
    if dbR_access == False:
        initialiseFile(fullDbPath, "/home/pi/pialert/back/pialert.db")

    # last attempt
    fixPermissions()


#-------------------------------------------------------------------------------
# File manipulation methods
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def get_file_content(path):

    f = open(path, 'r')
    content = f.read()
    f.close()

    return content

#-------------------------------------------------------------------------------
def write_file(pPath, pText):
    # Convert pText to a string if it's a dictionary
    if isinstance(pText, dict):
        pText = json.dumps(pText)

    # Convert pText to a string if it's a list
    if isinstance(pText, list):
        for item in pText:
            write_file(pPath, item)

    else:
        # Write the text using the correct Python version
        if sys.version_info < (3, 0):
            file = io.open(pPath, mode='w', encoding='utf-8')
            file.write(pText.decode('unicode_escape'))
            file.close()
        else:
            file = open(pPath, 'w', encoding='utf-8')
            if pText is None:
                pText = ""
            file.write(pText)
            file.close()

#-------------------------------------------------------------------------------
# Setting methods
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#  Return whole setting touple
def get_setting(key):

    settingsFile = apiPath + 'table_settings.json'

    try:
        with open(settingsFile, 'r') as json_file:

            data = json.load(json_file)

            for item in data.get("data",[]):
                if item.get("Code_Name") == key:
                    return item

            mylog('debug', [f'[Settings] ⚠ ERROR - setting_missing - Setting not found for key: {key} in file {settingsFile}'])  

            return None

    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        # Handle the case when the file is not found, JSON decoding fails, or data is not in the expected format
        mylog('none', [f'[Settings] ⚠ ERROR - JSONDecodeError or FileNotFoundError for file {settingsFile}'])                

        return None



#-------------------------------------------------------------------------------
#  Return setting value
def get_setting_value(key):
    
    setting = get_setting(key)

    value = ''

    if setting is not None:

        # mylog('none', [f'[SETTINGS] setting json:{json.dumps(setting)}'])        

        set_type  = 'Error: Not handled'
        set_value = 'Error: Not handled'

        set_value = setting["Value"]  # Setting value
        set_type = setting["Type"]  # Setting type        

        # Handle different types of settings
        if set_type in ['text', 'string', 'password', 'readonly', 'text.select']:
            value = str(set_value)
        elif set_type in ['boolean', 'integer.checkbox']:
            
            value = False

            if isinstance(set_value, str) and set_value.lower() in ['true', '1']:
                value = True
            elif isinstance(set_value, int) and set_value == 1:
                value = True
            elif isinstance(set_value, bool):
                value = set_value
            
        elif set_type in ['integer.select', 'integer']:
            value = int(set_value)
        elif set_type in ['text.multiselect', 'list', 'subnets']:
            # Assuming set_value is a list in this case
            value = set_value
        elif set_type == '.template':
            # Assuming set_value is a JSON object in this case
            value = json.loads(set_value)
        else:
            mylog('none', [f'[SETTINGS] ⚠ ERROR - set_type not handled:{set_type}'])
            mylog('none', [f'[SETTINGS] ⚠ ERROR - setting json:{json.dumps(setting)}'])


    return value




#-------------------------------------------------------------------------------
# IP validation methods
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def checkIPV4(ip):
    """ Define a function to validate an Ip address
    """
    ipRegex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"

    if(re.search(ipRegex, ip)):
        return True
    else:
        return False

#-------------------------------------------------------------------------------
def check_IP_format (pIP):
    # check if TCP communication error ocurred 
    if 'communications error to' in pIP:
        return ''

    # Check IP format 
    IPv4SEG  = r'(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])'
    IPv4ADDR = r'(?:(?:' + IPv4SEG + r'\.){3,3}' + IPv4SEG + r')'
    IP = re.search(IPv4ADDR, pIP)

    # Return empty if not IP
    if IP is None :
        return ""

    # Return IP
    return IP.group(0)



#-------------------------------------------------------------------------------
def resolve_device_name_dig (pMAC, pIP):
    
    nameNotFound = "(name not found)"

    dig_args = ['dig', '+short', '-x', pIP]

    # Execute command
    try:
        # try runnning a subprocess
        newName = subprocess.check_output (dig_args, universal_newlines=True)

        # Check returns
        newName = newName.strip()

        if len(newName) == 0 :
            return nameNotFound
            
        # Cleanup
        newName = cleanDeviceName(newName, True)

        if newName == "" or  len(newName) == 0 or newName == '-1' or newName == -1 or "communications error" in newName: 
            return nameNotFound

        # all checks passed
        mylog('debug', [f'[resolve_device_name_dig] Found a new name: "{newName}"'])  

        return newName

    except subprocess.CalledProcessError as e:
        # An error occured, handle it
        mylog('none', ['[resolve_device_name_dig] ⚠ ERROR: ', e.output])            
        # newName = "Error - check logs"
        return nameNotFound


#-------------------------------------------------------------------------------
# DNS record (Pholus/Name resolution) cleanup methods
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Disclaimer - I'm interfacing with a script I didn't write (pholus3.py) so it's possible I'm missing types of answers
# it's also possible the pholus3.py script can be adjusted to provide a better output to interface with it
# Hit me with a PR if you know how! :)
def resolve_device_name_pholus (pMAC, pIP, allRes, nameNotFound, match_IP = False):
    
    pholusMatchesIndexes = []

    result = nameNotFound

    # Collect all Pholus entries  with matching MAC and of type Answer
    index = 0
    for result in allRes:
        #  limiting entries used for name resolution to the ones containing the current IP (v4 only)
        if ((match_IP and result["IP_v4_or_v6"] == pIP ) or ( result["MAC"] == pMAC )) and result["Record_Type"] == "Answer" and '._googlezone' not in result["Value"]:
            # found entries with a matching MAC address, let's collect indexes             
            pholusMatchesIndexes.append(index)

        index += 1

    # return if nothing found
    if len(pholusMatchesIndexes) == 0:
        return nameNotFound   

    # we have some entries let's try to select the most useful one
    # Do I need to pre-order allRes to have the most valuable onse on the top?

    for i in pholusMatchesIndexes:
        if not checkIPV4(allRes[i]['IP_v4_or_v6']):
            continue

        value = allRes[i]["Value"]

        # airplay matches contain a lot of information
        # Matches for example:
        # Brand Tv (50)._airplay._tcp.local. TXT Class:32769 "acl=0 deviceid=66:66:66:66:66:66 features=0x77777,0x38BCB46 rsf=0x3 fv=p20.T-FFFFFF-03.1 flags=0x204 model=XXXX manufacturer=Brand serialNumber=XXXXXXXXXXX protovers=1.1 srcvers=777.77.77 pi=FF:FF:FF:FF:FF:FF psi=00000000-0000-0000-0000-FFFFFFFFFF gid=00000000-0000-0000-0000-FFFFFFFFFF gcgl=0 pk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        if '._airplay._tcp.local. TXT Class:32769' in value:
            return cleanDeviceName(value.split('._airplay._tcp.local. TXT Class:32769')[0], match_IP)
        
        # second best - contains airplay
        # Matches for example:
        # _airplay._tcp.local. PTR Class:IN "Brand Tv (50)._airplay._tcp.local."
        if '_airplay._tcp.local. PTR Class:IN' in value and ('._googlecast') not in value:
            return cleanDeviceName(value.split('"')[1], match_IP)    

        # Contains PTR Class:32769
        # Matches for example:
        # 3.1.168.192.in-addr.arpa. PTR Class:32769 "MyPc.local."
        if 'PTR Class:32769' in value:
            return cleanDeviceName(value.split('"')[1], match_IP)

        # Contains AAAA Class:IN
        # Matches for example:
        # DESKTOP-SOMEID.local. AAAA Class:IN "fe80::fe80:fe80:fe80:fe80"
        if 'AAAA Class:IN' in value:
            return cleanDeviceName(value.split('.local.')[0], match_IP)

        # Contains _googlecast._tcp.local. PTR Class:IN
        # Matches for example:
        # _googlecast._tcp.local. PTR Class:IN "Nest-Audio-ff77ff77ff77ff77ff77ff77ff77ff77._googlecast._tcp.local."
        if '_googlecast._tcp.local. PTR Class:IN' in value and ('Google-Cast-Group') not in value:
            return cleanDeviceName(value.split('"')[1], match_IP)

        # Contains A Class:32769
        # Matches for example:
        # Android.local. A Class:32769 "192.168.1.6"
        if ' A Class:32769' in value:
            return cleanDeviceName(value.split(' A Class:32769')[0], match_IP)

        # Contains PTR Class:IN
        # Matches for example:
        # _esphomelib._tcp.local. PTR Class:IN "ceiling-light-1._esphomelib._tcp.local."
        if 'PTR Class:IN' in value and len(value.split('"')) > 1:
            return cleanDeviceName(value.split('"')[1], match_IP)

    return nameNotFound
    
    

#-------------------------------------------------------------------------------
def cleanDeviceName(str, match_IP):
    # alternative str.split('.')[0]
    str = str.replace("._airplay", "")
    str = str.replace("._tcp", "")
    str = str.replace(".local", "")
    str = str.replace("._esphomelib", "")
    str = str.replace("._googlecast", "")
    str = str.replace(".lan", "")
    str = str.replace(".home", "")
    str = re.sub(r'-[a-fA-F0-9]{32}', '', str)    # removing last part of e.g. Nest-Audio-ff77ff77ff77ff77ff77ff77ff77ff77
    str = re.sub(r'#.*', '', str) # Remove everything after '#' including the '#'
    # remove trailing dots
    if str.endswith('.'):
        str = str[:-1]


    if match_IP:
        str = str + " (IP match)"

    return str


#-------------------------------------------------------------------------------
# String manipulation methods
#-------------------------------------------------------------------------------

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
def hide_email(email):
    m = email.split('@')

    if len(m) == 2:
        return f'{m[0][0]}{"*"*(len(m[0])-2)}{m[0][-1] if len(m[0]) > 1 else ""}@{m[1]}'

    return email

#-------------------------------------------------------------------------------
def hide_string(input_string):
    if len(input_string) < 3:
        return input_string  # Strings with 2 or fewer characters remain unchanged
    else:
        return input_string[0] + "*" * (len(input_string) - 2) + input_string[-1]


#-------------------------------------------------------------------------------
def removeDuplicateNewLines(text):
    if "\n\n\n" in text:
        return removeDuplicateNewLines(text.replace("\n\n\n", "\n\n"))
    else:
        return text

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
# JSON methods
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
def isJsonObject(value):
    return isinstance(value, dict)

#-------------------------------------------------------------------------------
def add_json_list (row, list):
    new_row = []
    for column in row :
        column = bytes_to_string(column)

        new_row.append(column)

    list.append(new_row)

    return list


#-------------------------------------------------------------------------------
# Checks if the object has a __dict__ attribute. If it does, it assumes that it's an instance of a class and serializes its attributes dynamically. 
class AppStateEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '__dict__'):
            # If the object has a '__dict__', assume it's an instance of a class
            return obj.__dict__
        return super().default(obj)

#-------------------------------------------------------------------------------
# Checks if the object has a __dict__ attribute. If it does, it assumes that it's an instance of a class and serializes its attributes dynamically. 
class NotiStrucEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '__dict__'):
            # If the object has a '__dict__', assume it's an instance of a class
            return obj.__dict__
        return super().default(obj)

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
# Get language strings from plugin JSON
def collect_lang_strings(json, pref, stringSqlParams):    

    for prop in json["localized"]:
        for language_string in json[prop]:

            stringSqlParams.append((str(language_string["language_code"]), str(pref + "_" + prop), str(language_string["string"]), ""))


    return stringSqlParams


#-------------------------------------------------------------------------------
#  Misc
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
def checkNewVersion():

    mylog('debug', [f"[Version check] Checking if new version available"])

    newVersion = False

    f = open(pialertPath + '/front/buildtimestamp.txt', 'r')
    buildTimestamp = int(f.read().strip())
    f.close()

    data = ""

    try:
        url = requests.get("https://api.github.com/repos/jokob-sk/Pi.Alert/releases")
        text = url.text
        data = json.loads(text)
    except requests.exceptions.ConnectionError as e:
        mylog('minimal', ["[Version check] ⚠ ERROR: Couldn't check for new release."])
        data = ""

    # make sure we received a valid response and not an API rate limit exceeded message
    if data != "" and len(data) > 0 and isinstance(data, list) and "published_at" in data[0]:

        dateTimeStr = data[0]["published_at"]

        releaseTimestamp = int(datetime.datetime.strptime(dateTimeStr, '%Y-%m-%dT%H:%M:%S%z').timestamp())

        if releaseTimestamp > buildTimestamp + 600:
            mylog('none', ["[Version check] New version of the container available!"])
            newVersion = True       
        else:
            mylog('none', ["[Version check] Running the latest version."])

    return newVersion


#-------------------------------------------------------------------------------
def initOrSetParam(db, parID, parValue):
    sql = db.sql

    sql.execute ("INSERT INTO Parameters(par_ID, par_Value) VALUES('"+str(parID)+"', '"+str(parValue)+"') ON CONFLICT(par_ID) DO UPDATE SET par_Value='"+str(parValue)+"' where par_ID='"+str(parID)+"'")

    db.commitDB()

#-------------------------------------------------------------------------------
class json_obj:
    def __init__(self, jsn, columnNames):
        self.json = jsn
        self.columnNames = columnNames

#-------------------------------------------------------------------------------
class noti_obj:
    def __init__(self, json, text, html):
        self.json = json
        self.text = text
        self.html = html  

