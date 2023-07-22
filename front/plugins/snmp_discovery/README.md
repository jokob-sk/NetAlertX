## Overview

A plugin for importing devices from an SNMP enabled router or switch.  Using SNMP offers an efficient way to discover IPv4 devices across one or more networks/subnets/vlans.

### Usage

Specify the following settings in the Settings section of PiAlert:

- `SNMPDSC_routers` - A list of `snmpwalk` commands to execute against IP addresses of roputers/switches with SNMP turned on. For example: 

  - `snmpwalk -v 2c -c public -OXsq 192.168.1.1 .1.3.6.1.2.1.3.1.1.2`
  - `snmpwalk -v 2c -c public -Oxsq 192.168.1.1 .1.3.6.1.2.1.3.1.1.2` (note: lower case `x`)


### Setup Cisco IOS

Enable IOS SNMP service and restrict to selected (internal) IP/Subnet.

````
! Add standard ip access-list 10
ip access-list standard 10
 permit 192.168.1.0 0.0.0.255
 permit host 192.168.2.10
!
! Enable IOS snmp server with Read Only community 'mysnmpcommunitysecret' name.
! Restrict connections to access-list 10
snmp-server community mysnmpcommunitysecret RO 10
````

Confirm SNMP enabled
````
show snmp
````

### Notes

- Only IPv4 supported.
- The SNMP OID `.1.1.1.3.6.1.2.1.3.1.1.2` is specifically for devices IPv4 ARP table. This OID has been tested on Cisco ISRs and other L3 devices. Support may vary between other vendors / devices.
- Expected output (ingestion) in format `iso.3.6.1.2.1.3.1.1.2.3.1.192.168.1.2 "6C 6C 6C 6C 6C 6C "`.
