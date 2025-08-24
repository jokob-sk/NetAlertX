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

---

### Implementation Details

The endpoint calls the helper function `delete_online_history()`:

```python
def delete_online_history():
    """Delete all online history activity"""

    conn = get_temp_db_connection()
    cur = conn.cursor()

    # Remove all entries from Online_History table
    cur.execute("DELETE FROM Online_History")

    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Deleted online history"})
```

* Opens a temporary database connection for the request.
* Executes a **full table delete** (`DELETE FROM Online_History`).
* Commits the transaction and closes the connection.
* Returns a JSON confirmation message.
