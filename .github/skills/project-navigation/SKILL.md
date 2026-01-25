---
name: about-netalertx-project-structure
description: Navigate the NetAlertX codebase structure. Use this when asked about file locations, project structure, where to find code, or key paths.
---

# Project Navigation

## Key Paths

| Component | Path |
|-----------|------|
| Workspace root | `/workspaces/NetAlertX` |
| Backend entry | `server/__main__.py` |
| API server | `server/api_server/api_server_start.py` |
| Plugin system | `server/plugin.py` |
| Initialization | `server/initialise.py` |
| Frontend | `front/` |
| Frontend JS | `front/js/common.js` |
| Frontend PHP | `front/php/server/*.php` |
| Plugins | `front/plugins/` |
| Plugin template | `front/plugins/__template` |
| Database helpers | `server/db/db_helper.py` |
| Device model | `server/models/device_instance.py` |
| Messaging | `server/messaging/` |
| Workflows | `server/workflows/` |

## Architecture

NetAlertX uses a frontend–backend architecture: the frontend runs on **PHP + Nginx** (see `front/`), the backend is implemented in **Python** (see `server/`), and scheduled tasks are managed by a **supercronic** scheduler that runs periodic jobs.

## Runtime Paths

| Data | Path |
|------|------|
| Config (runtime) | `/data/config/app.conf` |
| Config (default) | `back/app.conf` |
| Database | `/data/db/app.db` |
| API JSON cache | `/tmp/api/*.json` |
| Logs | `/tmp/log/` |
| Plugin logs | `/tmp/log/plugins/` |

## Environment Variables

Use these NETALERTX_* instead of hardcoding paths. Examples:

- `NETALERTX_DB`
- `NETALERTX_LOG`
- `NETALERTX_CONFIG`
- `NETALERTX_DATA`
- `NETALERTX_APP`

## Documentation

| Topic | Path |
|-------|------|
| Plugin development | `docs/PLUGINS_DEV.md` |
| System settings | `docs/SETTINGS_SYSTEM.md` |
| API docs | `docs/API_*.md` |
| Debug guides | `docs/DEBUG_*.md` |
