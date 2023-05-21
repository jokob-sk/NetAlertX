""" Colection of generic functions to support Pi.Alert """
import datetime
import os
import subprocess

from const import *
from logger import mylog, logResult

#-------------------------------------------------------------------------------
def timeNow():
    return datetime.datetime.now().replace(microsecond=0)

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