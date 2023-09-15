""" Colection of generic functions to support Pi.Alert """

import io
import sys
import datetime
import os
import re
import subprocess
import pytz
from pytz import timezone
from datetime import timedelta
import json
import time
from pathlib import Path
import requests

import conf
from const import *
from logger import mylog, logResult




#-------------------------------------------------------------------------------
def timeNowTZ():
    if isinstance(conf.TIMEZONE, str):
        tz = pytz.timezone(conf.TIMEZONE)
    else:
        tz = conf.TIMEZONE

    return datetime.datetime.now(tz).replace(microsecond=0)

def timeNow():
    return datetime.datetime.now().replace(microsecond=0)


#-------------------------------------------------------------------------------
# A class to manage the application state and to provide a frontend accessible API point
class app_state_class:
    def __init__(self, currentState):
        
        # json file containing the state to communicate with teh frontend
        stateFile = apiPath + '/pialert_app_state.json'

        #  update self
        self.currentState = currentState
        self.lastUpdated = str(timeNowTZ())

        # update .json file
        write_file(stateFile , json.dumps(self, cls=AppStateEncoder)) 

         
    def isSet(self):  

        result = False       

        if self.currentState != "":
            result = True

        return result

#-------------------------------------------------------------------------------
# Checks if the object has a __dict__ attribute. If it does, it assumes that it's an instance of a class and serializes its attributes dynamically. 
class AppStateEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '__dict__'):
            # If the object has a '__dict__', assume it's an instance of a class
            return obj.__dict__
        return super().default(obj)

#-------------------------------------------------------------------------------
def updateState( newState):

    state = app_state_class(newState)

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
def collect_lang_strings(db, json, pref, stringSqlParams):    

    for prop in json["localized"]:
        for language_string in json[prop]:

            stringSqlParams.append((str(language_string["language_code"]), str(pref + "_" + prop), str(language_string["string"]), ""))


    return stringSqlParams


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
def checkIPV4(ip):
    """ Define a function to validate an Ip address
    """
    ipRegex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"

    if(re.search(ipRegex, ip)):
        return True
    else:
        return False


#-------------------------------------------------------------------------------
def isNewVersion(newVersion: bool):

    mylog('debug', [f"[Version check] New version available? {newVersion}"])

    if newVersion == False:

        f = open(pialertPath + '/front/buildtimestamp.txt', 'r')
        buildTimestamp = int(f.read().strip())
        f.close()

        data = ""

        try:
            url = requests.get("https://api.github.com/repos/jokob-sk/Pi.Alert/releases")
            text = url.text
            data = json.loads(text)
        except requests.exceptions.ConnectionError as e:
            mylog('minimal', ["    Couldn't check for new release."])
            data = ""

        # make sure we received a valid response and not an API rate limit exceeded message
        if data != "" and len(data) > 0 and isinstance(data, list) and "published_at" in data[0]:

            dateTimeStr = data[0]["published_at"]

            realeaseTimestamp = int(datetime.datetime.strptime(dateTimeStr, '%Y-%m-%dT%H:%M:%SZ').strftime('%s'))

            if realeaseTimestamp > buildTimestamp + 600:
                mylog('none', ["[Version check] New version of the container available!"])
                newVersion = True                

    return newVersion

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
class noti_struc:
    def __init__(self, json, text, html):
        self.json = json
        self.text = text
        self.html = html        

#-------------------------------------------------------------------------------
def isJsonObject(value):
    return isinstance(value, dict)

#-------------------------------------------------------------------------------
#  Return whole setting touple
def get_setting(key):
    result = None
    # index order: key, name, desc, inputtype, options, regex, result, group, events
    for set in conf.mySettings:
        if set[0] == key:
            result = set
    
    if result is None:
        mylog('minimal', [' Error - setting_missing - Setting not found for key: ', key])           
        mylog('minimal', [' Error - logging the settings into file: ', logPath + '/setting_missing.json'])           
        write_file (logPath + '/setting_missing.json', json.dumps({ 'data' : conf.mySettings}))    

    return result

#-------------------------------------------------------------------------------
#  Return setting value
def get_setting_value(key):
    
    set = get_setting(key)

    if get_setting(key) is not None:

        setVal = set[6] # setting value
        setTyp = set[3] # setting type

        return setVal

    return ''

