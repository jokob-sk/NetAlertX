# GraphQL API Endpoint

GraphQL queries are **read-optimized for speed**. Data may be slightly out of date until the file system cache refreshes. The GraphQL endpoints allow you to access the following objects:

* Devices
* Device History (change audit log)
* Settings
* Events
* PluginsObjects
* PluginsHistory
* PluginsEvents
* Language Strings (LangStrings)

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

## LangStrings Query

The **LangStrings query** provides access to localized strings. Supports filtering by `langCode` and `langStringKey`. If the requested string is missing or empty, you can optionally fallback to `en_us`.

### Sample Query

```graphql
query GetLangStrings {
  langStrings(langCode: "de_de", langStringKey: "settings_other_scanners") {
    langStrings {
      langCode
      langStringKey
      langStringText
    }
    count
  }
}
```

### Query Parameters

| Parameter        | Type    | Description                                                                              |
| ---------------- | ------- | ---------------------------------------------------------------------------------------- |
| `langCode`       | String  | Optional language code (e.g., `en_us`, `de_de`). If omitted, all languages are returned. |
| `langStringKey`  | String  | Optional string key to retrieve a specific entry.                                        |
| `fallback_to_en` | Boolean | Optional (default `true`). If `true`, empty or missing strings fallback to `en_us`.      |

### `curl` Example

```sh
curl 'http://host:GRAPHQL_PORT/graphql' \
  -X POST \
  -H 'Authorization: Bearer API_TOKEN' \
  -H 'Content-Type: application/json' \
  --data '{
    "query": "query GetLangStrings { langStrings(langCode: \"de_de\", langStringKey: \"settings_other_scanners\") { langStrings { langCode langStringKey langStringText } count } }"
  }'
```

### Sample Response

```json
{
  "data": {
    "langStrings": {
      "count": 1,
      "langStrings": [
        {
          "langCode": "de_de",
          "langStringKey": "settings_other_scanners",
          "langStringText": "Other, non-device scanner plugins that are currently enabled."  // falls back to en_us if empty
        }
      ]
    }
  }
}
```

---

## Plugin Tables (Objects, Events, History)

Three queries expose the plugin database tables with server-side pagination, filtering, and search:

* `pluginsObjects` — current plugin object state
* `pluginsEvents` — unprocessed plugin events
* `pluginsHistory` — historical plugin event log

All three share the same `PluginQueryOptionsInput` and return the same `PluginEntry` shape.

### Sample Query

```graphql
query GetPluginObjects($options: PluginQueryOptionsInput) {
  pluginsObjects(options: $options) {
    dbCount
    count
    entries {
      index plugin objectPrimaryId objectSecondaryId
      dateTimeCreated dateTimeChanged
      watchedValue1 watchedValue2 watchedValue3 watchedValue4
      status extra userData foreignKey
      syncHubNodeName helpVal1 helpVal2 helpVal3 helpVal4 objectGuid
    }
  }
}
```

### Query Parameters (`PluginQueryOptionsInput`)

| Parameter    | Type              | Description                                            |
| ------------ | ----------------- | ------------------------------------------------------ |
| `page`       | Int               | Page number (1-based).                                 |
| `limit`      | Int               | Rows per page (max 1000).                              |
| `sort`       | [SortOptionsInput] | Sorting options (`field`, `order`).                   |
| `search`     | String            | Free-text search across key columns.                   |
| `filters`    | [FilterOptionsInput] | Column-value exact-match filters.                   |
| `plugin`     | String            | Plugin prefix to scope results (e.g. `"ARPSCAN"`).    |
| `foreignKey` | String            | Foreign key filter (e.g. device MAC).                  |
| `dateFrom`   | String            | Start of date range filter on `dateTimeCreated`.       |
| `dateTo`     | String            | End of date range filter on `dateTimeCreated`.         |

### Response Fields

| Field     | Type          | Description                                                   |
| --------- | ------------- | ------------------------------------------------------------- |
| `dbCount` | Int           | Total rows for the requested plugin (before search/filters).  |
| `count`   | Int           | Total rows after all filters (before pagination).             |
| `entries` | [PluginEntry] | Paginated list of plugin entries.                             |

### `curl` Example

```sh
curl 'http://host:GRAPHQL_PORT/graphql' \
  -X POST \
  -H 'Authorization: Bearer API_TOKEN' \
  -H 'Content-Type: application/json' \
  --data '{
    "query": "query GetPluginObjects($options: PluginQueryOptionsInput) { pluginsObjects(options: $options) { dbCount count entries { index plugin objectPrimaryId status foreignKey } } }",
    "variables": {
      "options": {
        "plugin": "ARPSCAN",
        "page": 1,
        "limit": 25
      }
    }
  }'
```

### Badge Prefetch (Batched Counts)

Use GraphQL aliases to fetch counts for all plugins in a single request:

```graphql
query BadgeCounts {
  ARPSCAN: pluginsObjects(options: {plugin: "ARPSCAN", page: 1, limit: 1}) { dbCount }
  INTRNT:  pluginsObjects(options: {plugin: "INTRNT",  page: 1, limit: 1}) { dbCount }
}
```

---

## Events Query

Access the Events table with server-side pagination, filtering, and search.

### Sample Query

```graphql
query GetEvents($options: EventQueryOptionsInput) {
  events(options: $options) {
    dbCount
    count
    entries {
      eveMac
      eveIp
      eveDateTime
      eveEventType
      eveAdditionalInfo
      evePendingAlertEmail
    }
  }
}
```

