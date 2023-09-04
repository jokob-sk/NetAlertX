""" Colection of functions to support all logging for Pi.Alert """
import sys
import io
import datetime

import conf
from const import *
# from helper import get_setting_value

#-------------------------------------------------------------------------------
# duplication from helper to avoid circle
#-------------------------------------------------------------------------------
def timeNowTZ():
    if conf.tz:
        return datetime.datetime.now(conf.tz).replace(microsecond=0)
    else:
        return datetime.datetime.now().replace(microsecond=0)


# conf.LOG_LEVEL = get_setting_value("LOG_LEVEL")

#-------------------------------------------------------------------------------
debugLevels =   [
                    ('none', 0), ('minimal', 1), ('verbose', 2), ('debug', 3)
                ]

def mylog(requestedDebugLevel, n):

    setLvl = 0  
    reqLvl = 0  

    #  Get debug urgency/relative weight
    for lvl in debugLevels:
        if conf.LOG_LEVEL == lvl[0]:
            setLvl = lvl[1]
        if requestedDebugLevel == lvl[0]:
            reqLvl = lvl[1]

    if reqLvl <= setLvl:
        file_print (*n)        

#-------------------------------------------------------------------------------
def file_print (*args):

    result = timeNowTZ().strftime ('%H:%M:%S') + ' '    
       
    for arg in args:                
        result += str(arg)
    print(result)

    try:
        # Set a timeout for opening the file (in seconds)
        file_open_timeout = 10

        with open(os.path.join(logPath, "pialert.log"), "a", timeout=file_open_timeout) as file:
            file.write(result + '\n')
    except Exception as e:
        print(f"Error opening/writing to the file: {e}")

#-------------------------------------------------------------------------------
def print_log (pText):

    # Check LOG actived
    if not conf.LOG_LEVEL == 'debug' :
        return

    # Current Time    
    log_timestamp2 = datetime.datetime.now(conf.tz).replace(microsecond=0)

    # Print line + time + elapsed time + text
    file_print ('[LOG_LEVEL=debug] ',
        # log_timestamp2, ' ',
        log_timestamp2.strftime ('%H:%M:%S'), ' ',
        pText)


    return pText



#-------------------------------------------------------------------------------
# textchars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
# is_binary_string = lambda bytes: bool(bytes.translate(None, textchars))

def append_file_binary(file_path, input_data):
    with open(file_path, 'ab') as file:
        if isinstance(input_data, str):
            input_data = input_data.encode('utf-8')  # Encode string as bytes
        file.write(input_data)



#-------------------------------------------------------------------------------
def logResult (stdout, stderr):
    if stderr != None:
        append_file_binary (logPath + '/stderr.log', stderr)
    if stdout != None:
        append_file_binary (logPath + '/stdout.log', stdout)  

#-------------------------------------------------------------------------------
def append_line_to_file (pPath, pText):
    # append the line depending using the correct python version
    if sys.version_info < (3, 0):
        file = io.open (pPath , mode='a', encoding='utf-8')
        file.write ( pText.decode('unicode_escape') ) 
        file.close() 
    else:
        file = open (pPath, 'a', encoding='utf-8') 
        file.write (pText) 
        file.close() 