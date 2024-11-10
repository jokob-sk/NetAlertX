#!/usr/bin/env python

import os
import pathlib
import sys
import hashlib
import requests
import json
import sqlite3
import base64


# Define the installation path and extend the system path for plugin imports
INSTALL_PATH = "/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from plugin_helper import Plugin_Object, Plugin_Objects, decodeBase64
from plugin_utils import get_plugins_configs, decode_and_rename_files
from logger import mylog
from const import pluginsPath, fullDbPath
from helper import timeNowTZ, get_setting_value 
from crypto_utils import encrypt_data
from notification import write_notification
import conf
from pytz import timezone

# Make sure the TIMEZONE for logging is correct
conf.tz = timezone(get_setting_value('TIMEZONE'))

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
    api_token = get_setting_value('API_TOKEN')  
    encryption_key = get_setting_value('SYNC_encryption_key')
    hub_url = get_setting_value('SYNC_hub_url')
    node_name = get_setting_value('SYNC_node_name')
    send_devices = get_setting_value('SYNC_devices')
    pull_nodes = get_setting_value('SYNC_nodes')
    
    # variables to determine operation mode
    is_hub  = False
    is_node = False
    
    # Check if api_token set
    if not api_token:
        mylog('verbose', [f'[{pluginName}] ⚠ ERROR api_token not defined - quitting.'])
        return -1

    #  check if this is a hub or a node
    if len(hub_url) > 0 and (send_devices or plugins_to_sync):
        is_node = True   
        mylog('verbose', [f'[{pluginName}] Mode 1: PUSH (NODE) - This is a NODE as SYNC_hub_url, SYNC_devices or SYNC_plugins are set'])    
    if len(pull_nodes) > 0: 
        is_hub = True
        mylog('verbose', [f'[{pluginName}] Mode 2: PULL (HUB) - This is a HUB as SYNC_nodes is set'])    

    # Mode 1: PUSH/SEND (NODE)        
    if is_node:
        # PUSHING/SENDING Plugins    
        
        # Get all plugin configurations
        all_plugins = get_plugins_configs()

        mylog('verbose', [f'[{pluginName}] plugins_to_sync {plugins_to_sync}'])
        
        for plugin in all_plugins:
            pref = plugin["unique_prefix"]  

            index = 0
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
                    
                    
        # PUSHING/SENDING devices
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
        else:
            mylog('verbose', [f'[{pluginName}] SYNC_hub_url not defined, skipping posting "Devices" data']) 
    else:
        mylog('verbose', [f'[{pluginName}] SYNC_hub_url not defined, skipping posting "Plugins" and "Devices" data'])  

    # Mode 2: PULL/GET (HUB)
    
    # PULLING DEVICES 
    
    file_dir = os.path.join(pluginsPath, 'sync')
    file_prefix = 'last_result'
    
    # pull data from nodes if specified
    if is_hub:
        for node_url in pull_nodes:
            response_json = get_data(api_token, node_url)
            
            # Extract node_name and base64 data
            node_name = response_json.get('node_name', 'unknown_node')
            data_base64 = response_json.get('data_base64', '')

            # Decode base64 data
            decoded_data = base64.b64decode(data_base64)
            
            # Create log file name using node name
            log_file_name = f'{file_prefix}.{node_name}.log'

            # Write decoded data to log file
            with open(os.path.join(file_dir, log_file_name), 'wb') as log_file:
                log_file.write(decoded_data)

            message = f'[{pluginName}] Device data from node "{node_name}" written to {log_file_name}'
            mylog('verbose', [message])
            write_notification(message, 'info', timeNowTZ())           
        

    # Process any received data for the Device DB table (ONLY JSON)
    # Create the file path

    # Get all "last_result" files from the sync folder, decode, rename them, and get the list of files
    files_to_process = decode_and_rename_files(file_dir, file_prefix)
    
    if len(files_to_process) > 0:
                
        mylog('verbose', [f'[{pluginName}] Mode 3: RECEIVE (HUB) - This is a HUB as received data found']) 

        # Connect to the App database
        conn    = sqlite3.connect(fullDbPath)
        cursor  = conn.cursor()

        # Collect all unique devMac values from the JSON files
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
                        if device['devMac'] not in unique_mac_addresses:
                            device['devSyncHubNode'] = tmp_SyncHubNodeName
                            unique_mac_addresses.add(device['devMac'])
                            device_data.append(device)    
                            
                # Rename the file to "processed_" + current name
                new_file_name = f"processed_{file_name}"
                new_file_path = os.path.join(file_dir, new_file_name)

                # Overwrite if the new file already exists
                if os.path.exists(new_file_path):
                    os.remove(new_file_path)

                os.rename(file_path, new_file_path)

        if len(device_data) > 0:
            # Retrieve existing devMac values from the Devices table
            placeholders = ', '.join('?' for _ in unique_mac_addresses)
            cursor.execute(f'SELECT devMac FROM Devices WHERE devMac IN ({placeholders})', tuple(unique_mac_addresses))
            existing_mac_addresses = set(row[0] for row in cursor.fetchall())
            

            # insert devices into the lats_result.log to manage state
            for device in device_data:
                if device['devPresentLastScan'] == 1:
                    plugin_objects.add_object(
                        primaryId   = device['devMac'],
                        secondaryId = device['devLastIP'],
                        watched1    = device['devName'],
                        watched2    = device['devVendor'],
                        watched3    = device['devSyncHubNode'],
                        watched4    = device['devGUID'],
                        extra       = '',
                        foreignKey  = device['devGUID'])

            # Filter out existing devices
            new_devices = [device for device in device_data if device['devMac'] not in existing_mac_addresses]

            #  Remove 'rowid' key if it exists 
            for device in new_devices:
                device.pop('rowid', None)

            mylog('verbose', [f'[{pluginName}] All devices: "{len(device_data)}"'])
            mylog('verbose', [f'[{pluginName}] New devices: "{len(new_devices)}"'])

            # Prepare the insert statement
            if new_devices:

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


# send data to the HUB
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
        
# get data from the nodes to the HUB
def get_data(api_token, node_url):
    mylog('verbose', [f'[{pluginName}] Getting data from node: "{node_url}"'])
    
    # Set the authorization header with the API token
    headers = {'Authorization': f'Bearer {api_token}'}
    api_endpoint = f"{node_url}/plugins/sync/hub.php"
    response = requests.get(api_endpoint, headers=headers)

    # mylog('verbose', [f'[{pluginName}] response: "{response.text}"'])

    if response.status_code == 200:
        try:
            # Parse JSON response
            response_json = response.json()
            
            return response_json

        except json.JSONDecodeError:
            message = f'[{pluginName}] Failed to parse JSON response from "{node_url}"'
            mylog('verbose', [message])
            write_notification(message, 'alert', timeNowTZ())
            return ""

    else:
        message = f'[{pluginName}] Failed to send data for "{node_url}" (Status code: {response.status_code})'
        mylog('verbose', [message])
        write_notification(message, 'alert', timeNowTZ())
        return ""



if __name__ == '__main__':
    main()
