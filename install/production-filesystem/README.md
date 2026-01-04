
# NetAlertX Production Container Filesystem

This document describes the filesystem structure of the NetAlertX production Docker container. This setup focuses on security by separating application code, configuration, and runtime data.

## Directory Structure

### `/app` - Main Application Directory
The core application location where NetAlertX runs. This directory contains only the application code in production. Configuration, database files, and logs now live in dedicated `/data` and `/tmp` mounts to keep the runtime read-only and auditable.

The core application location. Contains:
- Source code directories (`back`, `front`, `server`) copied in read-only mode
- Service orchestration scripts under `/services`
- No persistent data or logs—those are redirected to `/data` and `/tmp`

### `/data` - Persistent Configuration and Database
Writable volume that stores administrator-managed settings and database state. The entrypoint ensures directories are owned by the `netalertx` user (UID 20211).

Contains:
- `/data/config` - persisted settings such as `app.conf`
- `/data/db` - SQLite database files (e.g., `app.db`)
- Optional host bind mounts for backups or external sync

### `/build` - Build-Time Scripts
Temporary directory used during Docker image building to prepare the container environment. Scripts in this directory run during the build process to set up the system before it's locked down for production use. This ensures the container is properly configured before runtime.

Temporary directory used during Docker image building:
- Scripts run at the end of the build process
- Deleted after build to reduce image size
- Only exists during container creation

### `/opt/venv/lib/python3.12/site-packages/aiofreebox` - Certificate Storage
Contains SSL certificates required for secure communication with Freebox OS devices. The aiofreebox Python package uses these certificates to authenticate and establish encrypted connections when integrating with Freebox routers for network device discovery.

Contains certificates for the aiofreebox package, which communicates with Freebox OS devices.

### `/services` - Service Management
Contains all scripts and configurations for running NetAlertX services. This directory holds the complete service orchestration layer that manages the container's runtime behavior, including startup scripts, configuration files, and utility tools for system maintenance and monitoring.

Contains all scripts and configurations for running NetAlertX services:

#### `/services/config` - Service Configurations
Configuration files for each service that runs in the container. These files define how services like the web server, task scheduler, and Python backend operate, including security settings, resource limits, and integration parameters.

Configuration files for each service:
- `crond/` - Task scheduler settings
- `nginx/` - Web server configuration
- `php/` - PHP interpreter settings
  - `php-fpm.d/` - Additional PHP configurations
- `python/` - Python backend launch parameters

#### `/services/scripts` - System Scripts and Utilities
Pre-startup checks and specialized maintenance tools. Files named `check-*` are intended to verify system functions at startup and correct issues or warn users as needed. Additional scripts perform various update tasks and provide integration capabilities with external systems.

Pre-startup checks and specialized maintenance tools:
- `check-cap.sh` - Verifies container permissions for network tools
- `check-first-run-config.sh` - Sets up initial configuration
- `check-first-run-db.sh` - Prepares database on first run
- `check-permissions.sh` - Validates file and directory permissions
- `check-ramdisk.sh` - Checks temporary storage setup
- `check-root.sh` - Confirms proper user privileges
- `check-storage.sh` - Ensures storage directories exist
- `update_vendors.sh` - Updates MAC address vendor database
- `checkmk/` - Checkmk monitoring integration scripts
- `db_cleanup/` - Database maintenance and cleanup tools
- `db_empty/` - Database reset utilities
- `list-ports.sh` - Network port enumeration script
- `opnsense_leases/` - OPNsense DHCP lease integration tools

### `/tmp` - Ephemeral Runtime Data
All writable runtime data is consolidated under `/tmp`, which is mounted as `tmpfs` by default for speed and automatic cleanup on restart.

- `/tmp/log` - Application, PHP, and plugin logs (bind mount to persist between restarts)
- `/tmp/api` - Cached API responses for the UI (configurable via `NETALERTX_API` environment variable)
- `/tmp/nginx/active-config` - Optional override directory for nginx configuration
- `/tmp/run` - Runtime socket and temp directories for nginx and PHP (`client_body`, `proxy`, `php.sock`, etc.)

#### Service Control Scripts
Scripts that start and manage the core services required for NetAlertX operation. These scripts handle the initialization of the web server, application server, task scheduler, and backend processing components that work together to provide network monitoring functionality.

- `start-backend.sh` - Launches Python backend service
- `start-crond.sh` - Starts task scheduler
- `start-nginx.sh` - Starts web server
- `start-php-fpm.sh` - Starts PHP processor
- `healthcheck.sh` - Container health verification
- `cron_script.sh` - Scheduled task definitions


### `/root-entrypoint.sh` - Initial Entrypoint and Permission Priming
This script is the very first process executed in the production container (it becomes PID 1 and `/` in the Docker filesystem). Its primary role is to perform best-effort permission priming for all runtime and persistent paths, ensuring that directories like `/data`, `/tmp`, and their subpaths are owned and writable by the correct user and group (as specified by the `PUID` and `PGID` environment variables, defaulting to 20211).

