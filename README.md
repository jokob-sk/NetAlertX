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

### Back
In charge of:
  - Scan the network searching connected devices using the scanning methods
    described
  - Store the information in the DB
  - Report the changes detected by e-mail

  | ![Report 1][report1] | ![Report 2][report2] |
  | -------------------- | -------------------- |

### Front
A web frontal that allows:
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
Initially designed to run on a Raspberry Pi, probably it can run on many other
Linux distributions.

- One-step Automated Install:
  #### `curl -sSL https://github.com/pucherot/Pi.Alert/raw/main/install/pialert_install.sh | bash`

- [Installation Guide (step by step)](docs/INSTALL.md)


# Update
<!--- --------------------------------------------------------------------- --->
- One-step Automated Update:
  #### `curl -sSL https://github.com/pucherot/Pi.Alert/raw/main/install/pialert_update.sh | bash`

# Uninstall process
<!--- --------------------------------------------------------------------- --->
  - [Unistall process](docs/UNINSTALL.md)


# Device Management
<!--- --------------------------------------------------------------------- --->
  - [Device Management instructions](docs/DEVICE_MANAGEMENT.md)


## Other useful info
<!--- --------------------------------------------------------------------- --->

### [Versions History](docs/VERSIONS_HISTORY.md)

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
  [Read more here](LICENSE.txt)

### Contact
  pi.alert.application@gmail.com
  
  ***Suggestions and comments are welcome***


<!--- --------------------------------------------------------------------- --->
[main]:    ./docs/img/1_devices.jpg           "Main screen"
[screen1]: ./docs/img/2_1_device_details.jpg  "Screen 1"
[screen2]: ./docs/img/2_2_device_sessions.jpg "Screen 2"
[screen3]: ./docs/img/2_3_device_presence.jpg "Screen 3"
[screen4]: ./docs/img/3_presence.jpg          "Screen 4"
[report1]: ./docs/img/4_report_1.jpg          "Report sample 1"
[report2]: ./docs/img/4_report_2.jpg          "Report sample 2"

