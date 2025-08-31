# Settings API Endpoints

Retrieve application settings stored in the configuration system. This endpoint is useful for quickly fetching individual settings such as `API_TOKEN` or `TIMEZONE`.

For bulk or structured access (all settings, schema details, or filtering), use the [GraphQL API Endpoint](API_GRAPHQL.md).

---

### Get a Setting

* **GET** `/settings/<key>` → Retrieve the value of a specific setting

**Path Parameter:**

* `key` → The setting key to retrieve (e.g., `API_TOKEN`, `TIMEZONE`)

**Authorization:**
Requires a valid API token in the `Authorization` header.

---

#### `curl` Example (Success)

```sh
curl 'http://<server_ip>:<GRAPHQL_PORT>/settings/API_TOKEN' \
  -H 'Authorization: Bearer <API_TOKEN>' \
  -H 'Accept: application/json'
```

**Response:**

```json
{
  "success": true,
  "value": "my-secret-token"
}
```

---

#### `curl` Example (Invalid Key)

```sh
curl 'http://<server_ip>:<GRAPHQL_PORT>/settings/DOES_NOT_EXIST' \
  -H 'Authorization: Bearer <API_TOKEN>' \
  -H 'Accept: application/json'
```

**Response:**

```json
{
  "success": true,
  "value": null
}
```

---

#### `curl` Example (Unauthorized)

```sh
curl 'http://<server_ip>:<GRAPHQL_PORT>/settings/API_TOKEN' \
  -H 'Accept: application/json'
```

**Response:**

```json
{
  "error": "Forbidden"
}
```

---

### Notes

* This endpoint is optimized for **direct retrieval of a single setting**.
* For **complex retrieval scenarios** (listing all settings, retrieving schema metadata like `setName`, `setDescription`, `setType`, or checking if a setting is overridden by environment variables), use the **GraphQL Settings Query**:

```sh
curl 'http://<server_ip>:<GRAPHQL_PORT>/graphql' \
  -X POST \
  -H 'Authorization: Bearer <API_TOKEN>' \
  -H 'Content-Type: application/json' \
  --data '{
    "query": "query GetSettings { settings { settings { setKey setName setDescription setType setOptions setGroup setValue setEvents setOverriddenByEnv } count } }"
  }'
```

See the [GraphQL API Endpoint](API_GRAPHQL.md) for more details.
