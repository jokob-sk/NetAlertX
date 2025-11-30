## Overview

A plugin for importing devices from an SNMP-enabled router or switch. Using SNMP offers an efficient way to discover IPv4 devices across one or more networks/subnets/vlans.

### Usage

Specify the following settings in the Settings section of NetAlertX:

- `SNMPDSC_routers` - A list of `snmpwalk` commands to execute against IP addresses of routers/switches with SNMP turned on. For example:

  - `snmpwalk -v 2c -c public -OXsq 192.168.1.1 .1.3.6.1.2.1.3.1.1.2`
  - `snmpwalk -v 2c -c public -Oxsq 192.168.1.1 .1.3.6.1.2.1.3.1.1.2` (note: lower case `x`)


If unsure, please check [snmpwalk examples](https://www.comparitech.com/net-admin/snmpwalk-examples-windows-linux/).

Supported output formats:

```
ipNetToMediaPhysAddress[3][192.168.1.9] 6C:6C:6C:6C:6C:b6C1
IP-MIB::ipNetToMediaPhysAddress.17.10.10.3.202 = STRING: f8:81:1a:ef:ef:ef
mib-2.3.1.1.2.15.1.192.168.1.14 "2C F4 32 18 61 43 "
```

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

### Setup for (old) procurve switches

```
snmpwalk -v 2c -c XXXXXX -On -Ovq 192.168.45.58 .1.3.6.1.2.1.4.22.1.3.102
```

### Notes

- Only IPv4 supported.
- The SNMP OID `.1.1.1.3.6.1.2.1.3.1.1.2` is specifically for devices IPv4 ARP table. This OID has been tested on Cisco ISRs and other L3 devices. Support may vary between other vendors/devices.
- Expected output (ingestion) in formats:

  - `iso.3.6.1.2.1.3.1.1.2.3.1.192.168.1.2 "6C 6C 6C 6C 6C 6C "`.
  - `ipNetToMediaPhysAddress[3][192.168.1.9] 6C:6C:6C:6C:6C:b6C1`.


### Finding your OID

- Ssh into the router (in this example the IP of the router is `192.168.1.1`)
- On the router execute `snmptranslate -On -IR ipNetToMediaPhysAddress` (This is a UniFi router example, and the `object_id` is `ipNetToMediaPhysAddress`. This might vary between vendors, google your router manufacturer examples.)

```bash
jokob@SecurityGateway-USG:~$ snmptranslate -On -IR ipNetToMediaPhysAddress
.1.3.6.1.2.1.4.22.1.2
```

- Use the `snmpwalk -v 2c -OXsq -c public 192.168.1.1 .1.3.6.1.2.1.4.22.1.2` command in NetAlertX



