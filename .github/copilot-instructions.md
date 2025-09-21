This is NetAlertX — network monitoring & alerting.

Purpose: Guide AI assistants to follow NetAlertX architecture, conventions, and safety practices. Be concise, opinionated, and prefer existing helpers/settings over new code or hardcoded values.

## Architecture (what runs where)
- Backend (Python): main loop + GraphQL/REST endpoints orchestrate scans, plugins, workflows, notifications, and JSON export.
	- Key: `server/__main__.py`, `server/plugin.py`, `server/initialise.py`, `server/api_server/api_server_start.py`
- Data (SQLite): persistent state in `db/app.db`; helpers in `server/database.py` and `server/db/*`.
- Frontend (Nginx + PHP + JS): UI reads JSON, triggers execution queue events.
	- Key: `front/`, `front/js/common.js`, `front/php/server/*.php`
- Plugins (Python): acquisition/enrichment/publishers under `front/plugins/*` with `config.json` manifests.
- Messaging/Workflows: `server/messaging/*`, `server/workflows/*`
- API JSON Cache for UI: generated under `api/*.json`

Backend loop phases (see `server/__main__.py` and `server/plugin.py`): `once`, `schedule`, `always_after_scan`, `before_name_updates`, `on_new_device`, `on_notification`, plus ad‑hoc `run` via execution queue. Plugins execute as scripts that write result logs for ingestion.

## Plugin patterns that matter
- Manifest lives at `front/plugins/<code_name>/config.json`; `code_name` == folder, `unique_prefix` drives settings and filenames (e.g., `ARPSCAN`).
- Control via settings: `<PREF>_RUN` (phase), `<PREF>_RUN_SCHD` (cron-like), `<PREF>_CMD` (script path), `<PREF>_RUN_TIMEOUT`, `<PREF>_WATCH` (diff columns).
- Data contract: scripts write `/app/log/plugins/last_result.<PREF>.log` (pipe‑delimited: 9 required cols + optional 4). Use `front/plugins/plugin_helper.py`’s `Plugin_Objects` to sanitize text and normalize MACs, then `write_result_file()`.
- Device import: define `database_column_definitions` when creating/updating devices; watched fields trigger notifications.

## API/Endpoints quick map
- Flask app: `server/api_server/api_server_start.py` exposes routes like `/device/<mac>`, `/devices`, `/devices/export/{csv,json}`, `/devices/import`, `/devices/totals`, `/devices/by-status`, plus `nettools`, `events`, `sessions`, `dbquery`, `metrics`, `sync`.
- Authorization: all routes expect header `Authorization: Bearer <API_TOKEN>` via `get_setting_value('API_TOKEN')`.

## Conventions & helpers to reuse
- Settings: add/modify via `ccd()` in `server/initialise.py` or per‑plugin manifest. Never hardcode ports or secrets; use `get_setting_value()`.
- Logging: use `logger.mylog(level, [message])`; levels: none/minimal/verbose/debug/trace.
- Time/MAC/strings: `helper.py` (`timeNowTZ`, `normalize_mac`, sanitizers). Validate MACs before DB writes.
- DB helpers: prefer `server/db/db_helper.py` functions (e.g., `get_table_json`, device condition helpers) over raw SQL in new paths.

## Dev workflow (devcontainer)
- Services: use tasks to (re)start backend and nginx/PHP-FPM. Backend runs with debugpy on 5678; attach a Python debugger if needed.
- Run a plugin manually: `python3 front/plugins/<code_name>/script.py` (ensure `sys.path` includes `/app/front/plugins` and `/app/server` like the template).
- Testing: pytest available via Alpine packages. Tests live in `test/`; app code is under `server/`. PYTHONPATH is preconfigured to include workspace and `/opt/venv` site‑packages.

## What “done right” looks like
- When adding a plugin, start from `front/plugins/__template`, implement with `plugin_helper`, define manifest settings, and wire phase via `<PREF>_RUN`. Verify logs in `/app/log/plugins/` and data in `api/*.json`.
- When introducing new config, define it once (core `ccd()` or plugin manifest) and read it via helpers everywhere.
- When exposing new server functionality, add endpoints in `server/api_server/*` and keep authorization consistent; update UI by reading/writing JSON cache rather than bypassing the pipeline.

## Useful references
- Docs: `docs/PLUGINS_DEV.md`, `docs/SETTINGS_SYSTEM.md`, `docs/API_*.md`, `docs/DEBUG_*.md`
- Logs: backend `/app/log/app.log`, plugin logs under `/app/log/plugins/`, nginx/php logs under `/var/log/*`

Assistant expectations
- Reference concrete files/paths. Use existing helpers/settings. Keep changes idempotent and safe. Offer a quick validation step (log line, API hit, or JSON export) for anything you add.