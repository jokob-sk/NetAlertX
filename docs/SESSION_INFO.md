# Sessions Section in Device View

The **Sessions Section** provides details about a device's connection history. This data is automatically detected and cannot be edited by the user.

 ![Session info](./img/SESSION_INFO/DeviceDetails_SessionInfo.png)

---

## Key Fields

1. **Date and Time of First Connection**
   - **Description:** Displays the first detected connection time for the device.
   - **Editability:** Uneditable (auto-detected).
   - **Source:** Automatically captured when the device is first added to the system.

2. **Date and Time of Last Connection**
   - **Description:** Shows the most recent time the device was online.
   - **Editability:** Uneditable (auto-detected).
   - **Source:** Updated with every new connection event.

3. **Offline Devices with Missing or Conflicting Data**
   - **Description:** Handles cases where a device is offline but has incomplete or conflicting session data (e.g., missing start times).
   - **Handling:** The system flags these cases for review and attempts to infer missing details.

---

## How Sessions are Discovered and Calculated

### 1. Detecting New Devices
When a device is first detected in the network, the system logs it in the events table:

`INSERT INTO Events (eve_MAC, eve_IP, eve_DateTime, eve_EventType, eve_AdditionalInfo, eve_PendingAlertEmail) SELECT cur_MAC, cur_IP, '{startTime}', 'New Device', cur_Vendor, 1 FROM CurrentScan WHERE NOT EXISTS (SELECT 1 FROM Devices WHERE devMac = cur_MAC)`

- Devices scanned in the current cycle (**CurrentScan**) are checked against the **Devices** table.
- If a device is new:
  - A **New Device** event is logged.
  - The device’s MAC, IP, vendor, and detection time are recorded.

### 2. Logging Connection Sessions
When a new connection is detected, the system creates a session record:

`INSERT INTO Sessions (ses_MAC, ses_IP, ses_EventTypeConnection, ses_DateTimeConnection, ses_EventTypeDisconnection, ses_DateTimeDisconnection, ses_StillConnected, ses_AdditionalInfo) SELECT cur_MAC, cur_IP, 'Connected', '{startTime}', NULL, NULL, 1, cur_Vendor FROM CurrentScan WHERE NOT EXISTS (SELECT 1 FROM Sessions WHERE ses_MAC = cur_MAC)`

- A new session is logged in the **Sessions** table if no prior session exists.
- Fields like `MAC`, `IP`, `Connection Type`, and `Connection Time` are populated.
- The `Still Connected` flag is set to `1` (active connection).

### 3. Handling Missing or Conflicting Data
- Devices with incomplete or conflicting session data (e.g., missing start times) are detected.
- The system flags these records and attempts corrections by inferring details from available data.

### 4. Updating Sessions
- When a device reconnects, its session is updated with a new connection timestamp.
- When a device disconnects:
  - The **Disconnection Time** is recorded.
  - The `Still Connected` flag is set to `0`.

The session information is then used to display the device presence under **Monitoring** -> **Presence**.

![Monitoring Device Presence](./img/SESSION_INFO/Monitoring_Presence.png)


