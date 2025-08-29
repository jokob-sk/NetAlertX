# Database Query API

The **Database Query API** provides direct, low-level access to the NetAlertX database. It allows **read, write, update, and delete** operations against tables, using **base64-encoded** SQL or structured parameters.

> [!Warning] 
> This API is primarily used internally to generate and render the application UI. These endpoints are low-level and powerful, and should be used with caution. Wherever possible, prefer the [standard API endpoints](API.md). Invalid or unsafe queries can corrupt data.
> If you need data in a specific format that is not already provided, please open an issue or pull request with a clear, broadly useful use case. This helps ensure new endpoints benefit the wider community rather than relying on raw database queries.

---

## Authentication

All `/dbquery/*` endpoints require an API token in the HTTP headers:

```http
Authorization: Bearer <API_TOKEN>
```

If the token is missing or invalid:

```json
{ "error": "Forbidden" }
```

---

## Endpoints

### 1. `POST /dbquery/read`

Execute a **read-only** SQL query (e.g., `SELECT`).

#### Request Body

```json
{
  "rawSql": "U0VMRUNUICogRlJPTSBERVZJQ0VT"   // base64 encoded SQL
}
```

Decoded SQL:

```sql
SELECT * FROM Devices;
```

#### Response

```json
{
  "success": true,
  "results": [
    { "devMac": "AA:BB:CC:DD:EE:FF", "devName": "Phone" }
  ]
}
```

---

### 2. `POST /dbquery/update` (safer than `/dbquery/write`)

Update rows in a table by `columnName` + `id`. `/dbquery/update` is parameterized to reduce the risk of SQL injection, while `/dbquery/write` executes raw SQL directly.

#### Request Body

```json
{
  "columnName": "devMac",
  "id": ["AA:BB:CC:DD:EE:FF"],
  "dbtable": "Devices",
  "columns": ["devName", "devOwner"],
  "values": ["Laptop", "Alice"]
}
```

#### Response

```json
{ "success": true, "updated_count": 1 }
```

---

### 3. `POST /dbquery/write`

Execute a **write query** (`INSERT`, `UPDATE`, `DELETE`).

#### Request Body

```json
{
  "rawSql": "SU5TRVJUIElOVE8gRGV2aWNlcyAoZGV2TWFjLCBkZXYgTmFtZSwgZGV2Rmlyc3RDb25uZWN0aW9uLCBkZXZMYXN0Q29ubmVjdGlvbiwgZGV2TGFzdElQKSBWQUxVRVMgKCc2QTpCQjo0Qzo1RDo2RTonLCAnVGVzdERldmljZScsICcyMDI1LTA4LTMwIDEyOjAwOjAwJywgJzIwMjUtMDgtMzAgMTI6MDA6MDAnLCAnMTAuMC4wLjEwJyk="
}

```

Decoded SQL:

```sql
INSERT INTO Devices (devMac, devName, devFirstConnection, devLastConnection, devLastIP)
VALUES ('6A:BB:4C:5D:6E', 'TestDevice', '2025-08-30 12:00:00', '2025-08-30 12:00:00', '10.0.0.10');

```

#### Response

```json
{ "success": true, "affected_rows": 1 }
```


---

### 4. `POST /dbquery/delete`

Delete rows in a table by `columnName` + `id`.

#### Request Body

```json
{
  "columnName": "devMac",
  "id": ["AA:BB:CC:DD:EE:FF"],
  "dbtable": "Devices"
}
```

#### Response

```json
{ "success": true, "deleted_count": 1 }
```

---

## Notes & Best Practices

* All queries must be **base64 encoded** when passed as `rawSql`.
* `update` and `delete` endpoints use **structured parameters** to prevent SQL injection.
* Avoid large or complex queries in `read` — paginate results instead.
* Always validate queries in a safe environment before running them via API.
