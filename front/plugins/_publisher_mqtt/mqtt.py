#!/usr/bin/env python

import json
import subprocess
import argparse
import os
import pathlib
import sys
from datetime import datetime
import time
import re
from paho.mqtt import client as mqtt_client
import hashlib


# Replace these paths with the actual paths to your Pi.Alert directories
sys.path.extend(["/home/pi/pialert/front/plugins", "/home/pi/pialert/pialert"])

#  PiAlert modules
import conf
from const import apiPath
from plugin_utils import getPluginObject
from plugin_helper import Plugin_Objects
from logger import mylog, append_line_to_file
from helper import timeNowTZ, get_setting_value, bytes_to_string, sanitize_string
from notification import Notification_obj
from database import DB, get_all_devices, get_device_stats


CUR_PATH = str(pathlib.Path(__file__).parent.resolve())
RESULT_FILE = os.path.join(CUR_PATH, 'last_result.log')


# Initialize the Plugin obj output file
plugin_objects = Plugin_Objects(RESULT_FILE)
# Create an MD5 hash object
md5_hash = hashlib.md5()

pluginName = 'MQTT'
module_name = pluginName

# globals

mqtt_sensors                = []
mqtt_connected_to_broker    = False
client                      = None  # mqtt client

def main():
    
    mylog('verbose', [f'[{pluginName}](publisher) In script'])    
    
    # Check if basic config settings supplied
    if check_config() == False:
        mylog('none', [f'[{pluginName}] ⚠ ERROR: Publisher notification gateway not set up correctly. Check your pialert.conf {pluginName}_* variables.'])
        return

    # Create a database connection
    db = DB()  # instance of class DB
    db.open()

    mqtt_start(db)

    plugin_objects.write_result_file()



#-------------------------------------------------------------------------------
# MQTT
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def check_config():
        if get_setting_value('MQTT_BROKER') == '' or get_setting_value('MQTT_PORT') == '' or get_setting_value('MQTT_USER') == '' or get_setting_value('MQTT_PASSWORD') == '':
            mylog('none', ['[Check Config] ⚠ ERROR: MQTT service not set up correctly. Check your pialert.conf MQTT_* variables.'])
            return False
        else:
            return True


#-------------------------------------------------------------------------------
class sensor_config:
    def __init__(self, deviceId, deviceName, sensorType, sensorName, icon, mac):
        self.deviceId = deviceId
        self.deviceName = deviceName
        self.sensorType = sensorType
        self.sensorName = sensorName
        self.icon = icon 

        # Define your input string
        input_string = str(deviceId) + str(deviceName) + str(sensorType) + str(sensorName) + str(icon)

        # Hash the input string and convert the hash to a string
        # Update the hash object with the bytes of the input string
        md5_hash.update(input_string.encode('utf-8'))

        # Get the hexadecimal representation of the MD5 hash
        md5_hash_hex = md5_hash.hexdigest()
        hash_value = str(md5_hash_hex)

        self.hash = hash_value

        plugObj = getPluginObject({"Plugin":"MQTT", "Watched_Value3":hash_value}) 

        # mylog('verbose', [f"[{pluginName}] Previous plugin object entry: {json.dumps(plugObj)}"])        

        if plugObj == {}:
            self.isNew = True
            mylog('verbose', [f"[{pluginName}] New sensor entry mac          : {mac}"])  
            mylog('verbose', [f"[{pluginName}] New sensor entry input_string : {input_string}"])  
            mylog('verbose', [f"[{pluginName}] New sensor entry hash_value   : {hash_value}"])  
        else:
            self.isNew = False


        # Log sensor
        global plugin_objects

        if mac == '':
            mac = "N/A"

        plugin_objects.add_object(
            primaryId   = deviceId,
            secondaryId = sensorName,            
            watched1    = deviceName,
            watched2    = sensorType,            
            watched3    = hash_value,
            watched4    = mac,
            extra       = input_string,
            foreignKey  = mac
        )

