## Overview

Arp-scan is a command-line tool that uses the ARP protocol to discover and fingerprint IP hosts on the local network. An alternative to ARP scan is to enable the `PIHOLE_RUN` PiHole integration settings. The arp-scan (and other Network-scan plugin times using the `SCAN_SUBNETS` setting) time depends on the number of IP addresses to check so set this up carefully with the appropriate network mask and interface. Check the [subnets documentation](https://github.com/jokob-sk/Pi.Alert/blob/main/docs/SUBNETS.md) for help on setting up VLANs, what VLANs are supported, or how to figure out the network mask and your interface. 

### Usage

- Go to settings and set the `SCAN_SUBNETS` setting as per [subnets documentation](https://github.com/jokob-sk/Pi.Alert/blob/main/docs/SUBNETS.md).
- Enable the plugin by changing the RUN parameter from disabled to your preferred run time (usually: `schedule`).
  - Specify the schedule in the `ARPSCAN_RUN_SCHD` setting
- Adjust the timeout if needed in the `ARPSCAN_RUN_TIMEOUT` setting
- Review remaining settings
- SAVE
- Wait for the next scan to finish

