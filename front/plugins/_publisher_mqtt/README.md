## Overview

- Feed your data and device changes into [Home Assistant](https://github.com/jokob-sk/NetAlertX/blob/main/docs/HOME_ASSISTANT.md) via the MQTT Mosquito broker. (other brokers might work as well)

### Usage

- Go to settings and fill in relevant details.


### Notes

The first run will take a while, subsequent should be much faster because new sensors don't have to be created anymore. If the first sync times out, try to increase the timeout setting (default: 10s per device). A bit of background:

1. The app keeps a hash of the sensors. The hash includes:
    - deviceId: Unique identifier for the device associated with the sensor.
    - deviceName: Name of the device.
    - sensorType: Type of sensor.
    - sensorName: Name of the sensor.
    - icon: Icon associated with the sensor.
2. This hash is compared to existing MQTT plugin object hashes, which can be found under Integrations > Plugins > MQTT (Plugin objects tab) > Hash
3. If the hash is not found, a new device/device state is assumed and the device is sent to the broker


The state is managed differently, the state of the sensor is not included in the hash. This might be improved upon in later releases. 