#-------------------------------------------------------------------------------

def publish_mqtt(client, topic, message):
    status = 1
    while status != 0:
        result = client.publish(
                topic=topic,
                payload=message,
                qos=get_setting_value('MQTT_QOS'),
                retain=True,
            )

        status = result[0]

        if status != 0:            
            mylog('minimal', [f"[{pluginName}] Waiting to reconnect to MQTT broker"])
            time.sleep(0.1) 
    return True

#-------------------------------------------------------------------------------
def create_generic_device(client):  
    
    deviceName = 'PiAlert'
    deviceId = 'pialert'    
    
    create_sensor(client, deviceId, deviceName, 'sensor', 'online', 'wifi-check')    
    create_sensor(client, deviceId, deviceName, 'sensor', 'down', 'wifi-cancel')        
    create_sensor(client, deviceId, deviceName, 'sensor', 'all', 'wifi')
    create_sensor(client, deviceId, deviceName, 'sensor', 'archived', 'wifi-lock')
    create_sensor(client, deviceId, deviceName, 'sensor', 'new', 'wifi-plus')
    create_sensor(client, deviceId, deviceName, 'sensor', 'unknown', 'wifi-alert')
        

#-------------------------------------------------------------------------------

def create_sensor(client, deviceId, deviceName, sensorType, sensorName, icon, mac=""):    

    global mqtt_sensors    

    new_sensor_config = sensor_config(deviceId, deviceName, sensorType, sensorName, icon, mac) 
           
    # save if new
    if new_sensor_config.isNew:   
        mylog('minimal', [f"[{pluginName}] Publishing sensor number {len(mqtt_sensors)}"])          
        publish_sensor(client, new_sensor_config)        




#-------------------------------------------------------------------------------
def publish_sensor(client, sensorConfig):      

    global mqtt_sensors   

    message = '{ \
                "name":"'+sensorConfig.sensorName+'", \
                "state_topic":"system-sensors/'+sensorConfig.sensorType+'/'+sensorConfig.deviceId+'/state", \
                "value_template":"{{value_json.'+sensorConfig.sensorName+'}}", \
                "unique_id":"'+sensorConfig.deviceId+'_sensor_'+sensorConfig.sensorName+'", \
                "device": \
                    { \
                        "identifiers": ["'+sensorConfig.deviceId+'_sensor"], \
                        "manufacturer": "PiAlert", \
                        "name":"'+sensorConfig.deviceName+'" \
                    }, \
                "icon":"mdi:'+sensorConfig.icon+'" \
                }'

    topic='homeassistant/'+sensorConfig.sensorType+'/'+sensorConfig.deviceId+'/'+sensorConfig.sensorName+'/config'

    # add the sensor to the global list to keep track of succesfully added sensors
    if publish_mqtt(client, topic, message):        
                                     # hack - delay adding to the queue in case the process is 
        time.sleep(get_setting_value('MQTT_DELAY_SEC'))   # restarted and previous publish processes aborted 
                                     # (it takes ~2s to update a sensor config on the broker)
        mqtt_sensors.append(sensorConfig)

#-------------------------------------------------------------------------------
def mqtt_create_client():    
    def on_disconnect(client, userdata, rc):
        
        global mqtt_connected_to_broker

        mqtt_connected_to_broker = False
        
        # not sure is below line is correct / necessary        
        # client = mqtt_create_client() 

    def on_connect(client, userdata, flags, rc):
        
        global mqtt_connected_to_broker

        if rc == 0: 
            mylog('verbose', [f"[{pluginName}]         Connected to broker"])            
            mqtt_connected_to_broker = True     # Signal connection 
        else: 
            mylog('none', [f"[{pluginName}]         Connection failed"])
            mqtt_connected_to_broker = False


    global client

    client = mqtt_client.Client('PiAlert')   # Set Connecting Client ID    
    client.username_pw_set(get_setting_value('MQTT_USER'), get_setting_value('MQTT_PASSWORD'))    
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.connect(get_setting_value('MQTT_BROKER'), get_setting_value('MQTT_PORT'))
    client.loop_start() 

    return client

