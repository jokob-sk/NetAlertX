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

![Report][report]


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
  | ------------------- | ------------------- |
  | ![Screen 3][screen3] | ![Screen 4][screen4] |


# Installation
<!--- --------------------------------------------------------------------- --->
Initially designed to run on a Raspberry PI, probably it can run on many other
Linux distributions.

## Dependencies
  | Dependency               | Comments                                                 |
  | ------------------------ | -------------------------------------------------------- |
  | Lighttpd                 | Probably works on other webservers / not tested          |
  | arp-scan                 | Required for Scan Method 1                               |
  | Pi.hole                  | Optional. Scan Method 2. Check devices doing DNS queries |
  | dnsmasq                  | Optional. Scan Method 3. Check devices using DHCP server |
  | IEEE HW Vendors Database | Necessary to identified Device vendor                    |

## Installation process
```
Pending explain the installation process
- step 1
- step 2
```


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


<!--- --------------------------------------------------------------------- --->
[main]:    ./doc/img/1_devices.jpg           "Main screen"
[screen1]: ./doc/img/2_1_device_details.jpg  "Screen 1"
[screen2]: ./doc/img/2_2_device_sessions.jpg "Screen 2"
[screen3]: ./doc/img/2_3_device_presence.jpg "Screen 3"
[screen4]: ./doc/img/3_presence.jpg          "Screen 4"
[report]:  ./doc/img/4_report.jpg            "Report sample"
