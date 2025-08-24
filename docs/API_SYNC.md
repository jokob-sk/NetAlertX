# Sync API Endpoint 

---

The `/sync` endpoint is used by the **SYNC plugin** to synchronize data between multiple NetAlertX instances (e.g., from a node to a hub). It supports both **GET** and **POST** requests.

#### 9.1 GET `/sync`

Fetches data from a node to the hub. The data is returned as a **base64-encoded JSON file**.

**Example Request:**

```sh
curl 'http://<server>:<GRAPHQL_PORT>/sync' \
  -H 'Authorization: Bearer <API_TOKEN>'
```

**Response Example:**

```json
{
  "node_name": "NODE-01",
  "status": 200,
  "message": "OK",
  "data_base64": "eyJkZXZpY2VzIjogW3siZGV2TWFjIjogIjAwOjExOjIyOjMzOjQ0OjU1IiwiZGV2TmFtZSI6ICJEZXZpY2UgMSJ9XSwgImNvdW50Ijog1fQ==",
  "timestamp": "2025-08-24T10:15:00+10:00"
}
```

**Notes:**

* `data_base64` contains the full JSON data encoded in Base64.
* `node_name` corresponds to the `SYNC_node_name` setting on the node.
* Errors (e.g., missing file) return HTTP 500 with an error message.

---

#### 9.2 POST `/sync`

Used by a node to send data to the hub. The hub receives **form-encoded data** and stores it for processing.

**Required Form Fields:**

| Field       | Description                         |
| ----------- | ----------------------------------- |
| `data`      | The payload (plain text or JSON)    |
| `node_name` | Name of the node sending the data   |
| `plugin`    | The plugin name generating the data |

**Example Request (cURL):**

```sh
curl -X POST 'http://<server>:<GRAPHQL_PORT>/sync' \
  -H 'Authorization: Bearer <API_TOKEN>' \
  -F 'data=<payload here>' \
  -F 'node_name=NODE-01' \
  -F 'plugin=SYNC'
```

**Response Example:**

```json
{
  "message": "Data received and stored successfully"
}
```

**Storage Details:**

* Data is stored under `INSTALL_PATH/log/plugins` with filenames following the pattern:

```
last_result.<plugin>.encoded.<node_name>.<sequence>.log
```

* Both encoded and decoded files are tracked, and new submissions increment the sequence number.
* If storing fails, the API returns HTTP 500 with an error message.

---

#### 9.3 Notes and Best Practices

* **Authorization Required** – Both GET and POST require a valid API token.
* **Data Integrity** – Ensure that `node_name` and `plugin` are consistent to avoid overwriting files.
* **Monitoring** – Notifications are generated whenever data is sent or received (`write_notification`), which can be used for alerting or auditing.
* **Use Case** – Typically used in multi-node deployments to consolidate device and event data on a central hub.

