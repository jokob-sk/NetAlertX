# GraphQL API Endpoint

GraphQL queries are read-optimized for speed. Data may be slightly out of date until the file system cache refreshes.

## Endpoints

* **GET** `/graphql`
  Returns a simple status message (useful for browser or debugging).

* **POST** `/graphql`
  Execute GraphQL queries against the `devicesSchema`.

---

## Sample Query

```graphql
query GetDevices($options: PageQueryOptionsInput) {
  devices(options: $options) {
    devices {
      rowid
      devMac
      devName
      devOwner
      devType
      devVendor
      devLastConnection
      devStatus
    }
    count
  }
}
```

See also: [Debugging GraphQL issues](./DEBUG_GRAPHQL.md)

---

## `curl` Example

```sh
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

---

## Query Parameters

| Parameter | Description                                                                                             |
| --------- | ------------------------------------------------------------------------------------------------------- |
| `page`    | Page number of results to fetch.                                                                        |
| `limit`   | Number of results per page.                                                                             |
| `sort`    | Sorting options (`field` = field name, `order` = `asc` or `desc`).                                      |
| `search`  | Term to filter devices.                                                                                 |
| `status`  | Filter devices by status: `my_devices`, `connected`, `favorites`, `new`, `down`, `archived`, `offline`. |

---

## Notes on `curl`

* `-X POST` specifies a POST request.
* `-H 'Content-Type: application/json'` sets JSON content type.
* `--data` provides the request payload (GraphQL query + variables).

---

## Sample Response

```json
{
  "data": {
    "devices": {
      "devices": [
        {
          "rowid": 1,
          "devMac": "00:11:22:33:44:55",
          "devName": "Device 1",
          "devOwner": "Owner 1",
          "devType": "Type 1",
          "devVendor": "Vendor 1",
          "devLastConnection": "2025-01-01T00:00:00Z",
          "devStatus": "connected"
        },
        {
          "rowid": 2,
          "devMac": "66:77:88:99:AA:BB",
          "devName": "Device 2",
          "devOwner": "Owner 2",
          "devType": "Type 2",
          "devVendor": "Vendor 2",
          "devLastConnection": "2025-01-02T00:00:00Z",
          "devStatus": "connected"
        }
      ],
      "count": 2
    }
  }
}
```
