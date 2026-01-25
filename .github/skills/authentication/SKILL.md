---
name: netalertx-authentication-tokens
description: Manage and troubleshoot API tokens and authentication-related secrets. Use this when you need to find, rotate, verify, or debug authentication issues (401/403) in NetAlertX.
---

# Authentication

## Purpose ✅
Explain how to locate, validate, rotate, and troubleshoot API tokens and related authentication settings used by NetAlertX.

## Pre-Flight Check (MANDATORY) ⚠️
1. Ensure the backend is running (use devcontainer services or `ps`/systemd checks).
2. Verify the `API_TOKEN` setting can be read with Python (see below).
3. If a token-related error occurs, gather logs (`/tmp/log/app.log`, nginx logs) before changing secrets.

## Retrieve the API token (Python — preferred) 🐍
Always use Python helpers to read secrets to avoid accidental exposure in shells or logs:

```python
from helper import get_setting_value
token = get_setting_value("API_TOKEN")
```

If you must inspect from a running container (read-only), use:

```bash
docker exec <CONTAINER_ID> python3 -c "from helper import get_setting_value; print(get_setting_value('API_TOKEN'))"
```

You can also check the runtime config file:

```bash
docker exec <CONTAINER_ID> grep API_TOKEN /data/config/app.conf
```

## Rotate / Generate a new token 🔁
- Preferred: Use the web UI (Settings / System) and click **Generate** for the `API_TOKEN` field — this updates the value safely and immediately.
- Manual: Edit `/data/config/app.conf` and restart the backend if required (use the existing devcontainer service tasks).
- After rotation: verify the value with `get_setting_value('API_TOKEN')` and update any clients or sync nodes to use the new token.

## Troubleshooting 401 / 403 Errors 🔍
1. Confirm backend is running and reachable.
2. Confirm `get_setting_value('API_TOKEN')` returns a non-empty value.
3. Ensure client requests send the header exactly: `Authorization: Bearer <API_TOKEN>`.
4. Check `/tmp/log/app.log` and plugin logs (e.g., sync plugin) for "Incorrect API Token" messages.
5. If using multiple nodes, ensure the token matches across nodes for sync operations.
6. If token appears missing or incorrect, rotate via UI or update `app.conf` and re-verify.

## Best Practices & Security 🔐
- Never commit tokens to source control or paste them in public issues. Redact tokens when sharing logs.
- Rotate tokens when a secret leak is suspected or per your security policy.
- Use `get_setting_value()` in tests and scripts — do not hardcode secrets.

## Related Skills & Docs 📚
- `testing-workflow` — how to use `API_TOKEN` in tests
- `settings-management` — where settings live and how they are managed
- Docs: `docs/API.md`, `docs/API_OLD.md`, `docs/API_SSE.md`

---
_Last updated: 2026-01-23_
