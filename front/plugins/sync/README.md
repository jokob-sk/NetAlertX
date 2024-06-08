## Overview

Synchronization plugin to synchronize multiple app instances. The Plugin can sychronize 2 types of data:

1. 💻 Devices: The plugin sends an encrypted `table_devices.json` file to synchronize the whole Devices DB table.
1. 🔌 Plugin data:  The plugin sends encrypted `last_result.log` files for individual plugins. 

> [!TIP]
> `[n]` indicates a setting taht is usually specified for the node instance. `[n,h]` indicates a setting used both, on the node and on the hub instance.

### Synchronizing 💻 Devices data or 🔌 Plugins data

Most of the setups will probably only use 💻 Devices synchronization. 🔌 Plugins data will be probably used in only special use cases. 

#### [n] Node (Source) Settings

- When to run [n,h] `SYNC_RUN`
- Schedule [n,h] `SYNC_RUN_SCHD`
- API token [n,h] `SYNC_api_token`
- Encryption Key [n,h] `SYNC_encryption_key` 
- Node name [n] `SYNC_node_name`
- Hub URL [n] `SYNC_hub_url`
- Sync Devices [n] `SYNC_devices` or Sync Plugins [n] `SYNC_plugins` (or both)

#### [h] Hub (Target) Settings

- When to run [n,h] `SYNC_RUN`
- Schedule [n,h] `SYNC_RUN_SCHD`
- API token [n,h] `SYNC_api_token`
- Encryption Key [n,h] `SYNC_encryption_key`


### Usage

- Head to **Settings** > **Sync Hub** to adjust the default values.

### Notes

- If a MAC address already exists on the hub, the device will be skipped in the data coming from this SYNC plugin. 