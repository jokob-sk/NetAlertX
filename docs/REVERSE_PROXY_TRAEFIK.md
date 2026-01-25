# Guide: Routing NetAlertX API via Traefik v3

> [!NOTE]
> NetAlertX requires access to both the **web UI**  (default `20211`) and the **GraphQL backend `GRAPHQL_PORT`** (default `20212`) ports.
> Ensure your reverse proxy allows traffic to both for proper functionality.


> [!NOTE]
> This is community-contributed. Due to environment, setup, or networking differences, results may vary. Please open a PR to improve it instead of creating an issue, as the maintainer is not actively maintaining it.


Traefik v3 requires the following setup to route traffic properly. This guide shows a working configuration using a dedicated `PathPrefix`.

---

## 1. Configure NetAlertX Backend URL

1. Open the NetAlertX UI: **Settings → Core → General**.
2. Set the `BACKEND_API_URL` to include a custom path prefix, for example:

```
https://netalertx.yourdomain.com/netalertx-api
```

This tells the frontend where to reach the backend API.

---

## 2. Create a Traefik Router for the API

Define a router specifically for the API with a higher priority and a `PathPrefix` rule:

```yaml
netalertx-api:
  rule: "Host(`netalertx.yourdomain.com`) && PathPrefix(`/netalertx-api`)"
  service: netalertx-api-service
  middlewares:
    - netalertx-stripprefix
  priority: 100
```

**Notes:**

* `Host(...)` ensures requests are only routed for your domain.
* `PathPrefix(...)` routes anything under `/netalertx-api` to the backend.
* Priority `100` ensures this router takes precedence over other routes.

---

## 3. Add a Middleware to Strip the Prefix

NetAlertX expects requests at the root (`/`). Use Traefik’s `StripPrefix` middleware:

```yaml
middlewares:
  netalertx-stripprefix:
    stripPrefix:
      prefixes:
        - "/netalertx-api"
```

This removes `/netalertx-api` before forwarding the request to the backend container.

---

## 4. Map the API Service to the Backend Container

Point the service to the internal GraphQL/Backend port (20212):

```yaml
netalertx-api-service:
  loadBalancer:
    servers:
      - url: "http://<INTERNAL_IP>:20212"
```

Replace `<INTERNAL_IP>` with your NetAlertX container’s internal address.

---

✅ With this setup:

* `https://netalertx.yourdomain.com` → Web interface (port 20211)
* `https://netalertx.yourdomain.com/netalertx-api` → API/GraphQL backend (port 20212)

This cleanly separates API requests from frontend requests while keeping everything under the same domain.
