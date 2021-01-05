# Pi.Alert
WIFI / LAN intruder detector.

Check the devices connected to your WIFI / LAN and alert you the unknown devices. It also warns of the disconnection of "always connected" devices.

*(Apologies for my english and my limited knowledge of Python, php and JavaScript)*

### How it works


### Componets
The system consists of two parts:

- **Back**: in charge of scanning the network searching connected devices, store the information in the DB, and reporting the changes detected by e-mail.

- **Front**: a web frontal that allows to display, in a visual way, all the information collected by the back.
<Image>


# Installation
Initially designed to run on a Raspberry PI, it can run on many other Linux distributions.

```
Pending explain the installation process
- step 1
- step 2
```

### Dependencies
- Lighttpd (probably works on other webservers / not tested)
- arp-scan (Required for Scan Method 1) 
- Pi.hole (optional. Scan Method 2. Check devices doing DNS queries)
- dnsmasq (optional. Scan Method 3. Check devices using DHCP server)
- IEEE HW Vendors Database (Necessary to identified HW vendor)

# Powered by:
- Python (Programming language for the Back)
- PHP (Programming language for the Front-end)
- JavaScript (Programming language for the Front-end)
- Bootstrap (Front-end framework)
- Admin.LTE (Bootstrap template)
- FullCalendar (calendar component)
- Sqlite (DB engine)
- Lighttpd (Webserver)
- arp-scan (Scan network using arp commands)
- Pi.hole (DNS Server)
- dnsmasq (DHCP Server)

# License
GPL 3.0

# Contact
_pending..._
