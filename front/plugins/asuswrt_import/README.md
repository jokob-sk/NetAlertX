## Overview

Plugin that imports device IP, MAC, Name, Vendor and Online status from AsusWRT and AsusWRT-Merlin based routers.

This Plugin is using awesome [asusrouter](https://github.com/Vaskivskyi/asusrouter) library. Please check if your router is supported by it [here](https://github.com/Vaskivskyi/asusrouter?tab=readme-ov-file#supported-devices).

### Usage

- Enable the `ASUSWRT` plugin
- Head to **Settings** > **AsusWRT device import** to adjust the default values.
- If you have troubles configuring the plugin set the `LOG_LEVEL='debug'` to get a more detailed error message.

### Notes

- In case an existing imported device is renamed in Asus Router it will not be renamed in NetAlertX. In this case it has to be done manually or the device should be removed and it will appear on the next scan. 
- Only clients listed in the main AsusWRT interface are imported. If using plugins, such as the `YazFi plugin`, check the [Asus routers DHCPLSS guide](/front/plugins/dhcp_leases/ASUS_ROUTERS.md) for a possible workaround.

## Other info

- Version: 1.0.0
- Author: [labmonkey](https://github.com/labmonkey)
- Release Date: 16.1.2025 

