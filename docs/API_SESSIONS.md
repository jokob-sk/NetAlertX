# Sessions API Endpoints

Track and manage device connection sessions. Sessions record when a device connects or disconnects on the network.

### Create a Session

* **POST** `/sessions/create` → Create a new session for a device

  **Request Body:**

  ```json
  {
    "mac": "AA:BB:CC:DD:EE:FF",
    "ip": "192.168.1.10",
    "start_time": "2025-08-01T10:00:00",
    "end_time": "2025-08-01T12:00:00",      // optional
    "event_type_conn": "Connected",         // optional, default "Connected"
    "event_type_disc": "Disconnected"       // optional, default "Disconnected"
  }
  ```

  **Response:**

  ```json
  {
    "success": true,
    "message": "Session created for MAC AA:BB:CC:DD:EE:FF"
  }
  ```

#### `curl` Example

```bash
curl -X POST "http://<server_ip>:<GRAPHQL_PORT>/sessions/create" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "mac": "AA:BB:CC:DD:EE:FF",
    "ip": "192.168.1.10",
    "start_time": "2025-08-01T10:00:00",
    "end_time": "2025-08-01T12:00:00",
    "event_type_conn": "Connected",
    "event_type_disc": "Disconnected"
  }'

```

---

### Delete Sessions

* **DELETE** `/sessions/delete` → Delete all sessions for a given MAC

  **Request Body:**

  ```json
  {
    "mac": "AA:BB:CC:DD:EE:FF"
  }
  ```

  **Response:**

  ```json
  {
    "success": true,
    "message": "Deleted sessions for MAC AA:BB:CC:DD:EE:FF"
  }
  ```

#### `curl` Example

```bash
curl -X DELETE "http://<server_ip>:<GRAPHQL_PORT>/sessions/delete" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "mac": "AA:BB:CC:DD:EE:FF"
  }'
```

---

### List Sessions

* **GET** `/sessions/list` → Retrieve sessions optionally filtered by device and date range

  **Query Parameters:**

  * `mac` (optional) → Filter by device MAC address
  * `start_date` (optional) → Filter sessions starting from this date (`YYYY-MM-DD`)
  * `end_date` (optional) → Filter sessions ending by this date (`YYYY-MM-DD`)

  **Example:**

  ```
  /sessions/list?mac=AA:BB:CC:DD:EE:FF&start_date=2025-08-01&end_date=2025-08-21
  ```

  **Response:**

  ```json
  {
    "success": true,
    "sessions": [
      {
        "ses_MAC": "AA:BB:CC:DD:EE:FF",
        "ses_Connection": "2025-08-01 10:00",
        "ses_Disconnection": "2025-08-01 12:00",
        "ses_Duration": "2h 0m",
        "ses_IP": "192.168.1.10",
        "ses_Info": ""
      }
    ]
  }
  ```
#### `curl` Example

**get sessions for mac**

```bash
curl -X GET "http://<server_ip>:<GRAPHQL_PORT>/sessions/list?mac=AA:BB:CC:DD:EE:FF&start_date=2025-08-01&end_date=2025-08-21" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Accept: application/json"
```

---

### Calendar View of Sessions

* **GET** `/sessions/calendar` → View sessions in calendar format

  **Query Parameters:**

  * `start` → Start date (`YYYY-MM-DD`)
  * `end` → End date (`YYYY-MM-DD`)

  **Example:**

  ```
  /sessions/calendar?start=2025-08-01&end=2025-08-21
  ```

  **Response:**

  ```json
  {
    "success": true,
    "sessions": [
      {
        "resourceId": "AA:BB:CC:DD:EE:FF",
        "title": "",
        "start": "2025-08-01T10:00:00",
        "end": "2025-08-01T12:00:00",
        "color": "#00a659",
        "tooltip": "Connection: 2025-08-01 10:00\nDisconnection: 2025-08-01 12:00\nIP: 192.168.1.10",
        "className": "no-border"
      }
    ]
  }
  ```

#### `curl` Example

```bash
curl -X GET "http://<server_ip>:<GRAPHQL_PORT>/sessions/calendar?start=2025-08-01&end=2025-08-21" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Accept: application/json"
```

---

### Device Sessions

* **GET** `/sessions/<mac>` → Retrieve sessions for a specific device

  **Query Parameters:**

  * `period` → Period to retrieve sessions (`1 day`, `7 days`, `1 month`, etc.)
    Default: `1 day`

  **Example:**

  ```
  /sessions/AA:BB:CC:DD:EE:FF?period=7 days
  ```

  **Response:**

  ```json
  {
    "success": true,
    "sessions": [
      {
        "ses_MAC": "AA:BB:CC:DD:EE:FF",
        "ses_Connection": "2025-08-01 10:00",
        "ses_Disconnection": "2025-08-01 12:00",
        "ses_Duration": "2h 0m",
        "ses_IP": "192.168.1.10",
        "ses_Info": ""
      }
    ]
  }
  ```

#### `curl` Example

```bash
curl -X GET "http://<server_ip>:<GRAPHQL_PORT>/sessions/AA:BB:CC:DD:EE:FF?period=7%20days" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Accept: application/json"
```

---

### Session Events Summary

* **GET** `/sessions/session-events` → Retrieve a summary of session events

  **Query Parameters:**

  * `type` → Event type (`all`, `sessions`, `missing`, `voided`, `new`, `down`)
    Default: `all`
  * `period` → Period to retrieve events (`7 days`, `1 month`, etc.)

  **Example:**

  ```
  /sessions/session-events?type=all&period=7 days
  ```

  **Response:**
  Returns a list of events or sessions with formatted connection, disconnection, duration, and IP information.

#### `curl` Example

```bash
curl -X GET "http://<server_ip>:<GRAPHQL_PORT>/sessions/session-events?type=all&period=7%20days" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Accept: application/json"
```