# Logs API Endpoints

Manage or purge application log files stored under `/app/log` and manage the execution queue. These endpoints are primarily used for maintenance tasks such as clearing accumulated logs or adding system actions without restarting the container.

Only specific, pre-approved log files can be purged for security and stability reasons.

---

## Delete (Purge) a Log File

* **DELETE** `/logs?file=<log_file>` → Purge the contents of an allowed log file.

**Query Parameter:**

* `file` → The name of the log file to purge (e.g., `app.log`, `stdout.log`)

**Allowed Files:**

```
app.log
app_front.log
IP_changes.log
stdout.log
stderr.log
app.php_errors.log
execution_queue.log
db_is_locked.log
```

**Authorization:**
Requires a valid API token in the `Authorization` header.

---

### `curl` Example (Success)

```sh
curl -X DELETE 'http://<server_ip>:<GRAPHQL_PORT>/logs?file=app.log' \
  -H 'Authorization: Bearer <API_TOKEN>' \
  -H 'Accept: application/json'
```

**Response:**

```json
{
  "success": true,
  "message": "[clean_log] File app.log purged successfully"
}
```

---

### `curl` Example (Not Allowed)

```sh
curl -X DELETE 'http://<server_ip>:<GRAPHQL_PORT>/logs?file=not_allowed.log' \
  -H 'Authorization: Bearer <API_TOKEN>' \
  -H 'Accept: application/json'
```

**Response:**

```json
{
  "success": false,
  "message": "[clean_log] File not_allowed.log is not allowed to be purged"
}
```

---

### `curl` Example (Unauthorized)

```sh
curl -X DELETE 'http://<server_ip>:<GRAPHQL_PORT>/logs?file=app.log' \
  -H 'Accept: application/json'
```

**Response:**

```json
{
  "error": "Forbidden"
}
```

---

## Add an Action to the Execution Queue

* **POST** `/logs/add-to-execution-queue` → Add a system action to the execution queue.

**Request Body (JSON):**

```json
{
  "action": "update_api|devices"
}
```

**Authorization:**
Requires a valid API token in the `Authorization` header.

---

### `curl` Example (Success)

The below will update the API cache for Devices

```sh
curl -X POST 'http://<server_ip>:<GRAPHQL_PORT>/logs/add-to-execution-queue' \
  -H 'Authorization: Bearer <API_TOKEN>' \
  -H 'Content-Type: application/json' \
  --data '{"action": "update_api|devices"}'
```

**Response:**

```json
{
  "success": true,
  "message": "[UserEventsQueueInstance] Action \"update_api|devices\" added to the execution queue."
}
```

---

### `curl` Example (Missing Parameter)

```sh
curl -X POST 'http://<server_ip>:<GRAPHQL_PORT>/logs/add-to-execution-queue' \
  -H 'Authorization: Bearer <API_TOKEN>' \
  -H 'Content-Type: application/json' \
  --data '{}'
```

**Response:**

```json
{
  "success": false,
  "message": "Missing parameters",
  "error": "Missing required 'action' field in JSON body"
}
```

---

### `curl` Example (Unauthorized)

```sh
curl -X POST 'http://<server_ip>:<GRAPHQL_PORT>/logs/add-to-execution-queue' \
  -H 'Content-Type: application/json' \
  --data '{"action": "update_api|devices"}'
```

**Response:**

```json
{
  "error": "Forbidden"
}
```

---

## Notes

* Only predefined files in `/app/log` can be purged — arbitrary paths are **not permitted**.
* When a log file is purged:

  * Its content is replaced with a short marker text: `"File manually purged"`.
  * A backend log entry is created via `mylog()`.
  * A frontend notification is generated via `write_notification()`.
* Execution queue actions are appended to `execution_queue.log` and can be processed asynchronously by background tasks or workflows.
* Unauthorized or invalid attempts are safely logged and rejected.
* For advanced log retrieval, analysis, or structured querying, use the frontend log viewer.
* Always ensure that sensitive or production logs are handled carefully — purging cannot be undone.