#-------------------------------------------------------------------------------
# Disclaimer - I'm interfacing with a script I didn't write (pholus3.py) so it's possible I'm missing types of answers
# it's also possible the pholus3.py script can be adjusted to provide a better output to interface with it
# Hit me with a PR if you know how! :)
def resolve_device_name_pholus (pMAC, pIP, allRes):
    
    pholusMatchesIndexes = []

    index = 0
    for result in allRes:
        #  limiting entries used for name resolution to the ones containing the current IP (v4 only)
        if result["MAC"] == pMAC and result["Record_Type"] == "Answer" and result["IP_v4_or_v6"] == pIP and '._googlezone' not in result["Value"]:
            # found entries with a matching MAC address, let's collect indexes             
            pholusMatchesIndexes.append(index)

        index += 1

    # return if nothing found
    if len(pholusMatchesIndexes) == 0:
        return -1

    # we have some entries let's try to select the most useful one

    # airplay matches contain a lot of information
    # Matches for example: 
    # Brand Tv (50)._airplay._tcp.local. TXT Class:32769 "acl=0 deviceid=66:66:66:66:66:66 features=0x77777,0x38BCB46 rsf=0x3 fv=p20.T-FFFFFF-03.1 flags=0x204 model=XXXX manufacturer=Brand serialNumber=XXXXXXXXXXX protovers=1.1 srcvers=777.77.77 pi=FF:FF:FF:FF:FF:FF psi=00000000-0000-0000-0000-FFFFFFFFFF gid=00000000-0000-0000-0000-FFFFFFFFFF gcgl=0 pk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    for i in pholusMatchesIndexes:
        if checkIPV4(allRes[i]['IP_v4_or_v6']) and '._airplay._tcp.local. TXT Class:32769' in str(allRes[i]["Value"]) :
            return allRes[i]["Value"].split('._airplay._tcp.local. TXT Class:32769')[0]
    
    # second best - contains airplay
    # Matches for example: 
    # _airplay._tcp.local. PTR Class:IN "Brand Tv (50)._airplay._tcp.local."
    for i in pholusMatchesIndexes:
        if checkIPV4(allRes[i]['IP_v4_or_v6']) and '_airplay._tcp.local. PTR Class:IN' in allRes[i]["Value"] and ('._googlecast') not in allRes[i]["Value"]:
            return cleanResult(allRes[i]["Value"].split('"')[1])    

    # Contains PTR Class:32769
    # Matches for example: 
    # 3.1.168.192.in-addr.arpa. PTR Class:32769 "MyPc.local."
    for i in pholusMatchesIndexes:
        if checkIPV4(allRes[i]['IP_v4_or_v6']) and 'PTR Class:32769' in allRes[i]["Value"]:
            return cleanResult(allRes[i]["Value"].split('"')[1])

    # Contains AAAA Class:IN
    # Matches for example: 
    # DESKTOP-SOMEID.local. AAAA Class:IN "fe80::fe80:fe80:fe80:fe80"
    for i in pholusMatchesIndexes:
        if checkIPV4(allRes[i]['IP_v4_or_v6']) and 'AAAA Class:IN' in allRes[i]["Value"]:
            return cleanResult(allRes[i]["Value"].split('.local.')[0])

    # Contains _googlecast._tcp.local. PTR Class:IN
    # Matches for example: 
    # _googlecast._tcp.local. PTR Class:IN "Nest-Audio-ff77ff77ff77ff77ff77ff77ff77ff77._googlecast._tcp.local."
    for i in pholusMatchesIndexes:
        if checkIPV4(allRes[i]['IP_v4_or_v6']) and '_googlecast._tcp.local. PTR Class:IN' in allRes[i]["Value"] and ('Google-Cast-Group') not in allRes[i]["Value"]:
            return cleanResult(allRes[i]["Value"].split('"')[1])

    # Contains A Class:32769
    # Matches for example: 
    # Android.local. A Class:32769 "192.168.1.6"
    for i in pholusMatchesIndexes:
        if checkIPV4(allRes[i]['IP_v4_or_v6']) and ' A Class:32769' in allRes[i]["Value"]:
            return cleanResult(allRes[i]["Value"].split(' A Class:32769')[0])

    # # Contains PTR Class:IN
    # Matches for example: 
    # _esphomelib._tcp.local. PTR Class:IN "ceiling-light-1._esphomelib._tcp.local."
    for i in pholusMatchesIndexes:
        if checkIPV4(allRes[i]['IP_v4_or_v6']) and 'PTR Class:IN' in allRes[i]["Value"]:
            if allRes[i]["Value"] and len(allRes[i]["Value"].split('"')) > 1:
                return cleanResult(allRes[i]["Value"].split('"')[1])

    return -1
    
#-------------------------------------------------------------------------------

def resolve_device_name_dig (pMAC, pIP):
    
    newName = ""

    try :
        dig_args = ['dig', '+short', '-x', pIP]

        # Execute command
        try:
            # try runnning a subprocess
            newName = subprocess.check_output (dig_args, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            # An error occured, handle it
            mylog('none', ['[device_name_dig] ', e.output])            
            # newName = "Error - check logs"
            return -1

        # Check returns
        newName = newName.strip()

        if len(newName) == 0 :
            return -1
            
        # Cleanup
        newName = cleanResult(newName)

        if newName == "" or  len(newName) == 0: 
            return -1

        # Return newName
        return newName

    # not Found
    except subprocess.CalledProcessError :
        return -1            

#-------------------------------------------------------------------------------
def cleanResult(str):
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

    return str