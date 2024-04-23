## Overview

Most on-network scanners (ARP-SCAN, NMAP, NSLOOKUP, DIG, PHOLUS) rely on scanning specific network interfaces and subnets. Check the <a href="https://github.com/jokob-sk/NetAlertX/blob/main/docs/SUBNETS.md" target="_blank">subnets documentation</a> for help on this setting, especially VLANs, what VLANs are supported, or how to figure out the network mask and your interface. <br/> <br/> An alternative to on-network scanners is to enable some other Device scanners/importers that don't rely on NetALert<sup>X</sup> having access to the network (UNIFI, dhcp.leases, PiHole, etc.). <br/> <br/> Note: The scan time itself depends on the number of IP addresses to check so set this up carefully with the appropriate network mask and interface.

### Usage

- Go to settings and set the `SCAN_SUBNETS` setting as per [subnets documentation](https://github.com/jokob-sk/NetAlertX/blob/main/docs/SUBNETS.md).
- Enable the plugin by changing the RUN parameter from disabled to your preferred run time (usually: `schedule`).
  - Specify the schedule in the `ARPSCAN_RUN_SCHD` setting
- Adjust the timeout if needed in the `ARPSCAN_RUN_TIMEOUT` setting
- Review remaining settings
- SAVE
- Wait for the next scan to finish

#### Examples

Settings:

![settings](/front/plugins/arp_scan/arp-scan-settings.png)

