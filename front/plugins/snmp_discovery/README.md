## Overview

A plugin for importing devices from an SNMP enabled router or switch.  

### Usage

Specify the following settings in the Settings section of PiAlert:

- `SNMPDSC_routers` - A list of IP addresses of roputers/switches with SNMP turned on.

### Notes

- Executing the `snmpwalk -v 2c -c public -OXsq <IP> .1.3.6.1.2.1.3.1.1.2` command.
- Only IPv4 supported.
- Expected output in format `iso.3.6.1.2.1.3.1.1.2.3.1.192.168.1.2 "6C 6C 6C 6C 6C 6C "`.