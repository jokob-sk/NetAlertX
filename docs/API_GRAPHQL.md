# GraphQL API Endpoint

GraphQL queries are **read-optimized for speed**. Data may be slightly out of date until the file system cache refreshes. The GraphQL endpoints allows you to access the following objects:

- Devices
- Settings

## Endpoints

* **GET** `/graphql`
  Returns a simple status message (useful for browser or debugging).

* **POST** `/graphql`
  Execute GraphQL queries against the `devicesSchema`.

---

## Devices Query

### Sample Query

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

### Query Parameters

| Parameter | Description                                                                                             |
| --------- | ------------------------------------------------------------------------------------------------------- |
| `page`    | Page number of results to fetch.                                                                        |
| `limit`   | Number of results per page.                                                                             |
| `sort`    | Sorting options (`field` = field name, `order` = `asc` or `desc`).                                      |
| `search`  | Term to filter devices.                                                                                 |
| `status`  | Filter devices by status: `my_devices`, `connected`, `favorites`, `new`, `down`, `archived`, `offline`. |
| `filters` | Additional filters (array of `{ filterColumn, filterValue }`).                                          |

---

### `curl` Example

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

### Sample Response

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
        }
      ],
      "count": 1
    }
  }
}
```

---

## Settings Query

The **settings query** provides access to NetAlertX configuration stored in the settings table.

### Sample Query

```graphql
query GetSettings {
  settings {
    settings {
      setKey
      setName
      setDescription
      setType
      setOptions
      setGroup
      setValue
      setEvents
      setOverriddenByEnv
    }
    count
  }
}
```

### Schema Fields

| Field                | Type    | Description                                                              |
| -------------------- | ------- | ------------------------------------------------------------------------ |
| `setKey`             | String  | Unique key identifier for the setting.                                   |
| `setName`            | String  | Human-readable name.                                                     |
| `setDescription`     | String  | Description or documentation of the setting.                             |
| `setType`            | String  | Data type (`string`, `int`, `bool`, `json`, etc.).                       |
| `setOptions`         | String  | Available options (for dropdown/select-type settings).                   |
| `setGroup`           | String  | Group/category the setting belongs to.                                   |
| `setValue`           | String  | Current value of the setting.                                            |
| `setEvents`          | String  | Events or triggers related to this setting.                              |
| `setOverriddenByEnv` | Boolean | Whether the setting is overridden by an environment variable at runtime. |

---

### `curl` Example

```sh
curl 'http://host:GRAPHQL_PORT/graphql' \
  -X POST \
  -H 'Authorization: Bearer API_TOKEN' \
  -H 'Content-Type: application/json' \
  --data '{
    "query": "query GetSettings { settings { settings { setKey setName setDescription setType setOptions setGroup setValue setEvents setOverriddenByEnv } count } }"
  }'
```

---

### Sample Response

```json
{
  "data": {
    "settings": {
      "settings": [
        {
          "setKey": "UI_MY_DEVICES",
          "setName": "My Devices Filter",
          "setDescription": "Defines which statuses to include in the 'My Devices' view.",
          "setType": "list",
          "setOptions": "[\"online\",\"new\",\"down\",\"offline\",\"archived\"]",
          "setGroup": "UI",
          "setValue": "[\"online\",\"new\"]",
          "setEvents": null,
          "setOverriddenByEnv": false
        },
        {
          "setKey": "NETWORK_DEVICE_TYPES",
          "setName": "Network Device Types",
          "setDescription": "Types of devices considered as network infrastructure.",
          "setType": "list",
          "setOptions": "[\"Router\",\"Switch\",\"AP\"]",
          "setGroup": "Network",
          "setValue": "[\"Router\",\"Switch\"]",
          "setEvents": null,
          "setOverriddenByEnv": true
        }
      ],
      "count": 2
    }
  }
}
```

---

## Notes

* Device and settings queries can be combined in one request since GraphQL supports batching.
* The `setOverriddenByEnv` flag helps identify setting values that are locked at container runtime.
* The schema is **read-only** — updates must be performed through other APIs or configuration management. See the other [API](API.md) endpoints for details. 

