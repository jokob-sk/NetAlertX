
import time
import re
from paho.mqtt import client as mqtt_client

from logger import mylog
from conf import MQTT_BROKER, MQTT_DELAY_SEC, MQTT_PASSWORD, MQTT_PORT, MQTT_QOS, MQTT_USER
from database import get_all_devices, get_device_stats
from helper import bytes_to_string, sanitize_string



#-------------------------------------------------------------------------------
# MQTT
#-------------------------------------------------------------------------------

mqtt_connected_to_broker = False
mqtt_sensors = []

#-------------------------------------------------------------------------------
class sensor_config:
    def __init__(self, deviceId, deviceName, sensorType, sensorName, icon):
        self.deviceId = deviceId
        self.deviceName = deviceName
        self.sensorType = sensorType
        self.sensorName = sensorName
        self.icon = icon 
        self.hash = str(hash(str(deviceId) + str(deviceName)+ str(sensorType)+ str(sensorName)+ str(icon)))

#-------------------------------------------------------------------------------

def publish_mqtt(client, topic, message):
    status = 1
    while status != 0:
        result = client.publish(
                topic=topic,
                payload=message,
                qos=MQTT_QOS,
                retain=True,
            )

        status = result[0]

        if status != 0:            
            mylog('info', ["Waiting to reconnect to MQTT broker"])
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
def create_sensor(client, deviceId, deviceName, sensorType, sensorName, icon):    

    new_sensor_config = sensor_config(deviceId, deviceName, sensorType, sensorName, icon)

    # check if config already in list and if not, add it, otherwise skip
    global mqtt_sensors, uniqueSensorCount

    is_unique = True

    for sensor in mqtt_sensors:
        if sensor.hash == new_sensor_config.hash:
            is_unique = False
            break
           
    # save if unique
    if is_unique:             
        publish_sensor(client, new_sensor_config)        




#-------------------------------------------------------------------------------
def publish_sensor(client, sensorConf): 

    global mqtt_sensors             

    message = '{ \
                "name":"'+ sensorConf.deviceName +' '+sensorConf.sensorName+'", \
                "state_topic":"system-sensors/'+sensorConf.sensorType+'/'+sensorConf.deviceId+'/state", \
                "value_template":"{{value_json.'+sensorConf.sensorName+'}}", \
                "unique_id":"'+sensorConf.deviceId+'_sensor_'+sensorConf.sensorName+'", \
                "device": \
                    { \
                        "identifiers": ["'+sensorConf.deviceId+'_sensor"], \
                        "manufacturer": "PiAlert", \
                        "name":"'+sensorConf.deviceName+'" \
                    }, \
                "icon":"mdi:'+sensorConf.icon+'" \
                }'

    topic='homeassistant/'+sensorConf.sensorType+'/'+sensorConf.deviceId+'/'+sensorConf.sensorName+'/config'

    # add the sensor to the global list to keep track of succesfully added sensors
    if publish_mqtt(client, topic, message):        
                                     # hack - delay adding to the queue in case the process is 
        time.sleep(MQTT_DELAY_SEC)   # restarted and previous publish processes aborted 
                                     # (it takes ~2s to update a sensor config on the broker)
        mqtt_sensors.append(sensorConf)

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
            mylog('verbose', ["        Connected to broker"])            
            mqtt_connected_to_broker = True     # Signal connection 
        else: 
            mylog('none', ["        Connection failed"])
            mqtt_connected_to_broker = False


    client = mqtt_client.Client('PiAlert')   # Set Connecting Client ID    
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)    
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_start() 

    return client

#-------------------------------------------------------------------------------
def mqtt_start():    

    global client, mqtt_connected_to_broker

    if mqtt_connected_to_broker == False:
        mqtt_connected_to_broker = True           
        client = mqtt_create_client() 
    
    # General stats    

    # Create a generic device for overal stats
    create_generic_device(client)

    # Get the data
    row = get_device_stats()   

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
    devices = get_all_devices()

    sec_delay = len(devices) * int(MQTT_DELAY_SEC)*5

    mylog('info', ["        Estimated delay: ", (sec_delay), 's ', '(', round(sec_delay/60,1) , 'min)' ])

    for device in devices:        

        # Create devices in Home Assistant - send config messages
        deviceId = 'mac_' + device["dev_MAC"].replace(" ", "").replace(":", "_").lower()
        deviceNameDisplay = re.sub('[^a-zA-Z0-9-_\s]', '', device["dev_Name"]) 

        create_sensor(client, deviceId, deviceNameDisplay, 'sensor', 'last_ip', 'ip-network')
        create_sensor(client, deviceId, deviceNameDisplay, 'binary_sensor', 'is_present', 'wifi')
        create_sensor(client, deviceId, deviceNameDisplay, 'sensor', 'mac_address', 'folder-key-network')
        create_sensor(client, deviceId, deviceNameDisplay, 'sensor', 'is_new', 'bell-alert-outline')
        create_sensor(client, deviceId, deviceNameDisplay, 'sensor', 'vendor', 'cog')
    
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