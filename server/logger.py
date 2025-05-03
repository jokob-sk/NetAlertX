import sys
import io
import datetime
import threading
import queue
import time
import logging

# NetAlertX imports

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
# Map custom debug levels to Python logging levels
custom_to_logging_levels = {
    'none': logging.NOTSET,
    'minimal': logging.WARNING,
    'verbose': logging.INFO,
    'debug': logging.DEBUG,
    'trace': logging.DEBUG,  # Can map to DEBUG or lower custom level if needed
}

#-------------------------------------------------------------------------------
# More verbose as the numbers go up
debugLevels = [
    ('none', 0), ('minimal', 1), ('verbose', 2), ('debug', 3), ('trace', 4)
]

# use the LOG_LEVEL from the config, may be overridden
currentLevel = conf.LOG_LEVEL

# tracking log levels
setLvl = 0  
reqLvl = 0  

#-------------------------------------------------------------------------------
class Logger:
    def __init__(self, LOG_LEVEL):        
        global currentLevel

        currentLevel = LOG_LEVEL
        conf.LOG_LEVEL = currentLevel

        # Automatically set up custom logging handler
        self.setup_logging()

    def setup_logging(self):
        root_logger = logging.getLogger()
        # Clear existing handlers to prevent duplicates
        if root_logger.hasHandlers():
            root_logger.handlers.clear()

        # Create the custom handler
        my_log_handler = MyLogHandler()
        # my_log_handler.setLevel(custom_to_logging_levels.get(currentLevel, logging.NOTSET))

        # Optional: Add a formatter for consistent log message format
        # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        formatter = logging.Formatter('%(message)s', datefmt='%H:%M:%S')
        my_log_handler.setFormatter(formatter)

        # Attach the handler to the root logger
        root_logger.addHandler(my_log_handler)
        root_logger.setLevel(custom_to_logging_levels.get(currentLevel, logging.NOTSET))

# for python logging
class MyLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        log_queue.put(log_entry)

def mylog(requestedDebugLevel, n):
    global setLvl, reqLvl  

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

    logging.log(custom_to_logging_levels.get(currentLevel, logging.NOTSET), result)  # Forward to Python's logging system 
    print(result)

    # Ensure the log writer thread is running
    start_log_writer_thread()


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
