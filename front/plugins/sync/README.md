## Overview

Synchronization plugin to synchronize multiple app instances. The Plugin can sychronize 2 types of data:

1. 💻 Devices: The plugin sends an encrypted `table_devices.json` file to synchronize the whole Devices DB table.
1. 🔌 Plugin data:  The plugin sends encrypted `last_result.log` files for individual plugins. 

### Synchronizing 💻 Devices data

This is probably what most of the setups will use. Required settings follow.

#### Node (Source) Settings

- When to run `SYNC_RUN`
- Schedule `SYNC_RUN_SCHD`
- API token `SYNC_api_token`
- Encryption Key `SYNC_encryption_key`
- Node name `SYNC_node_name`
- Hub URL `SYNC_hub_url`
- Send Devices `SYNC_devices` 👈

#### Hub (Target) Settings

- When to run `SYNC_RUN`
- Schedule `SYNC_RUN_SCHD`
- API token `SYNC_api_token`
- Encryption Key `SYNC_encryption_key`

### Synchronizing 🔌 Plugins data

This mechanism will be probably used in special use cases. Required settings follow.

#### Node (Source) Settings

- When to run `SYNC_RUN`
- Schedule `SYNC_RUN_SCHD`
- API token `SYNC_api_token`
- Encryption Key `SYNC_encryption_key`
- Node name `SYNC_node_name`
- Hub URL `SYNC_hub_url`
- Send Plugins `SYNC_plugins` 👈

#### Hub (Target) Settings

- When to run `SYNC_RUN`
- Schedule `SYNC_RUN_SCHD`
- API token `SYNC_api_token`
- Encryption Key `SYNC_encryption_key`


### Usage

- Head to **Settings** > **Sync Hub** to adjust the default values.

### Notes

- TBC