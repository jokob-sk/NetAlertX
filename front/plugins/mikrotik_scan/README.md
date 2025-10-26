## Overview

The plugin uses the MikroTik API to discover devices by retrieving DHCP lease information.

### Prerequisites

- API must be enabled in `API > Interfaces` on your MikroTik router.
- A user must be created in `System > Users` on your MikroTik router. Read-only permissions are recommended for security.

### Usage

It is recommended to use this plugin in scheduled mode for continuous device discovery and monitoring.

In the Settings section of NetAlertX, provide the following parameters:

- **MTSCAN_MT_HOST**: IP address of the MikroTik router (default: `192.168.88.1`).
- **MTSCAN_MT_PORT**: Port for the MikroTik API (default: `8728`).
- **MTSCAN_MT_USER**: Username for the MikroTik router.
- **MTSCAN_MT_PASS**: Password for the MikroTik router.

### Device name resolution order

To assign a meaningful device name, the plugin resolves it in the following order:

- **Comment**: The `comment` field in the MikroTik router's DHCP lease configuration. This is useful for naming static leases of known devies.
- **Hostname**: The hostname provided by the device during DHCP negotiation.
- **"(unknown)"**: as the fallback name, allowing other plugins to resolve the device name later.


### Other info

- Version: 1.0
- Author: [lookflying](https://github.com/lookflying)
- Maintainer(s): [elraro](https://github.com/elraro), [kamil-olszewski-devskiller](https://github.com/kamil-olszewski-devskiller)
- Release Date: 12-Sep-2024
