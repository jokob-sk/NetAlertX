# In-app Notifications API

Manage in-app notifications for users. Notifications can be written, retrieved, marked as read, or deleted.

---

### Write Notification

* **POST** `/messaging/in-app/write` → Create a new in-app notification.

  **Request Body:**

  ```json
  {
    "content": "This is a test notification",
    "level": "alert"   // optional, ["interrupt","info","alert"]  default: "alert"
  }
  ```

  **Response:**

  ```json
  {
    "success": true
  }
  ```

#### `curl` Example

```bash
curl -X POST "http://<server_ip>:<GRAPHQL_PORT>/messaging/in-app/write" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "This is a test notification",
    "level": "alert"
  }'
```

---

### Get Unread Notifications

* **GET** `/messaging/in-app/unread` → Retrieve all unread notifications.

  **Response:**

  ```json
  [
    {
      "timestamp": "2025-10-10T12:34:56",
      "guid": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "read": 0,
      "level": "alert",
      "content": "This is a test notification"
    }
  ]
  ```

#### `curl` Example

```bash
curl -X GET "http://<server_ip>:<GRAPHQL_PORT>/messaging/in-app/unread" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Accept: application/json"
```

---

### Mark All Notifications as Read

* **POST** `/messaging/in-app/read/all` → Mark all notifications as read.

  **Response:**

  ```json
  {
    "success": true
  }
  ```

#### `curl` Example

```bash
curl -X POST "http://<server_ip>:<GRAPHQL_PORT>/messaging/in-app/read/all" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Accept: application/json"
```

---

### Mark Single Notification as Read

* **POST** `/messaging/in-app/read/<guid>` → Mark a single notification as read using its GUID.

  **Response (success):**

  ```json
  {
    "success": true
  }
  ```

  **Response (failure):**

  ```json
  {
    "success": false,
    "error": "Notification not found"
  }
  ```

#### `curl` Example

```bash
curl -X POST "http://<server_ip>:<GRAPHQL_PORT>/messaging/in-app/read/f47ac10b-58cc-4372-a567-0e02b2c3d479" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Accept: application/json"
```

---

### Delete All Notifications

* **DELETE** `/messaging/in-app/delete` → Remove all notifications from the system.

  **Response:**

  ```json
  {
    "success": true
  }
  ```

#### `curl` Example

```bash
curl -X DELETE "http://<server_ip>:<GRAPHQL_PORT>/messaging/in-app/delete" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Accept: application/json"
```

---

### Delete Single Notification

* **DELETE** `/messaging/in-app/delete/<guid>` → Remove a single notification by its GUID.

  **Response (success):**

  ```json
  {
    "success": true
  }
  ```

  **Response (failure):**

  ```json
  {
    "success": false,
    "error": "Notification not found"
  }
  ```

#### `curl` Example

```bash
curl -X DELETE "http://<server_ip>:<GRAPHQL_PORT>/messaging/in-app/delete/f47ac10b-58cc-4372-a567-0e02b2c3d479" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Accept: application/json"
```
