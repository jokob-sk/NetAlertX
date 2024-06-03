#!/usr/bin/env python

import os
import pathlib
import sys
import hashlib
import requests


# Define the installation path and extend the system path for plugin imports
INSTALL_PATH = "/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from plugin_helper import Plugin_Object, Plugin_Objects, decodeBase64
from plugin_utils import get_plugins_configs
from logger import mylog
from helper import timeNowTZ, get_setting_value

# Define the current path and log file paths
CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
LOG_FILE = os.path.join(CUR_PATH, 'script.log')
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')

pluginName = 'SYNC'

# Function to encrypt data using a password
def encrypt_data(data, password):
    key = hashlib.sha256(password.encode()).digest()
    cipher = hashlib.pbkdf2_hmac('sha256', data.encode(), key, 100000)
    return cipher.hex()

def main():
    mylog('verbose', [f'[{pluginName}] In script']) 


    # Initialize the Plugin obj output file
    plugin_objects = Plugin_Objects(RESULT_FILE)

    # Retrieve configuration settings
    plugins_to_sync = get_setting_value('SYNC_plugins')
    api_token = get_setting_value('SYNC_api_token')  # Use an API token instead of a password
    hub_url = get_setting_value('SYNC_hub_url')
    node_name = get_setting_value('SYNC_node_name')

    # Get all plugin configurations
    all_plugins = get_plugins_configs()

    mylog('verbose', [f'[{pluginName}] DEBUG {len(all_plugins)}'])
    mylog('verbose', [f'[{pluginName}] plugins_to_sync {plugins_to_sync}'])

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
                    newLines = f.read()
                    # Encrypt the log data using the API token
                    encrypted_data = encrypt_data(newLines, api_token)

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
                        mylog('verbose', [f'[{pluginName}] Data for "{plugin_folder}" sent successfully'])
                    else:
                        mylog('error', [f'[{pluginName}] Failed to send data for "{plugin_folder}"'])

                    # log result
                    plugin_objects.add_object(
                        primaryId   = pref,
                        secondaryId = timeNowTZ(),
                        watched1    = node_name,
                        watched2    = response.status_code,
                        watched3    = response.text,
                        watched4    = '',
                        extra       = '',
                        foreignKey  = '')
            else:
                mylog('verbose', [f'[{pluginName}] {plugin_folder}/last_result.log not found'])             

    # log result
    plugin_objects.write_result_file()

    return 0

if __name__ == '__main__':
    main()
