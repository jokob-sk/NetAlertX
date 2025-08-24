# NetAlertX API Documentation

This API provides programmatic access to **devices, events, sessions, metrics, network tools, and sync** in NetAlertX. It is implemented as a **REST and GraphQL server**. All requests require authentication via **API Token** (`API_TOKEN` setting) unless explicitly noted.

```graphql
curl 'http://host:GRAPHQL_PORT/graphql' \
  -X POST \
  -H 'Authorization: Bearer API_TOKEN' \
  -H 'Content-Type: application/json' \
  --data '{
    "query": "query GetDevices($options: PageQueryOptionsInput) { devices(options: $options) { devices { rowid devMac devName devOwner devType devVendor devLastConnection devStatus } count } }",
    "variables": {
      "options": {
        "page": 1,
        "limit": 10,
        "sort": [{ "field": "devName", "order": "asc" }],
        "search": "",
        "status": "connected"
      }
    }
  }'
```

It runs on `0.0.0.0:<graphql_port>` with **CORS enabled** for all main endpoints.

---

## Authentication

All endpoints require an API token provided in the HTTP headers:

```http
Authorization: Bearer <API_TOKEN>
```

If the token is missing or invalid, the server will return:

```json
{ "error": "Forbidden" }
```

---

## Base URL

```
http://<server>:<GRAPHQL_PORT>/
```

---

## Endpoints


> [!TIP]
> When retrieving devices try using the GraphQL API endpoint first as it is read-optimized.

* [Device API Endpoints](API_DEVICE.md) – Manage individual devices
* [Devices Collection](API_DEVICES.md) – Bulk operations on multiple devices
* [Events](API_EVENTS.md) – Device event logging and management
* [Sessions](API_SESSIONS.md) – Connection sessions and history
* [Metrics](API_METRICS.md) – Prometheus metrics and per-device status
* [Network Tools](API_NETTOOLS.md) – Utilities like Wake-on-LAN, traceroute, nslookup, nmap, and internet info
* [Online History](API_ONLINEHISTORY.md) – Online/offline device records
* [GraphQL](API_GRAPHQL.md) – Advanced queries and filtering
* [Sync](API_SYNC.md) – Synchronization between multiple NetAlertX instances

See [Testing](API_TESTS.md) for example requests and usage.

---

## Notes

* All endpoints enforce **Bearer token authentication**.
* Errors return JSON with `success: False` and an error message.
* GraphQL is available for advanced queries, while REST endpoints cover structured use cases.
* Endpoints run on `0.0.0.0:<GRAPHQL_PORT>` with **CORS enabled**.
* Use consistent API tokens and node/plugin names when interacting with `/sync` to ensure data integrity.


