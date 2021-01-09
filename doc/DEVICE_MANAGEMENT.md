# Pi.Alert - Device Management
<!--- --------------------------------------------------------------------- --->
To edit device information:
  - Select "Devices" in the menu on the left of the screen
  - Find the device you want to edit in the central table
  - Go to the device page by clicking on the device name or status
  - Press "Details" tab of the device
  - Edit the device data
  - Press the "Save" button


![Device Details][screen1]


## Main Info
  - **MAC**: MAC addres of the device. Not editable.
  - **Name**: Friendly device name
  - **Owner**: Device owner (The list is self-populated with existing owners)
  - **Type**: Select a device type from the dropdown list (Smartphone, Table,
      Laptop, TV, router, ....) or type a new device type
  - **Vendor**: Automatically updated by Pi.Alert
  - **Favorite**: Mark the device as favorite and then it will appears at the
      begining of the device list
  - **Group**: Select a grouper ('Always on', 'Personal', Friends') or type
      your own Group name
  - **Comments**: Type any comments for the device

## Session Info
  - **Status**: Show device status : On-line / Off-Line
  - **First Session**: Date and time of the first connection
  - **Last Session**: Date and time of the last connection
  - **Last IP**: Last known IP used during the last connection
  - **Static IP**: Check this box to identify devices that always use the
      same IP

## Events & Alerts config
  - **Scan Cycle**: Select the scan cycle: 0, 1', 15'
    - Some devices do not respond to all ARP packets, for this cases is better
      to use a 15' cycle.
    - **For Apple devices I recommend using 15' cycle**
  - **Alert All Events**: Send a notification in each event (connection,
      disconnection, IP Changed, ...)
  - **Alert Down**: Send a notification when the device is down
    - *(Userful with "always connected" devices: Router, AP, Camera, Alexa,
      ...)*
  - **Skip repeated notifications during**: Do not send more than one
      notification to this device for X hours
    - *(Useful to avoid notification saturation on devices that frequently
      connects and disconnects)*

### License
  GPL 3.0
  [Read more here](LICENSE.txt)

### Contact
  pi.alert.application@gmail.com
  
  ***Suggestions and comments are welcome***


<!--- --------------------------------------------------------------------- --->
[main]:    ./img/1_devices.jpg           "Main screen"
[screen1]: ./img/2_1_device_details.jpg  "Screen 1"

