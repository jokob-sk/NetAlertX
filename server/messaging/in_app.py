import datetime
import os
import sys
import _io
import json
import uuid
import socket
import subprocess
import requests
from yattag import indent
from json2table import convert

# Register NetAlertX directories
INSTALL_PATH="/app"
sys.path.extend([f"{INSTALL_PATH}/server"])

# Register NetAlertX modules 

import conf
from const import applicationPath, logPath, apiPath, confFileName, reportTemplatesPath
from logger import logResult, mylog
from helper import generate_mac_links, removeDuplicateNewLines, timeNowTZ, get_file_content, write_file, get_setting_value, get_timezone_offset

NOTIFICATION_API_FILE = apiPath + 'user_notifications.json'

# Show Frontend User Notification
def write_notification(content, level, timestamp):        

        # Generate GUID
        guid = str(uuid.uuid4())

        # Prepare notification dictionary
        notification = {
            'timestamp': str(timestamp),
            'guid': guid,
            'read': 0,
            'level': level,
            'content': content
        }

        # If file exists, load existing data, otherwise initialize as empty list
        if os.path.exists(NOTIFICATION_API_FILE):
            with open(NOTIFICATION_API_FILE, 'r') as file:
                # Check if the file object is of type _io.TextIOWrapper
                if isinstance(file, _io.TextIOWrapper):
                    file_contents = file.read()  # Read file contents
                    if file_contents == '':
                        file_contents = '[]'  # If file is empty, initialize as empty list

                    # mylog('debug', ['[Notification] User Notifications file: ', file_contents])
                    notifications = json.loads(file_contents)  # Parse JSON data
                else:
                    mylog('none', '[Notification] File is not of type _io.TextIOWrapper')
                    notifications = []
        else:
            notifications = []

        # Append new notification
        notifications.append(notification)

        # Write updated data back to file
        with open(NOTIFICATION_API_FILE, 'w') as file:
            json.dump(notifications, file, indent=4)

# Trim notifications
def remove_old(keepNumberOfEntries):

    # Check if file exists
    if not os.path.exists(NOTIFICATION_API_FILE):
        mylog('info', '[Notification] No notifications file to clean.')
        return

    # Load existing notifications
    try:
        with open(NOTIFICATION_API_FILE, 'r') as file:
            file_contents = file.read().strip()
            if file_contents == '':
                notifications = []
            else:
                notifications = json.loads(file_contents)
    except Exception as e:
        mylog('none', f'[Notification] Error reading notifications file: {e}')
        return

    if not isinstance(notifications, list):
        mylog('none', '[Notification] Invalid format: not a list')
        return

    # Sort by timestamp descending
    try:
        notifications.sort(key=lambda x: x['timestamp'], reverse=True)
    except KeyError:
        mylog('none', '[Notification] Missing timestamp in one or more entries')
        return

    # Trim to the latest entries
    trimmed = notifications[:keepNumberOfEntries]

    # Write back the trimmed list
    try:
        with open(NOTIFICATION_API_FILE, 'w') as file:
            json.dump(trimmed, file, indent=4)
        mylog('verbose', f'[Notification] Trimmed notifications to latest {keepNumberOfEntries}')
    except Exception as e:
        mylog('none', f'Error writing trimmed notifications file: {e}')
