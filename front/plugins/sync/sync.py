#!/usr/bin/env python

import os
import pathlib
import sys
import hashlib
import requests
import json
import sqlite3


# Define the installation path and extend the system path for plugin imports
INSTALL_PATH = "/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from plugin_helper import Plugin_Object, Plugin_Objects, decodeBase64
from plugin_utils import get_plugins_configs, decode_and_rename_files
from logger import mylog
from const import pluginsPath, fullDbPath
from helper import timeNowTZ, get_setting_value 
from cryptography import encrypt_data
from notification import write_notification

# Define the current path and log file paths
CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
LOG_FILE = os.path.join(CUR_PATH, 'script.log')
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

# Initialize the Plugin obj output file
plugin_objects = Plugin_Objects(RESULT_FILE)

pluginName = 'SYNC'

def main():
    mylog('verbose', [f'[{pluginName}] In script']) 

    # Retrieve configuration settings
    plugins_to_sync = get_setting_value('SYNC_plugins')
    api_token = get_setting_value('SYNC_api_token')  
    encryption_key = get_setting_value('SYNC_encryption_key')
    hub_url = get_setting_value('SYNC_hub_url')
    node_name = get_setting_value('SYNC_node_name')
    send_devices = get_setting_value('SYNC_devices')

    # Get all plugin configurations
    all_plugins = get_plugins_configs()

    mylog('verbose', [f'[{pluginName}] plugins_to_sync {plugins_to_sync}'])

    # Plugins processing
    index = 0
    for plugin in all_plugins:
        pref = plugin["unique_prefix"]  

        if pref in plugins_to_sync:
            index += 1
            mylog('verbose', [f'[{pluginName}] synching "{pref}" ({index}/{len(plugins_to_sync)})'])

            # Construct the file path for the plugin's last_result.log file
            plugin_folder = plugin["code_name"]
            file_path = f"{INSTALL_PATH}/front/plugins/{plugin_folder}/last_result.log"

            if os.path.exists(file_path):
                # Read the content of the log file
                with open(file_path, 'r') as f:
                    file_content = f.read()

                    mylog('verbose', [f'[{pluginName}] Sending file_content: "{file_content}"'])

                    # encrypt and send data to the hub
                    send_data(api_token, file_content, encryption_key, plugin_folder, node_name, pref, hub_url)

            else:
                mylog('verbose', [f'[{pluginName}] {plugin_folder}/last_result.log not found'])             

    # Devices procesing
    if send_devices:

        file_path = f"{INSTALL_PATH}/front/api/table_devices.json"
        plugin_folder = 'sync'
        pref = 'SYNC'

        if os.path.exists(file_path):
            # Read the content of the log file
            with open(file_path, 'r') as f:
                file_content = f.read()

                mylog('verbose', [f'[{pluginName}] Sending file_content: "{file_content}"'])
                send_data(api_token, file_content, encryption_key, plugin_folder, node_name, pref, hub_url)

    # process any received data for the Device DB table
    # Create the file path
    file_dir = os.path.join(pluginsPath, 'sync')
    file_prefix = 'last_result'

    # Decode files, rename them, and get the list of files
    files_to_process = decode_and_rename_files(file_dir, file_prefix)

    # Connect to the App database
    conn    = sqlite3.connect(fullDbPath)
    cursor  = conn.cursor()

    # Collect all unique dev_MAC values from the JSON files
    unique_mac_addresses = set()
    device_data = []

    mylog('verbose', [f'[{pluginName}] Devices files to process: "{files_to_process}"'])

    for file_name in files_to_process:

        # only process received .log files, skipping the one logging the progress of this plugin
        if file_name != 'last_result.log':
            mylog('verbose', [f'[{pluginName}] Processing: "{file_name}"'])

            # Store e.g. Node_1 from last_result.encoded.Node_1.1.log
            tmp_SyncHubNodeName = ''
            if len(file_name.split('.')) > 3:
                tmp_SyncHubNodeName = file_name.split('.')[2]   


            file_path = f"{INSTALL_PATH}/front/plugins/sync/{file_name}"
            
            with open(file_path, 'r') as f:
                data = json.load(f)
                for device in data['data']:
                    if device['dev_MAC'] not in unique_mac_addresses:
                        device['dev_SyncHubNodeName'] = tmp_SyncHubNodeName
                        unique_mac_addresses.add(device['dev_MAC'])
                        device_data.append(device)

    if len(device_data) > 0:
        # Retrieve existing dev_MAC values from the Devices table
        placeholders = ', '.join('?' for _ in unique_mac_addresses)
        cursor.execute(f'SELECT dev_MAC FROM Devices WHERE dev_MAC IN ({placeholders})', tuple(unique_mac_addresses))
        existing_mac_addresses = set(row[0] for row in cursor.fetchall())

        # Filter out existing devices
        new_devices = [device for device in device_data if device['dev_MAC'] not in existing_mac_addresses]

        #  Remove 'rowid' key if it exists 
        for device in new_devices:
            device.pop('rowid', None)


        # Prepare the insert statement
        if new_devices:
            # insert devices into the lats_result.log to manage state
            for device in new_devices:
                plugin_objects.add_object(
                    primaryId   = device['dev_MAC'],
                    secondaryId = device['dev_LastIP'],
                    watched1    = device['dev_Name'],
                    watched2    = device['dev_Vendor'],
                    watched3    = device['dev_SyncHubNodeName'],
                    watched4    = device['dev_GUID'],
                    extra       = '',
                    foreignKey  = device['dev_GUID'])

            columns = ', '.join(k for k in new_devices[0].keys() if k != 'rowid')
            placeholders = ', '.join('?' for k in new_devices[0] if k != 'rowid')
            sql = f'INSERT INTO Devices ({columns}) VALUES ({placeholders})'

            # Extract values for the new devices
            values = [tuple(device.values()) for device in new_devices]

            mylog('verbose', [f'[{pluginName}] Inserting Devices SQL   : "{sql}"'])
            mylog('verbose', [f'[{pluginName}] Inserting Devices VALUES: "{values}"'])

            # Use executemany for batch insertion
            cursor.executemany(sql, values)

            message = f'[{pluginName}] Inserted "{len(new_devices)}" new devices'

            mylog('verbose', [message])
            write_notification(message, 'info', timeNowTZ())

    # Commit and close the connection
    conn.commit()
    conn.close()

    # log result
    plugin_objects.write_result_file()

    return 0


def send_data(api_token, file_content, encryption_key, plugin_folder, node_name, pref, hub_url):
    # Encrypt the log data using the encryption_key
    encrypted_data = encrypt_data(file_content, encryption_key)

    mylog('verbose', [f'[{pluginName}] Sending encrypted_data: "{encrypted_data}"'])

    # Prepare the data payload for the POST request
    data = {
        'data': encrypted_data,
        'plugin_folder': plugin_folder,
        'node_name': node_name
    }
    # Set the authorization header with the API token
    headers = {'Authorization': f'Bearer {api_token}'}
    api_endpoint = f"{hub_url}/plugins/sync/hub.php"
    response = requests.post(api_endpoint, data=data, headers=headers)

    mylog('verbose', [f'[{pluginName}] response: "{response}"'])

    if response.status_code == 200:
        message = f'[{pluginName}] Data for "{plugin_folder}" sent successfully'
        mylog('verbose', [message])
        write_notification(message, 'info', timeNowTZ())
    else:
        message = f'[{pluginName}] Failed to send data for "{plugin_folder}" (Status code: {response.status_code})'
        mylog('verbose', [message])
        write_notification(message, 'alert', timeNowTZ())



if __name__ == '__main__':
    main()
