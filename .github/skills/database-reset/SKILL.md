---
name: reset-netalertx-database
description: Wipe and regenerate the NetAlertX database and config. Use this when asked to reset database, wipe db, fresh database, clean slate, or start fresh.
---

# Database Reset

Completely wipes devcontainer database and config, then regenerates from scratch.

## Command

```bash
killall 'python3' || true
sleep 1
rm -rf /data/db/* /data/config/*
bash /entrypoint.d/15-first-run-config.sh
bash /entrypoint.d/20-first-run-db.sh
```

## What This Does

1. Kills backend to release database locks
2. Deletes all files in `/data/db/` and `/data/config/`
3. Runs first-run config provisioning
4. Runs first-run database initialization

## After Reset

Run the startup script to restart services:

```bash
/workspaces/NetAlertX/.devcontainer/scripts/setup.sh
```

## Database Location

- Runtime: `/data/db/app.db` (SQLite)
- Config: `/data/config/app.conf`
