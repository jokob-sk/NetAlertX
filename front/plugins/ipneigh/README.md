## Overview

This plugin reads from the ARP and NDP tables using the `ip neigh` command.

This differs from the `ARPSCAN` plugin because
* It does *not* send arp requests, it just reads the table
* It supports IPv6
* It sends an IPv6 multicast ping to solicit IPv6 neighbour discovery

### Quick setup guide

To set up the plugin correctly, make sure to add in the plugin settings the name of the interfaces you want to scan. This plugin doesn't use the global `SCAN_SUBNET` setting, this is because by design it is not aware of subnets, it just looks at all the IPs reachable from an interface.

### Usage

- Head to **Settings** > **IP Neigh** to add the interfaces you want to scan to the `IPNEIGH_interfaces` option
- The interface list must be formatted without whitespaces and comma separated

### Notes

- `ARPSCAN` does a better job at discovering IPv4 devices because it explicitly sends arp requests
- IPv6 devices can