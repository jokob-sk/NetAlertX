# Pi.Alert
<!--- --------------------------------------------------------------------- --->

WIFI / LAN intruder detector.

Scan the devices connected to your WIFI / LAN and alert you the connection of
unknown devices. It also warns of the disconnection of "always connected"
devices.

*(Apologies for my english and my limited knowledge of Python, php and
JavaScript)*

## How it works

The system continuously scan the network for:
  - New devices
  - New connections (re-connections)
  - Disconnections
  - IP changes
  - "Always Connected" devices down
  - Changes in Internet IP address

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
        examines the DHCP leases (addresses asigned) to find active devices
        that were not discovered by the previous methods.

## Components

The system consists of two parts:

- **Back**, in charge of:
  - scanning the network searching connected devices using the scanning methods
        described
  - store the information in the DB
  - report the changes detected by e-mail

- **Front**, a web frontal that allows:
  - display in a visual way all the information collected by the back
  - Manage de devices inventory and the characteristics

<Image>


# Installation
<!--- --------------------------------------------------------------------- --->
Initially designed to run on a Raspberry PI, it can run on many other Linux
distributions.

## Dependencies
  - Lighttpd (probably works on other webservers / not tested)
  - arp-scan (required for Scan Method 1)
  - Pi.hole (optional. Scan Method 2. Check devices doing DNS queries)
  - dnsmasq (optional. Scan Method 3. Check devices using DHCP server)
  - IEEE HW Vendors Database (necessary to identified Device vendor)

## Installation process
```
Pending explain the installation process
- step 1
- step 2
```


## Other useful info
<!--- --------------------------------------------------------------------- --->

### Powered by:
  - Python (Programming language for the Back)
  - PHP (Programming language for the Front-end)
  - JavaScript (Programming language for the Front-end)
  - Bootstrap (Front-end framework)
  - Admin.LTE (Bootstrap template)
  - FullCalendar (calendar component)
  - Sqlite (DB engine)
  - Lighttpd (Webserver)
  - arp-scan (Scan network using arp commands)
  - Pi.hole (DNS Server with Ad-block)
  - dnsmasq (DHCP Server)

### License
  GPL 3.0
  [Read more here](doc/LICENSE.txt)

### Contact
  pi.alert.application@gmail.com
