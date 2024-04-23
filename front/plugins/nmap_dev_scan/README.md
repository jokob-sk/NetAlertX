## Overview

NMAP-scan is a command-line tool to discover and fingerprint IP hosts on the local network. The NMAP-scan (and other Network-scan plugin times using the `SCAN_SUBNETS` setting) time depends on the number of IP addresses to check so set this up carefully with the appropriate network mask and interface. Check the [subnets documentation](https://github.com/jokob-sk/NetAlertX/blob/main/docs/SUBNETS.md) for help on setting up VLANs, what VLANs are supported, or how to figure out the network mask and your interface. 

### Usage

- Go to settings and set the `SCAN_SUBNETS` setting as per [subnets documentation](https://github.com/jokob-sk/NetAlertX/blob/main/docs/SUBNETS.md).
- Enable the plugin by changing the RUN parameter from disabled to your preferred run time (usually: `schedule`).
  - Specify the schedule in the `NMAPDEV_RUN_SCHD` setting
- Adjust the timeout if needed in the `NMAPDEV_RUN_TIMEOUT` setting
- Review remaining settings
- SAVE
- Wait for the next scan to finish

