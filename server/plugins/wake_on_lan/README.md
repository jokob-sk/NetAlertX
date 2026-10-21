## Overview

Automatically wakes devices on your network by sending them a Wake-on-LAN "magic packet" - useful for bringing machines back online on a schedule without touching them manually. On each run, the plugin picks devices matching your selected status (e.g. `offline` or `down`) and broadcasts a magic packet to each.

### Usage

- Head to **Settings** > **Wake on Lan (WOL)** to adjust the default values.

### Notes

- The target device must have Wake-on-LAN enabled in its BIOS/UEFI and network adapter settings - the plugin can only send the packet, it can't enable WOL support on a device that doesn't have it turned on.
- Your network must allow broadcast packets between the NetAlertX container and the target devices (same broadcast domain, or a broadcast IP configured for the right subnet).
