# Wake-on-LAN Plugin User Guide

## Overview
The Wake-on-LAN (WOL) plugin allows you to remotely wake devices on your network that support Wake-on-LAN functionality. This plugin sends a "magic packet" to the specified devices, which powers them on, provided they are configured to accept WOL requests.

## Configuration
All settings for the plugin can be configured via the user interface. The key settings include:

- **Broadcast IPs (`WOL_broadcast_ips`)**: 
  A list of IP addresses to use for broadcasting the WOL packet. Ensure these are valid network broadcast addresses for your environment.
  
- **Devices to Wake (`WOL_devices_to_wake`)**: 
  Defines the group of devices to be woken. You can choose from:
  - `offline`: Wake devices that are currently offline.
  - `down`: Wake devices that are in a "down" state.

- **Ports (`WOL_ports`)**: 
  A list of ports to use when sending the WOL packet. The default is usually port 9.

## Usage
1. Configure the settings through the UI.
2. The plugin will automatically detect devices based on the selected criteria (offline or down) and attempt to wake them by sending WOL magic packets.
3. The plugin logs the outcome of each attempt and processes results for monitoring and notifications.

## Logs
Logs for each run of the plugin are stored in the specified log path, where you can track:
- WOL packet sending attempts.
- Success or failure of waking devices.

## Notes
- Ensure the devices are configured to allow Wake-on-LAN in BIOS and the network adapter supports WOL when powered off.
- Make sure your network is configured to allow broadcast packets.

### Usage

- Head to **Settings** > **Plugin name** to adjust the default values.