### Query Parameters (`EventQueryOptionsInput`)

| Parameter   | Type               | Description                                      |
| ----------- | ------------------ | ------------------------------------------------ |
| `page`      | Int                | Page number (1-based).                           |
| `limit`     | Int                | Rows per page (max 1000).                        |
| `sort`      | [SortOptionsInput]  | Sorting options (`field`, `order`).              |
| `search`    | String             | Free-text search across key columns.             |
| `filters`   | [FilterOptionsInput] | Column-value exact-match filters.              |
| `eveMac`    | String             | Filter by device MAC address.                    |
| `eventType` | String             | Filter by event type (e.g. `"New Device"`).      |
| `dateFrom`  | String             | Start of date range filter on `eveDateTime`.     |
| `dateTo`    | String             | End of date range filter on `eveDateTime`.       |

### Response Fields

| Field     | Type         | Description                                                  |
| --------- | ------------ | ------------------------------------------------------------ |
| `dbCount` | Int          | Total rows in the Events table (before any filters).         |
| `count`   | Int          | Total rows after all filters (before pagination).            |
| `entries` | [EventEntry] | Paginated list of event entries.                             |

### `curl` Example

```sh
curl 'http://host:GRAPHQL_PORT/graphql' \
  -X POST \
  -H 'Authorization: Bearer API_TOKEN' \
  -H 'Content-Type: application/json' \
  --data '{
    "query": "query GetEvents($options: EventQueryOptionsInput) { events(options: $options) { dbCount count entries { eveMac eveIp eveDateTime eveEventType } } }",
    "variables": {
      "options": {
        "eveMac": "00:11:22:33:44:55",
        "page": 1,
        "limit": 50
      }
    }
  }'
```

---

## Notes

* Device, settings, LangStrings, plugin, and event queries can be combined in **one request** since GraphQL supports batching.
* The `fallback_to_en` feature ensures UI always has a value even if a translation is missing.
* Data is **cached in memory** per JSON file; changes to language or plugin files will only refresh after the cache detects a file modification.
* The `setOverriddenByEnv` flag helps identify setting values that are locked at container runtime.
* Plugin queries scope `dbCount` to the requested `plugin`/`foreignKey` so badge counts reflect per-plugin totals.
* The schema is **read-only** — updates must be performed through other APIs or configuration management. See the other [API](API.md) endpoints for details.

---

## Device History Queries

Device field change history is stored in `DevicesHistory` and exposed via two queries. History tracking is controlled by `DEV_HIST_DAYS` (retention window) and `DEV_HIST_TRACKED` (list of audited columns). Set `DEV_HIST_DAYS = 0` to disable tracking entirely.

### `deviceHistoryGrouped` — Single Device

Returns grouped change events for one device. Events are grouped by `(timestamp, changedBy)` so that simultaneous field changes are returned as a single object.

```graphql
query DeviceHistory($devGUID: String!, $changedColumn: String, $changedBy: String, $limit: Int, $offset: Int) {
  deviceHistoryGrouped(
    devGUID: $devGUID
    changedColumn: $changedColumn
    changedBy: $changedBy
    limit: $limit
    offset: $offset
  ) {
    count
    history {
      devGUID
      timestamp
      changedBy
      changes {
        changedColumn
        oldValue
        newValue
      }
    }
  }
}
```

#### Parameters

| Parameter       | Type     | Required | Description                                                          |
|-----------------|----------|----------|----------------------------------------------------------------------|
| `devGUID`       | `String` | No       | GUID of the device to fetch history for                              |
| `changedColumn` | `String` | No       | Filter to groups containing a change to this specific column         |
| `changedBy`     | `String` | No       | Filter to a specific attribution source (`USER`, `ARPSCAN`, etc.)    |
| `limit`         | `Int`    | No       | Max grouped events to return (default `50`)                          |
| `offset`        | `Int`    | No       | Grouped-event offset for pagination (default `0`)                    |

#### Response fields

| Field                      | Description                                                                 |
|----------------------------|-----------------------------------------------------------------------------|
| `count`                    | Total number of grouped events matching the filters (use for pagination)    |
| `history[].devGUID`        | Device GUID                                                                 |
| `history[].timestamp`      | UTC timestamp of the change event                                           |
| `history[].changedBy`      | Attribution: `USER`, plugin prefix (e.g. `ARPSCAN`), or `system`            |
| `history[].changes[].changedColumn` | Column name that changed                                           |
| `history[].changes[].oldValue`      | Value before the change (`null` for new devices)                   |
| `history[].changes[].newValue`      | Value after the change                                              |

#### `curl` Example

```sh
curl -X POST http://localhost:20212/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -d '{
    "query": "query($devGUID:String!,$limit:Int,$offset:Int){deviceHistoryGrouped(devGUID:$devGUID,limit:$limit,offset:$offset){count history{timestamp changedBy changes{changedColumn oldValue newValue}}}}",
    "variables": {
      "devGUID": "your-device-guid-here",
      "limit": 25,
      "offset": 0
    }
  }'
```

---



---

### Filter Values Endpoint

To populate dynamic filter dropdowns, fetch available `changedBy` and `changedColumn` values via the REST endpoint:

```sh
GET /devices/history/filters?devGUID=<guid>   # scoped to one device
GET /devices/history/filters                   # all devices
```

Response:
```json
{
  "success": true,
  "data": {
    "changedBy": ["ARPSCAN", "USER", "VNDRPDT", "system"],
    "changedColumn": ["devLastIP", "devName", "devNameSource", "devVendor"]
  }
}
```

