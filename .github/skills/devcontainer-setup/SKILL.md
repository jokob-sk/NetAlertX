---
name: netalertx-idempotent—setup
description: Reprovision and reset the devcontainer environment. Use this when asked to re-run startup, reprovision, setup devcontainer, fix permissions, or reset runtime state.
---

# Devcontainer Setup

The setup script forcefully resets all runtime state. It is idempotent—every run wipes and recreates all relevant folders, symlinks, and files.

## Command

```bash
/workspaces/NetAlertX/.devcontainer/scripts/setup.sh
```

## What It Does

1. Kills all services (php-fpm, nginx, crond, python3)
2. Mounts tmpfs ramdisks for `/tmp/log`, `/tmp/api`, `/tmp/run`, `/tmp/nginx`
3. Creates critical subdirectories
4. Links `/entrypoint.d` and `/app` symlinks
5. Creates `/data`, `/data/config`, `/data/db` directories
6. Creates all log files
7. Runs `/entrypoint.sh` to start services
8. Writes version to `.VERSION`

## When to Use

- After modifying setup scripts
- After container rebuild
- When environment is in broken state
- After database reset

## Philosophy

No conditional logic. Everything is recreated unconditionally. If something doesn't work, run setup again.
