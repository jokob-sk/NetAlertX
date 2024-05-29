## Overview

Most on-network scanners (ARP-SCAN, NMAP, NSLOOKUP, DIG, PHOLUS) rely on scanning specific network interfaces and subnets. Check the [subnets documentation](https://github.com/jokob-sk/NetAlertX/blob/main/docs/SUBNETS.md) for help on this setting, especially VLANs, what VLANs are supported, or how to figure out the network mask and your interface. 

An alternative to on-network scanners is to enable some other Device scanners/importers that don't rely on NetAlert<sup>X</sup> having access to the network (UNIFI, dhcp.leases, PiHole, etc.).

> Note: The scan time itself depends on the number of IP addresses to check so set this up carefully with the appropriate network mask and interface.

> [!NOTE]
> If you have a lot of offline devices, which should be online, look into using, or substituing, ARP scan with other scans, such as `NMAPDEV`. The [ARP scan protocol uses](https://networkencyclopedia.com/arp-command/) a cache so results may not be 100% reliable. You can find all available network scanning options (marked as `🔍 dev scanner`) in the [Plugins overview](https://github.com/jokob-sk/NetAlertX/blob/main/front/plugins/README.md) readme.   

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

