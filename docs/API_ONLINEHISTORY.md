# Online History API Endpoints

Manage the **online history records** of devices. Currently, the API supports deletion of all history entries. All endpoints require **authorization**.

---

## 1. Delete Online History

* **DELETE** `/history`
  Remove **all records** from the online history table (`Online_History`). This operation **cannot be undone**.

**Response** (success):

```json
{
  "success": true,
  "message": "Deleted online history"
}
```

**Error Responses**:

* Unauthorized → HTTP 403

---

### Example `curl` Request

```bash
curl -X DELETE "http://<server_ip>:<GRAPHQL_PORT>/history" \
  -H "Authorization: Bearer <API_TOKEN>"
```