#-------------------------------------------------------------------------------
def mqtt_start(db):    

    global client, mqtt_connected_to_broker

    if mqtt_connected_to_broker == False:
        mqtt_connected_to_broker = True           
        client = mqtt_create_client()     
    
    # General stats    

    # Create a generic device for overal stats
    create_generic_device(client)

    # Get the data
    row = get_device_stats(db)   

    columns = ["online","down","all","archived","new","unknown"]

    payload = ""

    # Update the values 
    for column in columns:       
        payload += '"'+column+'": ' + str(row[column]) +','       

    # Publish (warap into {} and remove last ',' from above)
    publish_mqtt(client, "system-sensors/sensor/pialert/state",              
            '{ \
                '+ payload[:-1] +'\
            }'
        )


    # Specific devices

    # Get all devices
    devices = get_all_devices(db)

    sec_delay = len(devices) * int(get_setting_value('MQTT_DELAY_SEC'))*5

    mylog('minimal', [f"[{pluginName}]         Estimated delay: ", (sec_delay), 's ', '(', round(sec_delay/60,1) , 'min)' ])

    
    for device in devices:      

    
        # Create devices in Home Assistant - send config messages
        deviceId = 'mac_' + device["dev_MAC"].replace(" ", "").replace(":", "_").lower()
        deviceNameDisplay = re.sub('[^a-zA-Z0-9-_\s]', '', device["dev_Name"]) 

        create_sensor(client, deviceId, deviceNameDisplay, 'sensor', 'last_ip', 'ip-network', device["dev_MAC"])
        create_sensor(client, deviceId, deviceNameDisplay, 'binary_sensor', 'is_present', 'wifi', device["dev_MAC"])
        create_sensor(client, deviceId, deviceNameDisplay, 'sensor', 'mac_address', 'folder-key-network', device["dev_MAC"])
        create_sensor(client, deviceId, deviceNameDisplay, 'sensor', 'is_new', 'bell-alert-outline', device["dev_MAC"])
        create_sensor(client, deviceId, deviceNameDisplay, 'sensor', 'vendor', 'cog', device["dev_MAC"])
    
        # update device sensors in home assistant              

        publish_mqtt(client, 'system-sensors/sensor/'+deviceId+'/state', 
            '{ \
                "last_ip": "' + device["dev_LastIP"] +'", \
                "is_new": "' + str(device["dev_NewDevice"]) +'", \
                "vendor": "' + sanitize_string(device["dev_Vendor"]) +'", \
                "mac_address": "' + str(device["dev_MAC"]) +'" \
            }'
        ) 

        publish_mqtt(client, 'system-sensors/binary_sensor/'+deviceId+'/state', 
            '{ \
                "is_present": "' + to_binary_sensor(str(device["dev_PresentLastScan"])) +'"\
            }'
        ) 

        # delete device / topic
        #  homeassistant/sensor/mac_44_ef_bf_c4_b1_af/is_present/config
        # client.publish(
        #     topic="homeassistant/sensor/"+deviceId+"/is_present/config",
        #     payload="",
        #     qos=1,
        #     retain=True,
        # )        
    # time.sleep(10)


#===============================================================================
# Home Assistant UTILs
#===============================================================================
def to_binary_sensor(input):
    # In HA a binary sensor returns ON or OFF    
    result = "OFF"

    # bytestring
    if isinstance(input, str):
        if input == "1":
            result = "ON"
    elif isinstance(input, int):
        if input == 1:
            result = "ON"
    elif isinstance(input, bool):
        if input == True:
            result = "ON"
    elif isinstance(input, bytes):
        if bytes_to_string(input) == "1":
            result = "ON"
    return result




#  -------------INIT---------------------
if __name__ == '__main__':
    sys.exit(main())



