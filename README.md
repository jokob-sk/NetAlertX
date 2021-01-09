# Pi.Alert
<!--- --------------------------------------------------------------------- --->

WIFI / LAN intruder detector.

Scan the devices connected to your WIFI / LAN and alert you the connection of
unknown devices. It also warns the disconnection of "always connected" devices.

![Main screen][main]

*(Apologies for my English and my limited knowledge of Python, php and
JavaScript)*

## How it works
The system continuously scans the network for:
  - New devices
  - New connections (re-connections)
  - Disconnections
  - "Always Connected" devices down
  - Devices IP changes
  - Internet IP address changes

## Scan Methods
Up to three scanning methods are used:
  - **Method 1: arp-scan**. The arp-scan system utility is used to search
        for devices on the network using arp frames.
  - **Method 2: Pi-hole**. This method is optional and complementary to
        method 1. If the Pi-hole DNS server is active, Pi.Alert examines its
        activity looking for active devices using DNS that have not been
        detected by method 1.
  - **Method 3. dnsmasq**. This method is optional and complementary to the
        previous methods. If the DHCP server dnsmasq is active, Pi.Alert
        examines the DHCP leases (addresses assigned) to find active devices
        that were not discovered by the other methods.

## Components
The system consists of two parts:

- **Back**, in charge of:
  - Scan the network searching connected devices using the scanning methods
        described
  - Store the information in the DB
  - Report the changes detected by e-mail

  | ![Report 1][report1] | ![Report 2][report2] |
  | -------------------- | -------------------- |

- **Front**, a web frontal that allows:
  - Manage the devices inventory and the characteristics
  - Display in a visual way all the information collected by the back
    - Sessions
    - Connected devices
    - Favorites
    - Events
    - Presence
    - Concurrent devices
    - Down alerts
    - IP's
    - ...

  | ![Screen 1][screen1] | ![Screen 2][screen2] |
  | -------------------- | -------------------- |
  | ![Screen 3][screen3] | ![Screen 4][screen4] |


# Installation
<!--- --------------------------------------------------------------------- --->
Initially designed to run on a Raspberry PI, probably it can run on many other
Linux distributions.

  [Instructions](doc/INSTALL.md)


# Device Management
<!--- --------------------------------------------------------------------- --->
To edit device information:
  - Select "Devices" in the menu on the left of the screen
  - Find the device you want to edit in the central table
  - Go to the device page by clicking on the device name or status
  - Press "Details" tab of the device
  - Edit the device data
  - Press the "Save" button

### Main Info
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

### Session Info
  - **Status**: Show device status : On-line / Off-Line
  - **First Session**: Date and time of the first connection
  - **Last Session**: Date and time of the last connection
  - **Last IP**: Last known IP used during the last connection
  - **Static IP**: Check this box to identify devices that always use the
      same IP

### Events & Alerts config
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


## Other useful info
<!--- --------------------------------------------------------------------- --->

### Powered by:
  | Product      | Objetive                               |
  | ------------ | -------------------------------------- |
  | Python       | Programming language for the Back      |
  | PHP          | Programming language for the Front-end |
  | JavaScript   | Programming language for the Front-end |
  | Bootstrap    | Front-end framework                    |
  | Admin.LTE    | Bootstrap template                     |
  | FullCalendar | Calendar component                     |
  | Sqlite       | DB engine                              |
  | Lighttpd     | Webserver                              |
  | arp-scan     | Scan network using arp commands        |
  | Pi.hole      | DNS Server with Ad-block               |
  | dnsmasq      | DHCP Server                            |

### License
  GPL 3.0
  [Read more here](doc/LICENSE.txt)

### Contact
  pi.alert.application@gmail.com
  
  ***Suggestions and comments are welcome***


<!--- --------------------------------------------------------------------- --->
[main]:    ./doc/img/1_devices.jpg           "Main screen"
[screen1]: ./doc/img/2_1_device_details.jpg  "Screen 1"
[screen2]: ./doc/img/2_2_device_sessions.jpg "Screen 2"
[screen3]: ./doc/img/2_3_device_presence.jpg "Screen 3"
[screen4]: ./doc/img/3_presence.jpg          "Screen 4"
[report1]: ./doc/img/4_report_1.jpg          "Report sample 1"
[report2]: ./doc/img/4_report_2.jpg          "Report sample 2"

