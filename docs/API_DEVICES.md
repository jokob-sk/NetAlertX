# Devices Collection API Endpoints

The Devices Collection API provides operations to **retrieve, manage, import/export, and filter devices** in bulk. All endpoints require **authorization** via Bearer token.

---

## Endpoints

### 1. Get All Devices

* **GET** `/devices`
  Retrieves all devices from the database.

**Response** (success):

```json
{
  "success": true,
  "devices": [
    {
      "devName": "Net - Huawei",
      "devMAC": "AA:BB:CC:DD:EE:FF",
      "devIP": "192.168.1.1",
      "devType": "Router",
      "devFavorite": 0,
      "devStatus": "online"
    },
    ...
  ]
}
```

**Error Responses**:

* Unauthorized → HTTP 403

---

### 2. Delete Devices by MAC

* **DELETE** `/devices`
  Deletes devices by MAC address. Supports exact matches or wildcard `*`.

**Request Body**:

```json
{
  "macs": ["AA:BB:CC:DD:EE:FF", "11:22:33:*"]
}
```

**Behavior**:

* If `macs` is omitted or `null` → deletes **all devices**.
* Wildcards `*` match multiple devices.

**Response**:

```json
{
  "success": true,
  "deleted_count": 5
}
```

**Error Responses**:

* Unauthorized → HTTP 403

---

### 3. Delete Devices with Empty MACs

* **DELETE** `/devices/empty-macs`
  Removes all devices where MAC address is null or empty.

**Response**:

```json
{
  "success": true,
  "deleted": 3
}
```

---

### 4. Delete Unknown Devices

* **DELETE** `/devices/unknown`
  Deletes devices with names marked as `(unknown)` or `(name not found)`.

**Response**:

```json
{
  "success": true,
  "deleted": 2
}
```

---

### 5. Export Devices

* **GET** `/devices/export` or `/devices/export/<format>`
  Exports all devices in **CSV** (default) or **JSON** format.

**Query Parameter / URL Parameter**:

* `format` (optional) → `csv` (default) or `json`

**CSV Response**:

* Returns as a downloadable CSV file: `Content-Disposition: attachment; filename=devices.csv`

**JSON Response**:

```json
{
  "data": [
    { "devName": "Net - Huawei", "devMAC": "AA:BB:CC:DD:EE:FF", ... },
    ...
  ],
  "columns": ["devName", "devMAC", "devIP", "devType", "devFavorite", "devStatus"]
}
```

**Error Responses**:

* Unsupported format → HTTP 400

---

### 6. Import Devices from CSV

* **POST** `/devices/import`
  Imports devices from an uploaded CSV or base64-encoded CSV content.

**Request Body** (multipart file or JSON with `content` field):

```json
{
  "content": "<base64-encoded CSV content>"
}
```

**Response**:

```json
{
  "success": true,
  "inserted": 25,
  "skipped_lines": [3, 7]
}
```

**Error Responses**:

* Missing file or content → HTTP 400 / 404
* CSV malformed → HTTP 400

---

### 7. Get Device Totals

* **GET** `/devices/totals`
  Returns counts of devices by various categories.

**Response**:

```json
[ 
  120,    // Total devices
  85,     // Connected
  5,      // Favorites
  10,     // New
  8,      // Down
  12      // Archived
]
```

*Order: `[all, connected, favorites, new, down, archived]`*

---

### 8. Get Devices by Status

* **GET** `/devices/by-status?status=<status>`
  Returns devices filtered by status.

**Query Parameter**:

* `status` → Supported values: `online`, `offline`, `down`, `archived`, `favorites`, `new`, `my`
* If omitted, returns **all devices**.

**Response** (success):

```json
[
  { "id": "AA:BB:CC:DD:EE:FF", "title": "Net - Huawei", "favorite": 0 },
  { "id": "11:22:33:44:55:66", "title": "★ USG Firewall", "favorite": 1 }
]
```

*If `devFavorite=1`, the title is prepended with a star `★`.*

---

## Example `curl` Requests

**Get All Devices**:

```sh
curl -X GET "http://<server_ip>:<GRAPHQL_PORT>/devices" \
  -H "Authorization: Bearer <API_TOKEN>"
```

**Delete Devices by MAC**:

```sh
curl -X DELETE "http://<server_ip>:<GRAPHQL_PORT>/devices" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Content-Type: application/json" \
  --data '{"macs":["AA:BB:CC:DD:EE:FF","11:22:33:*"]}'
```

**Export Devices CSV**:

```sh
curl -X GET "http://<server_ip>:<GRAPHQL_PORT>/devices/export?format=csv" \
  -H "Authorization: Bearer <API_TOKEN>"
```

**Import Devices from CSV**:

```sh
curl -X POST "http://<server_ip>:<GRAPHQL_PORT>/devices/import" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -F "file=@devices.csv"
```

**Get Devices by Status**:

```sh
curl -X GET "http://<server_ip>:<GRAPHQL_PORT>/devices/by-status?status=online" \
  -H "Authorization: Bearer <API_TOKEN>"
```

