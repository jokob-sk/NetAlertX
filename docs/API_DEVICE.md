# Device API Endpoints

Manage a **single device** by its MAC address. Operations include retrieval, updates, deletion, resetting properties, and copying data between devices. All endpoints require **authorization** via Bearer token.

---

## 1. Retrieve Device Details

* **GET** `/device/<mac>`
  Fetch all details for a single device, including:

* Computed status (`devStatus`) → `On-line`, `Off-line`, or `Down`
* Session and event counts (`devSessions`, `devEvents`, `devDownAlerts`)
* Presence hours (`devPresenceHours`)
* Children devices (`devChildrenDynamic`) and NIC children (`devChildrenNicsDynamic`)

**Special case**: `mac=new` returns a template for a new device with default values.

**Response** (success):

```json
{
  "devMac": "AA:BB:CC:DD:EE:FF",
  "devName": "Net - Huawei",
  "devOwner": "Admin",
  "devType": "Router",
  "devVendor": "Huawei",
  "devStatus": "On-line",
  "devSessions": 12,
  "devEvents": 5,
  "devDownAlerts": 1,
  "devPresenceHours": 32,
  "devChildrenDynamic": [...],
  "devChildrenNicsDynamic": [...],
  ...
}
```

**Error Responses**:

* Device not found → HTTP 404
* Unauthorized → HTTP 403

**MCP Integration**: Available as `get_device_info` and `set_device_alias` tools. See [MCP Server Bridge API](API_MCP.md).

---

## 2. Update Device Fields

* **POST** `/device/<mac>`
  Create or update a device record.

**Request Body**:

```json
{
  "devName": "New Device",
  "devOwner": "Admin",
  "createNew": true
}
```

**Behavior**:

* If `createNew=true` → creates a new device
* Otherwise → updates existing device fields

**Response**:

```json
{
  "success": true
}
```

**Error Responses**:

* Unauthorized → HTTP 403

---

## 3. Delete a Device

* **DELETE** `/device/<mac>/delete`
  Deletes the device with the given MAC.

**Response**:

```json
{
  "success": true
}
```

**Error Responses**:

* Unauthorized → HTTP 403

---

## 4. Delete All Events for a Device

* **DELETE** `/device/<mac>/events/delete`
  Removes all events associated with a device.

**Response**:

```json
{
  "success": true
}
```

---

## 5. Reset Device Properties

* **POST** `/device/<mac>/reset-props`
  Resets the device's custom properties to default values.

**Request Body**: Optional JSON for additional parameters.

**Response**:

```json
{
  "success": true
}
```

---

## 6. Copy Device Data

* **POST** `/device/copy`
  Copy all data from one device to another. If a device exists with `macTo`, it is replaced.

**Request Body**:

```json
{
  "macFrom": "AA:BB:CC:DD:EE:FF",
  "macTo": "11:22:33:44:55:66"
}
```

**Response**:

```json
{
  "success": true,
  "message": "Device copied from AA:BB:CC:DD:EE:FF to 11:22:33:44:55:66"
}
```

**Error Responses**:

* Missing `macFrom` or `macTo` → HTTP 400
* Unauthorized → HTTP 403

---

## 7. Update a Single Column

* **POST** `/device/<mac>/update-column`
  Update one specific column for a device.

**Request Body**:

```json
{
  "columnName": "devName",
  "columnValue": "Updated Device Name"
}
```

**Response** (success):

```json
{
  "success": true
}
```

**Error Responses**:

* Device not found → HTTP 404
* Missing `columnName` or `columnValue` → HTTP 400
* Unauthorized → HTTP 403

---

## Example `curl` Requests

**Get Device Details**:

```bash
curl -X GET "http://<server_ip>:<GRAPHQL_PORT>/device/AA:BB:CC:DD:EE:FF" \
  -H "Authorization: Bearer <API_TOKEN>"
```

**Update Device Fields**:

```bash
curl -X POST "http://<server_ip>:<GRAPHQL_PORT>/device/AA:BB:CC:DD:EE:FF" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Content-Type: application/json" \
  --data '{"devName": "New Device Name"}'
```

**Delete Device**:

```bash
curl -X DELETE "http://<server_ip>:<GRAPHQL_PORT>/device/AA:BB:CC:DD:EE:FF/delete" \
  -H "Authorization: Bearer <API_TOKEN>"
```

**Copy Device Data**:

```bash
curl -X POST "http://<server_ip>:<GRAPHQL_PORT>/device/copy" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Content-Type: application/json" \
  --data '{"macFrom":"AA:BB:CC:DD:EE:FF","macTo":"11:22:33:44:55:66"}'
```

**Update Single Column**:

```bash
curl -X POST "http://<server_ip>:<GRAPHQL_PORT>/device/AA:BB:CC:DD:EE:FF/update-column" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Content-Type: application/json" \
  --data '{"columnName":"devName","columnValue":"Updated Device"}'
```