Key behaviors:
- If started as root, attempts to create and chown all required paths, then drops privileges to the target user/group using `su-exec`.
- If started as non-root, skips priming and expects the operator to ensure correct host-side permissions.
- All permission operations are best-effort: failures to chown/chmod do not halt startup, but are logged for troubleshooting.
- The only fatal condition is a malformed (non-numeric) `PUID` or `PGID` value, which is treated as a security risk and halts startup with a clear error message and troubleshooting URL.
- No artificial upper bound is enforced on UID/GID; any numeric value is accepted.
- If privilege drop fails, the script logs a warning and continues as the current user for resilience.

This design ensures that NetAlertX can run securely and portably across a wide range of host environments (including NAS appliances and hardened Docker setups), while minimizing the risk of privilege escalation or misconfiguration.

### `/entrypoint.sh` - Container Startup Script
The main orchestration script that runs after `/root-entrypoint.sh` completes. It coordinates the entire container initialization process, from pre-startup validation through service startup and ongoing monitoring, ensuring NetAlertX operates reliably in production environments.

The main script that runs when the container starts:
- Runs all pre-startup checks from `/services/scripts`
- Creates necessary directories and files
- Starts all required services (crond, PHP-FPM, nginx, Python backend)
- Monitors services and handles failures
- Ensures clean shutdown on container stop

## Boot Flow

The container startup process is designed to be robust, secure, and informative. It follows a strict sequence to ensure the environment is correctly prepared before the application starts.

1.  **`root-entrypoint.sh` (Privilege & Permission Management)**
    *   **Validation:** Verifies that `PUID` and `PGID` environment variables are numeric (security measure).
    *   **Permission Priming:** If running as root, it attempts to fix ownership of writable volumes (`/data`, `/tmp`) to match the requested `PUID`/`PGID`. This ensures the application can write to its storage even if the host volume permissions are incorrect.
    *   **Privilege Drop:** Uses `su-exec` to switch to the target user (default `netalertx:20211`) before executing the main entrypoint.
    *   **Non-Root Support:** If the container is started as a non-root user, this step is skipped, and the operator is responsible for volume permissions.

2.  **`entrypoint.sh` (Orchestration)**
    *   **Banner:** Displays the NetAlertX logo and version.
    *   **Pre-Startup Checks:** Executes all scripts in `/entrypoint.d/` to validate the environment (see below).
    *   **Configuration:** Applies environment variable overrides (e.g., `GRAPHQL_PORT`) to the application configuration.
    *   **Background Tasks:** Launches `update_vendors.sh` to update the MAC address database without blocking startup.
    *   **Service Startup:** Launches core services in order:
        *   `crond` (Scheduler) - *Alpine only*
        *   `php-fpm` (PHP Processor)
        *   `nginx` (Web Server)
        *   `python3` (NetAlertX Backend)
    *   **Monitoring Loop:** Enters a loop to monitor the health of all started services. If any service fails (and `NETALERTX_DEBUG` is not enabled), the container shuts down to allow the orchestrator (Docker/K8s) to restart it.

3.  **`entrypoint.d` (Sanity Checks & Initialization)**
    Scripts in this directory run sequentially to prepare and validate the system. Key checks include:
    *   **Data Migration:** `05-data-migration.sh` - Handles data structure updates.
    *   **Capabilities:** `10-capabilities-audit.sh` - Verifies required network capabilities (CAP_NET_RAW, etc.).
    *   **Mounts:** `15-mounts.py` - Checks for correct volume mounts.
    *   **First Run:** `20-first-run-config.sh` & `25-first-run-db.sh` - Initializes config and database if missing.
    *   **Environment:** `30-mandatory-folders.sh` - Ensures required directories exist.
    *   **Configuration:** `35-apply-conf-override.sh` & `40-writable-config.sh` - Applies config overrides and checks write permissions.
    *   **Web Server:** `45-nginx-config.sh` - Generates Nginx configuration.
    *   **User ID:** `60-expected-user-id-match.sh` - Warns if running as an unexpected UID.
    *   **Network:** `80-host-mode-network.sh` & `99-ports-available.sh` - Checks network mode and port availability.
    *   **Security:** `90-excessive-capabilities.sh` & `95-appliance-integrity.sh` - Audits for security risks.

4.  **Service Operation**
    Once all checks pass and services are started, the container is fully operational. The `entrypoint.sh` script continues to run as PID 1, handling signals (SIGINT/SIGTERM) for graceful shutdown.

## Security Considerations

- Application code is read-only to prevent modifications
- Services run with minimal required permissions
- Configurations are separated from code
- Pre-startup checks verify system integrity
- Runtime data is isolated in dedicated directories
- Container exits immediately if any service fails (enables restart policies)