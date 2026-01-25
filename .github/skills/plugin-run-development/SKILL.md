---
name: netalertx-plugin-run-development
description: Create and run NetAlertX plugins. Use this when asked to create plugin, run plugin, test plugin, plugin development, or execute plugin script.
---

# Plugin Development

## Expected Workflow for Running Plugins

1. Read this skill document for context and instructions.
2. Find the plugin in `front/plugins/<code_name>/`.
3. Read the plugin's `config.json` and `script.py` to understand its functionality and settings.
4. Formulate and run the command: `python3 front/plugins/<code_name>/script.py`.
5. Retrieve the result from the plugin log folder (`/tmp/log/plugins/last_result.<PREF>.log`) quickly, as the backend may delete it after processing.

## Run a Plugin Manually

```bash
python3 front/plugins/<code_name>/script.py
```

Ensure `sys.path` includes `/app/front/plugins` and `/app/server` (as in the template).

## Plugin Structure

```text
front/plugins/<code_name>/
├── config.json      # Manifest with settings
├── script.py        # Main script
└── ...
```

## Manifest Location

`front/plugins/<code_name>/config.json`

- `code_name` == folder name
- `unique_prefix` drives settings and filenames (e.g., `ARPSCAN`)

## Settings Pattern

- `<PREF>_RUN`: execution phase
- `<PREF>_RUN_SCHD`: cron-like schedule
- `<PREF>_CMD`: script path
- `<PREF>_RUN_TIMEOUT`: timeout in seconds
- `<PREF>_WATCH`: columns to watch for changes

## Data Contract

Scripts write to `/tmp/log/plugins/last_result.<PREF>.log`

**Important:** The backend will almost immediately process this result file and delete it after ingestion. If you need to inspect the output, run the plugin and immediately retrieve the result file before the backend processes it.

Use `front/plugins/plugin_helper.py`:

```python
from plugin_helper import Plugin_Objects

plugin_objects = Plugin_Objects()
plugin_objects.add_object(...)  # During processing
plugin_objects.write_result_file()  # Exactly once at end
```

## Execution Phases

- `once`: runs once at startup
- `schedule`: runs on cron schedule
- `always_after_scan`: runs after every scan
- `before_name_updates`: runs before name resolution
- `on_new_device`: runs when new device detected
- `on_notification`: runs when notification triggered

## Plugin Formats

| Format | Purpose | Runs |
|--------|---------|------|
| publisher | Send notifications | `on_notification` |
| dev scanner | Create/manage devices | `schedule` |
| name discovery | Discover device names | `before_name_updates` |
| importer | Import from services | `schedule` |
| system | Core functionality | `schedule` |

## Starting Point

Copy from `front/plugins/__template` and customize.
