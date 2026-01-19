# Gemini-CLI Agent Instructions for NetAlertX

## 1. Environment & Devcontainer

When starting a session, always identify the active development container.

### Finding the Container
Run `docker ps` to list running containers. Look for an image name containing `vsc-netalertx` or similar.

```bash
docker ps --format "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Names}}" | grep netalertx
```

- **If no container is found:** Inform the user. You cannot run integration tests or backend logic without it.
- **If multiple containers are found:** Ask the user to clarify which one to use (e.g., provide the Container ID).

### Running Commands in the Container
Prefix commands with `docker exec <CONTAINER_ID>` to run them inside the environment. Use the scripts in `/services/` to control backend and other processes.
```bash
docker exec <CONTAINER_ID> bash /workspaces/NetAlertX/.devcontainer/scripts/setup.sh
```
*Note: This script wipes `/tmp` ramdisks, resets DBs, and restarts services (python server, cron,php-fpm, nginx).* 

## 2. Codebase Structure & Key Paths

- **Source Code:** `/workspaces/NetAlertX` (mapped to `/app` in container via symlink).
- **Backend Entry:** `server/api_server/api_server_start.py` (Flask) and `server/__main__.py`.
- **Frontend:** `front/` (PHP/JS).
- **Plugins:** `front/plugins/`.
- **Config:** `/data/config/app.conf` (runtime) or `back/app.conf` (default).
- **Database:** `/data/db/app.db` (SQLite).

## 3. Testing Workflow

**Crucial:** Tests MUST be run inside the container to access the correct runtime environment (DB, Config, Dependencies).

### Running Tests
Use `pytest` with the correct PYTHONPATH.

```bash
docker exec <CONTAINER_ID> bash -c "cd /workspaces/NetAlertX && pytest <test_file>"
```

*Example:*
```bash
docker exec <CONTAINER_ID> bash -c "cd /workspaces/NetAlertX && pytest test/api_endpoints/test_mcp_extended_endpoints.py"
```

### Authentication in Tests
The test environment uses `API_TOKEN`. The most reliable way to retrieve the current token from a running container is:
```bash
docker exec <CONTAINER_ID> python3 -c "from helper import get_setting_value; print(get_setting_value('API_TOKEN'))"
```

*Troubleshooting:* If tests fail with 403 Forbidden or empty tokens:
1. Verify server is running and use the aforementioned setup.sh if required.
2. Verify `app.conf` inside the container: `docker exec <ID> cat /data/config/app.conf`
23 Verify Python can read it: `docker exec <ID> python3 -c "from helper import get_setting_value; print(get_setting_value('API_TOKEN'))"`

