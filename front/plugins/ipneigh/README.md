## Overview

This plugin reads from the ARP and NDP tables using the `ip neigh` command.

This differs from the `ARPSCAN` plugin because
* It does *not* send arp requests, it just reads the table
* It supports IPv6
* It sends an IPv6 multicast ping to solicit IPv6 neighbour discovery

### Quick setup guide

To set up the plugin correctly, make sure to add in the plugin settings the name of the interfaces you want to scan. This plugin doesn't use the global `SCAN_SUBNET` setting, this is because by design it is not aware of subnets, it just looks at all the IPs reachable from an interface.

### Usage

- Head to **Settings** > **IP Neigh** to adjust the settings 
- Interfaces are extracted from the `SCAN_SUBNETS` setting (make sure you add interfaces in the prescribed format, e.g. `192.168.1.0/24 --interface=eth1`) 

### Notes

- `ARPSCAN` does a better job at discovering IPv4 devices because it explicitly sends arp requests
- IPv6 devices will often have multiple addresses, but the ping answer will contain only one. This means that in general this plugin will not discover every address but only those who answer

### Other info

- Author : [KayJay7](https://github.com/KayJay7)
- Date : 31-Nov-2024 - version 1.0
