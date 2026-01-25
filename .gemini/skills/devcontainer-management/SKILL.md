---
name: devcontainer-management
description: Guide for identifying, managing, and running commands within the NetAlertX development container. Use this when asked to run backend logic, setup scripts, or troubleshoot container issues.
---

# Devcontainer Management

When starting a session or performing tasks requiring the runtime environment, you must identify and use the active development container.

## Finding the Container

Run `docker ps` to list running containers. Look for an image name containing `vsc-netalertx` or similar.

```bash
docker ps --format "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Names}}" | grep netalertx
```

- **If no container is found:** Inform the user. You cannot run integration tests or backend logic without it.
- **If multiple containers are found:** Ask the user to clarify which one to use (e.g., provide the Container ID).

## Running Commands in the Container

Prefix commands with `docker exec <CONTAINER_ID>` to run them inside the environment. Use the scripts in `/services/` to control backend and other processes.

```bash
docker exec <CONTAINER_ID> bash /workspaces/NetAlertX/.devcontainer/scripts/setup.sh
```

*Note: This script wipes `/tmp` ramdisks, resets DBs, and restarts services (python server, cron,php-fpm, nginx).*

```
