## Overview

A plugin to resolve `(unknown)` device names. It uses the [Pholus](https://github.com/jokob-sk/Pi.Alert/tree/main/front/plugins/pholus_scan/pholus) sniffing tool. 

### Usage

- Go to settings and find Pholus-Scan (Name discovery) in the list of settings.
- Enable the plugin by changing the `RUN` parameter from disabled to one you prefer (`schedule`,  `always_after_scan`, `on_new_device`).
- Specify the `PHOLUS_RUN_TIMEOUT` (Will be divided by the number of subnets specified in the Arp-Scan (Network scan) plugin setting `SCAN_SUBNETS`)
- SAVE
- Wait for the next scan to finish


