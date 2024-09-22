## Overview

The synchronization plugin is designed to synchronize data across multiple instances of the app. It supports the following data synchronization modes:

1. **💻 Devices**: Sends an encrypted `table_devices.json` file to synchronize the entire Devices database table.
2. **🔌 Plugin Data**: Sends encrypted `last_result.log` files for individual plugins.

> **Note:** `[n]` indicates a setting specified for the node instance, and `[n,h]` indicates a setting used on both the node and the hub instances.

### Synchronization Modes

The plugin operates in three different modes based on the configuration settings:

1. **Mode 1: PUSH (NODE)** - Sends data from the node to the hub.
   - This mode is activated if `SYNC_hub_url` is set and either `SYNC_devices` or `SYNC_plugins` is enabled.
   - **Actions**:
     - Sends `table_devices.json` to the hub if `SYNC_devices` is enabled.
     - Sends individual plugin `last_result.log` files to the hub if `SYNC_plugins` is enabled.

2. **Mode 2: PULL (HUB)** - Retrieves data from nodes to the hub.
   - This mode is activated if `SYNC_nodes` is set.
   - **Actions**:
     - Retrieves data from configured nodes using the API and saves it locally for further processing.

3. **Mode 3: RECEIVE (HUB)** - Processes received data on the hub.
   - Activated when data is received in Mode 2 and is ready to be processed.
   - **Actions**:
     - Decodes received data files, processes them, and updates the Devices table accordingly.

### Settings

#### Node (Source) Settings `[n]`

- **When to Run** `[n,h]`: `SYNC_RUN`
- **Schedule** `[n,h]`: `SYNC_RUN_SCHD`
- **API Token** `[n,h]`: `SYNC_api_token`
- **Encryption Key** `[n,h]`: `SYNC_encryption_key`
- **Node Name** `[n]`: `SYNC_node_name`
- **Hub URL** `[n]`: `SYNC_hub_url`
- **Sync Devices** `[n]`: `SYNC_devices`
- **Sync Plugins** `[n]`: `SYNC_plugins`

#### Hub (Target) Settings `[h]`

- **When to Run** `[n,h]`: `SYNC_RUN`
- **Schedule** `[n,h]`: `SYNC_RUN_SCHD`
- **API Token** `[n,h]`: `SYNC_api_token`
- **Encryption Key** `[n,h]`: `SYNC_encryption_key`
- **Nodes to Pull From** `[h]`: `SYNC_nodes`

### Usage

1. **Adjust Settings**:
   - Navigate to **Settings** > **Sync Hub** to modify default settings.
2. **Data Flow**:
   - Nodes send or receive data based on the specified modes, either pushing data to the hub or pulling from nodes.

### Notes

- Existing devices on the hub will not be updated by the data received from this SYNC plugin if their MAC addresses are already present.
- It is recommended to use Device synchronization primarily. Plugin data synchronization is more suitable for specific use cases.

![Sync Hub Setup Diagram](/front/plugins/sync/sync_hub.png)
