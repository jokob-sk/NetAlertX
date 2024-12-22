import sys
import io
import datetime
import threading
import queue
import time
import conf
from const import *

#-------------------------------------------------------------------------------
# duplication from helper to avoid circle
#-------------------------------------------------------------------------------
def timeNowTZ():
    if conf.tz:
        return datetime.datetime.now(conf.tz).replace(microsecond=0)
    else:
        return datetime.datetime.now().replace(microsecond=0)

#-------------------------------------------------------------------------------
# More verbose as the numbers go up
debugLevels = [
    ('none', 0), ('minimal', 1), ('verbose', 2), ('debug', 3), ('trace', 4)
]

# use the LOG_LEVEL from the config, may be overridden
currentLevel = conf.LOG_LEVEL

#-------------------------------------------------------------------------------
class Logger:
    def __init__(self, LOG_LEVEL='verbose'):        
        global currentLevel

        currentLevel = LOG_LEVEL


def mylog(requestedDebugLevel, n):
    setLvl = 0  
    reqLvl = 0  

    #  Get debug urgency/relative weight
    for lvl in debugLevels:
        if currentLevel == lvl[0]:
            setLvl = lvl[1]
        if requestedDebugLevel == lvl[0]:
            reqLvl = lvl[1]

    if reqLvl <= setLvl:
        file_print (*n)        

#-------------------------------------------------------------------------------
# Queue for log messages
log_queue = queue.Queue(maxsize=1000)  # Increase size to handle spikes

# Dedicated thread for writing logs
log_thread = None  # Will hold the thread reference

def log_writer():
    buffer = []
    while True:
        try:
            log_entry = log_queue.get(timeout=1)  # Wait for 1 second for logs
            if log_entry is None:  # Graceful exit signal
                break
            buffer.append(log_entry)
            if len(buffer) >= 10:  # Write in batches of 10
                with open(logPath + "/app.log", 'a') as log_file:
                    log_file.write('\n'.join(buffer) + '\n')
                buffer.clear()
        except queue.Empty:
            # Flush buffer periodically if no new logs
            if buffer:
                with open(logPath + "/app.log", 'a') as log_file:
                    log_file.write('\n'.join(buffer) + '\n')
                buffer.clear()

#-------------------------------------------------------------------------------
# Function to start the log writer thread if it doesn't exist
def start_log_writer_thread():
    global log_thread
    if log_thread is None or not log_thread.is_alive():
        log_thread = threading.Thread(target=log_writer, daemon=True)
        log_thread.start()

#-------------------------------------------------------------------------------
def file_print(*args):
    result = timeNowTZ().strftime('%H:%M:%S') + ' '   
    
    for arg in args:                
        result += str(arg)        
    print(result)

    # Ensure the log writer thread is running
    start_log_writer_thread()

    # Queue the log entry for writing
    append_to_file_with_timeout( result, 5)

#-------------------------------------------------------------------------------
# Function to append to the file with a timeout
def append_to_file_with_timeout(data, timeout):
    try:
        log_queue.put_nowait(data)
    except queue.Full:
        print("Log queue is full, dropping log entry:" + data)

#-------------------------------------------------------------------------------
def print_log(pText):
    # Check if logging is active
    if not conf.LOG_LEVEL == 'debug':
        return

    # Current Time    
    log_timestamp2 = datetime.datetime.now(conf.tz).replace(microsecond=0)

    # Print line + time + text
    file_print('[LOG_LEVEL=debug]', log_timestamp2.strftime('%H:%M:%S'), pText)
    return pText

#-------------------------------------------------------------------------------
def append_file_binary(file_path, input_data):
    with open(file_path, 'ab') as file:
        if isinstance(input_data, str):
            input_data = input_data.encode('utf-8')  # Encode string as bytes
        file.write(input_data)

#-------------------------------------------------------------------------------
def logResult(stdout, stderr):
    if stderr is not None:
        append_file_binary(logPath + '/stderr.log', stderr)
    if stdout is not None:
        append_file_binary(logPath + '/stdout.log', stdout)

#-------------------------------------------------------------------------------
def append_line_to_file(pPath, pText):
    # append the line using the correct python version
    if sys.version_info < (3, 0):
        file = io.open(pPath, mode='a', encoding='utf-8')
        file.write(pText.decode('unicode_escape'))
        file.close() 
    else:
        file = open(pPath, 'a', encoding='utf-8') 
        file.write(pText)
        file.close()  
