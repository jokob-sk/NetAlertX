# Events API Endpoints

The Events API provides access to **device event logs**, allowing creation, retrieval, deletion, and summary of events over time.

---

## Endpoints

### 1. Create Event

* **POST** `/events/create/<mac>`
  Create an event for a device identified by its MAC address.

**Request Body** (JSON):

```json
{
  "ip": "192.168.1.10",
  "event_type": "Device Down",
  "additional_info": "Optional info about the event",
  "pending_alert": 1,
  "event_time": "2025-08-24T12:00:00Z"
}
```

* **Parameters**:

  * `ip` (string, optional): IP address of the device
  * `event_type` (string, optional): Type of event (default `"Device Down"`)
  * `additional_info` (string, optional): Extra information
  * `pending_alert` (int, optional): 1 if alert email is pending (default 1)
  * `event_time` (ISO datetime, optional): Event timestamp; defaults to current time

**Response** (JSON):

```json
{
  "success": true,
  "message": "Event created for 00:11:22:33:44:55"
}
```

---

### 2. Get Events

* **GET** `/events`
  Retrieve all events, optionally filtered by MAC address:

```
/events?mac=<mac>
```

**Response**:

```json
{
  "success": true,
  "events": [
    {
      "eve_MAC": "00:11:22:33:44:55",
      "eve_IP": "192.168.1.10",
      "eve_DateTime": "2025-08-24T12:00:00Z",
      "eve_EventType": "Device Down",
      "eve_AdditionalInfo": "",
      "eve_PendingAlertEmail": 1
    }
  ]
}
```

---

### 3. Delete Events

* **DELETE** `/events/<mac>` → Delete events for a specific MAC
* **DELETE** `/events` → Delete **all** events
* **DELETE** `/events/<days>` → Delete events older than N days

**Response**:

```json
{
  "success": true,
  "message": "Deleted events older than <days> days"
}
```

---

### 4. Event Totals Over a Period

* **GET** `/sessions/totals?period=<period>`
  Return event and session totals over a given period.

**Query Parameters**:

| Parameter | Description                                                                      |
| --------- | -------------------------------------------------------------------------------- |
| `period`  | Time period for totals, e.g., `"7 days"`, `"1 month"`, `"1 year"`, `"100 years"` |

**Sample Response** (JSON Array):

```json
[120, 85, 5, 10, 3, 7]
```

**Meaning of Values**:

1. Total events in the period
2. Total sessions
3. Missing sessions
4. Voided events (`eve_EventType LIKE 'VOIDED%'`)
5. New device events (`eve_EventType LIKE 'New Device'`)
6. Device down events (`eve_EventType LIKE 'Device Down'`)

---

## Notes

* All endpoints require **authorization** (Bearer token). Unauthorized requests return:

```json
{ "error": "Forbidden" }
```

* Events are stored in the **Events table** with the following fields:
  `eve_MAC`, `eve_IP`, `eve_DateTime`, `eve_EventType`, `eve_AdditionalInfo`, `eve_PendingAlertEmail`.

* Event creation automatically logs activity for debugging.

---

## Example `curl` Requests

**Create Event**:

```sh
curl -X POST "http://<server_ip>:<GRAPHQL_PORT>/events/create/00:11:22:33:44:55" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Content-Type: application/json" \
  --data '{
    "ip": "192.168.1.10",
    "event_type": "Device Down",
    "additional_info": "Power outage",
    "pending_alert": 1
  }'
```

**Get Events for a Device**:

```sh
curl "http://<server_ip>:<GRAPHQL_PORT>/events?mac=00:11:22:33:44:55" \
  -H "Authorization: Bearer <API_TOKEN>"
```

**Delete Events Older Than 30 Days**:

```sh
curl -X DELETE "http://<server_ip>:<GRAPHQL_PORT>/events/30" \
  -H "Authorization: Bearer <API_TOKEN>"
```

**Get Event Totals for 7 Days**:

```sh
curl "http://<server_ip>:<GRAPHQL_PORT>/sessions/totals?period=7 days" \
  -H "Authorization: Bearer <API_TOKEN>"
```
