""" Colection of functions to support all logging for Pi.Alert """

import datetime
from const import *

#-------------------------------------------------------------------------------
debugLevels =   [
                    ('none', 0), ('minimal', 1), ('verbose', 2), ('debug', 3)
                ]
LOG_LEVEL = 'debug'

def mylog(requestedDebugLevel, n):

    setLvl = 0  
    reqLvl = 0  

    #  Get debug urgency/relative weight
    for lvl in debugLevels:
        if LOG_LEVEL == lvl[0]:
            setLvl = lvl[1]
        if requestedDebugLevel == lvl[0]:
            reqLvl = lvl[1]

    if reqLvl <= setLvl:
        file_print (*n)

#-------------------------------------------------------------------------------
def file_print (*args):

    result = ''    
       
    for arg in args:                
        result += str(arg)
    print(result)

    file = open(logPath + "/pialert.log", "a") 
    file.write(result + '\n')
    file.close()

#-------------------------------------------------------------------------------
def print_log (pText):
    global log_timestamp

    # Check LOG actived
    if not LOG_LEVEL == 'debug' :
        return

    # Current Time    
    log_timestamp2 = datetime.datetime.now().replace(microsecond=0)

    # Print line + time + elapsed time + text
    file_print ('[LOG_LEVEL=debug] ',
        # log_timestamp2, ' ',
        log_timestamp2.strftime ('%H:%M:%S'), ' ',
        pText)
    

    # Save current time to calculate elapsed time until next log
    log_timestamp = log_timestamp2 

    return pText



#-------------------------------------------------------------------------------
def append_file_binary (pPath, input):    
    file = open (pPath, 'ab') 
    file.write (input) 
    file.close() 


#-------------------------------------------------------------------------------
def logResult (stdout, stderr):
    if stderr != None:
        append_file_binary (logPath + '/stderr.log', stderr)
    if stdout != None:
        append_file_binary (logPath + '/stdout.log', stdout)  

