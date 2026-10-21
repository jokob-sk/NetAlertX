## Overview

Detects DHCP servers answering on your network, using NMAP's `broadcast-dhcp-discover` probe - it broadcasts a DHCP discover request and lists every server that responds, the same way a rogue-DHCP detector would. NetAlertX doesn't know which responses are "expected" (your router) versus "rogue" (a misconfigured device, a second router, or something malicious) - that judgment call is yours; the plugin just gives you the full list so you can spot an unexpected one.

### Usage

- Check the Settings page for details.

### Notes

- Requires the container to send/receive broadcast traffic on the scanned network (host networking or an equivalent setup) - a bridged/isolated network namespace will prevent the probe from seeing real responses.

### Other info

- Based on the work of [leiweibau](https://github.com/leiweibau/Pi.Alert)
