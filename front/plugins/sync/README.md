## Overview

The synchronization plugin is designed to synchronize data across multiple instances of the app. It supports the following data synchronization modes:

1. **💻 Devices**: Sends an encrypted `table_devices.json` file to synchronize the entire Devices database table.
2. **🔌 Plugin Data**: Sends encrypted `last_result.log` files for individual plugins.


> [!TIP]
> This plugin is usually used if you need to monitor inaccessible networks (WAN, VLAN etc.). Read the [Remote networks documentation](/docs/REMOTE_NETWORKS.md) for more details about these scenarios.

### Synchronization Modes

The plugin operates in three different modes based on the configuration settings.

> **Note:** `[n]` indicates a setting specified for the node instance, and `[n,h]` indicates a setting used on both the node and the hub instances.

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

- **API Token** `[n,h]`: `API_TOKEN` (has to be same across all nodes)

- **When to Run** `[n,h]`: `SYNC_RUN`
- **Schedule** `[n,h]`: `SYNC_RUN_SCHD`
- **Encryption Key** `[n,h]`: `SYNC_encryption_key`
- **Node Name** `[n]`: `SYNC_node_name`
- **Hub URL** `[n]`: `SYNC_hub_url` + `GRAPHQL_PORT` of the target
- **Sync Devices** `[n]`: `SYNC_devices`
- **Sync Plugins** `[n]`: `SYNC_plugins`

#### Hub (Target) Settings `[h]`

- **API Token** `[n,h]`: `API_TOKEN` (has to be same across all nodes)

- **When to Run** `[n,h]`: `SYNC_RUN`
- **Schedule** `[n,h]`: `SYNC_RUN_SCHD`
- **Encryption Key** `[n,h]`: `SYNC_encryption_key`
- **Nodes to Pull From** `[h]`: `SYNC_nodes` + `GRAPHQL_PORT` of the source nodes

### Usage

1. **Adjust Settings**:
   - Navigate to **Settings** > **Sync Hub** to modify default settings.
2. **Data Flow**:
   - Nodes send or receive data based on the specified modes, either pushing data to the hub or pulling from nodes.

### Notes

- Existing devices on the hub will not be updated by the data received from this SYNC plugin if their MAC addresses are already present.
- It is recommended to use Device synchronization primarily. Plugin data synchronization is more suitable for specific use cases.

![Sync Hub Setup Diagram](/front/plugins/sync/sync_hub.png)

### Example use case: Network Setup with Multiple VLANs and VM Scanning

> Thank you to [@richtj999](https://github.com/richtj999) for the use case 🙏

I have 6 VLANs, all isolated by a firewall, except for one VLAN that has access to all the others.

Initially, I had one virtual machine (VM) with 6 network cards, one for each VLAN. While this setup worked, it introduced delays due to other concurrent scans. To optimize this, I switched to a multi-VM setup:

- I created 6 VMs, each attached to a single VLAN. 
- One VM acts as the "server," and the other 5 as "clients."
- The server has access to all VLANs (via firewall rules) and collects data from the client VMs, which each scan their own VLAN.

#### Summary

- **Single VM on six VLANs**: Slower because one VM scans all networks.
- **Six VMs on six VLANs**: Faster because each VM scans its own network, sending the results to the server.

#### Example Setup

- **VM1 ("Server")**: Network 1 (can access all networks) - IP: `10.10.10.106`  
  Receives data from all NetAlertX clients and scans network 1.

- **VM2 ("Client")**: Network 2 (can access only network 2) - IP: `192.168.x.x`  
  Scans network 2; VM1 retrieves this data.

- **VM3 ("Client")**: Network 3 (can access only network 3) - IP: `192.168.x.x`  
  Scans network 3; VM1 retrieves this data.

- **VM4 ("Client")**: Network 4 (can access only network 4) - IP: `192.168.x.x`  
  Scans network 4; VM1 retrieves this data.

- **VM5 ("Client")**: Network 5 (can access only network 5) - IP: `192.168.x.x`  
  Scans network 5; VM1 retrieves this data.

- **VM6 ("Client")**: Network 6 (can access only network 6) - IP: `192.168.x.x`  
  Scans network 6; VM1 retrieves this data.

---

#### How to Set It Up

##### Server (VM1)

1. Go to **Settings > System > Sync Hub**.
2. Set the schedule (5 minutes works for me).
3. **API Token**: Use any string, but it must match the clients (e.g., `abc123`).
4. **Encryption Key**: Use any string, but it must match the clients (e.g., `abc123`).
5. Under **Nodes**, add the full URL for each client, e.g., `http://192.168.1.20.20212/`, where the port `20212` is the value of the `GRAPHQL_PORT` setting of the given node (client)
6. **Node Name**: Leave blank.
7. Check **Sync Devices**.

##### Clients (VM2, VM3, VM4, VM5, VM6)

1. Go to **Settings > System > Sync Hub**.
2. Set **When to run** to "Always after scan."
3. **API Token**: Use the same token as the server (e.g., `abc123`).
4. **Encryption Key**: Use the same key as the server (e.g., `abc123`).
5. Leave **Nodes** blank.
6. Set **Node Name** to a unique, memorable name for each client.
7. Check **Sync Devices**.


