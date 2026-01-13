## Overview

**NMAP-scan** is a command-line tool used to discover and fingerprint IP hosts on your network.
The NMAP-scan (and other Network-scan plugins using the `SCAN_SUBNETS` setting) runtime depends on the number of IP addresses to check — so configure it carefully with the appropriate **network mask** and **interface**.

Refer to the [subnets documentation](https://docs.netalertx.com/SUBNETS) for help with setting up VLANs, understanding which VLANs are supported, and determining your network mask and interface.

> [!NOTE]
> The `NMAPDEV` plugin is excellent for detecting device availability, but **ARP-scan** is better for scanning across multiple VLANs and subnets.
> NMAP cannot retrieve MAC addresses from other subnets (an NMAP limitation), which are often required to identify devices.
> You can safely combine different scan methods.
> See all available network scanning options (marked with `🔍 dev scanner`) in the [Plugins overview](https://docs.netalertx.com/PLUGINS).

This plugin is **not optimized for name resolution** (use `NSLOOKUP` or `AVAHISCAN` instead), but if a name is available it will appear in the **Resolved Name** column.

---

### Usage

1. In **Settings**, configure the `SCAN_SUBNETS` value as described in the [subnets documentation](https://docs.netalertx.com/SUBNETS).
   The plugin automatically **strips unsupported `--vlan` parameters** and replaces `--interface` with `-e`.
2. Enable the plugin by setting the `RUN` parameter from `disabled` to your preferred run mode (usually `schedule`).
3. Specify the schedule using the `NMAPDEV_RUN_SCHD` setting.
4. Adjust the scan timeout if necessary with the `NMAPDEV_RUN_TIMEOUT` setting.
5. If scanning **remote networks**, consider enabling the `NMAPDEV_FAKE_MAC` setting — review its description carefully before use.
6. Review all remaining settings.
7. Click **SAVE**.
8. Wait for the next scheduled scan to complete.
