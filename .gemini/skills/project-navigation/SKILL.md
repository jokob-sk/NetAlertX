---
name: project-navigation
description: Reference for the NetAlertX codebase structure, key file paths, and configuration locations. Use this when exploring the codebase or looking for specific components like the backend entry point, frontend files, or database location.
---

# Project Navigation & Structure

## Codebase Structure & Key Paths

- **Source Code:** `/workspaces/NetAlertX` (mapped to `/app` in container via symlink).
- **Backend Entry:** `server/api_server/api_server_start.py` (Flask) and `server/__main__.py`.
- **Frontend:** `front/` (PHP/JS).
- **Plugins:** `front/plugins/`.
- **Config:** `/data/config/app.conf` (runtime) or `back/app.conf` (default).
- **Database:** `/data/db/app.db` (SQLite).
