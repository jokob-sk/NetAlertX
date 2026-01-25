---
name: netalertx-sample-data
description: Load synthetic device data into the devcontainer. Use this when asked to load sample devices, seed data, import test devices, populate database, or generate test data.
---

# Sample Data Loading

Generates synthetic device inventory and imports it via the `/devices/import` API endpoint.

## Command

```bash
cd /workspaces/NetAlertX/.devcontainer/scripts
./load-devices.sh
```

## Environment

- `CSV_PATH`: defaults to `/tmp/netalertx-devices.csv`

## Prerequisites

- Backend must be running
- API must be accessible

## What It Does

1. Generates synthetic device records (MAC addresses, IPs, names, vendors)
2. Creates CSV file at `$CSV_PATH`
3. POSTs to `/devices/import` endpoint
4. Devices appear in database and UI
