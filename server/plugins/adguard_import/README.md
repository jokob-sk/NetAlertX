## Overview

Imports devices *from* AdGuard Home *into* NetAlertX. On each run it pulls AdGuard Home's auto-discovered clients (devices AdGuard has seen via DNS activity, not the manually-configured persistent client list) and cross-references its DHCP leases to resolve a MAC address for each one.

This is the reverse direction of the [`adguard_export`](https://docs.netalertx.com/plugins/adguard_export) plugin, which pushes NetAlertX's known devices *to* AdGuard Home as persistent clients.

### Usage

- Enable the `ADGUARDIMP` plugin and point it at your AdGuard Home instance's address and credentials.
- If a client has no MAC in AdGuard's DHCP leases (e.g. it was seen only via DNS, not DHCP), enable the fake-MAC option to still import it under a deterministic synthetic MAC rather than skipping it.

### Notes

- Requires AdGuard Home's REST API to be reachable from the NetAlertX container.
