# Plugin Development Documentation Index

Complete guide to building NetAlertX plugins, split into focused, easy-to-navigate documents.

## Quick Navigation

**Just getting started?** → [Quick Start Guide](PLUGINS_DEV_QUICK_START.md)
**Need the basics?** → [Plugin Data Contract](PLUGINS_DEV_DATA_CONTRACT.md)
**Configuring plugins?** → [Plugin Settings System](PLUGINS_DEV_SETTINGS.md)
**Displaying results?** → [UI Components](PLUGINS_DEV_UI_COMPONENTS.md)
**Getting data?** → [Data Sources](PLUGINS_DEV_DATASOURCES.md)

---

## Documentation Structure

### Getting Started (Start Here!)

| Document | Purpose | Read Time |
|----------|---------|-----------|
| **[Quick Start Guide](PLUGINS_DEV_QUICK_START.md)** | Create a working plugin in 5 minutes. Copy template, edit config, implement script, test. | 5 min |
| **[Development Environment Setup](./DEV_ENV_SETUP.md)** | Set up your local development environment for plugin development. | 10 min |

### Core Concepts

| Document | Purpose | Read Time |
|----------|---------|-----------|
| **[Full Plugin Development Guide](PLUGINS_DEV.md)** | Comprehensive overview with references to all specialized guides. Architecture, file structure, manifest format. | 20 min |
| **[Plugin Data Contract](PLUGINS_DEV_DATA_CONTRACT.md)** | **THE** authoritative reference for plugin output format. 9-13 pipe-delimited columns. Examples, validation, debugging. | 15 min |
| **[Plugin Settings System](PLUGINS_DEV_SETTINGS.md)** | How to add user-configurable settings. Component types, reserved names, accessing in scripts. | 20 min |
| **[Data Sources](PLUGINS_DEV_DATASOURCES.md)** | How plugins retrieve data: scripts, database queries, external SQLite, templates. Performance considerations. | 15 min |
| **[UI Components](PLUGINS_DEV_UI_COMPONENTS.md)** | How to display plugin results: labels, links, color-coded badges, filters. Database mapping. | 25 min |

### Advanced Topics

| Document | Purpose | Read Time |
|----------|---------|-----------|
| **[Config Lifecycle](PLUGINS_DEV_CONFIG.md)** | Deep dive into how `config.json` is loaded, validated, and used throughout plugin lifecycle. | 15 min |
| **[Debugging Plugins](DEBUG_PLUGINS.md)** | Troubleshooting plugin issues: logs, validation, common errors. | 10 min |

---

## Document Overview

### [Quick Start Guide](PLUGINS_DEV_QUICK_START.md)
**For:** First-time plugin developers
**Contains:**
- 5 prerequisites
- Step-by-step: folder setup, config.json, script.py, execution settings
- Testing locally & via UI
- Common issues table

**Read this first if you want a working plugin in 5 minutes.**

---

### [Full Plugin Development Guide](PLUGINS_DEV.md)
**For:** Reference and architecture understanding
**Contains:**
- Quick links to all specialized guides
- Use cases and limitations
- Plugin workflow (4 steps)
- File structure overview
- Manifest format
- References to detailed guides

**Read this for the big picture and to navigate to specific topics.**

---

### [Plugin Data Contract](PLUGINS_DEV_DATA_CONTRACT.md)
**For:** Understanding plugin output format
**Contains:**
- 9 mandatory + 4 optional column specification
- Column purpose and examples
- Empty/null value handling
- Watched values explanation
- Foreign key usage
- Valid & invalid data examples
- Using `plugin_helper.py`
- De-duplication rules
- DateTime formatting
- Validation checklist
- Debugging commands

**Read this to understand exactly what format your plugin must output.**

---

### [Plugin Settings System](PLUGINS_DEV_SETTINGS.md)
**For:** Adding user-configurable options
**Contains:**
- Setting definition structure
- Required & optional properties
- 10 reserved function names (RUN, CMD, RUN_TIMEOUT, WATCH, etc.)
- Component types: text, password, select, multi-select, checkbox, textarea, label
- Reading settings in scripts (3 methods)
- Localized strings
- Complete examples (website monitor, PiHole)
- Validation & testing

**Read this to let users configure your plugin via the UI.**

---

### [Data Sources](PLUGINS_DEV_DATASOURCES.md)
**For:** Choosing how your plugin gets data
**Contains:**
- 5 data source types: `script`, `app-db-query`, `sqlite-db-query`, `template`, `plugin_type`
- Configuration for each type
- How it works section for each
- Script source best practices
- SQL query examples for app database
- External SQLite database setup
- Execution order/priority
- Performance considerations
- Debugging data sources

**Read this to decide where your plugin data comes from.**

---

### [UI Components](PLUGINS_DEV_UI_COMPONENTS.md)
**For:** Displaying plugin results in the web interface
**Contains:**
- Column definition structure
- Property reference (10+ properties)
- 15+ render types:
  - Display-only: label, device_mac, device_ip, device_name_mac, url, url_http_https, textarea_readonly
  - Interactive: textbox_save
  - Styled: threshold, replace, regex, eval
- Chaining types (e.g., regex.url_http_https)
- Dynamic options (SQL-driven, setting-driven)
- Database mapping to CurrentScan
- Static value mapping
- Filters with 5+ examples
- CSS classes reference
- Complete examples

**Read this to make your plugin results look great and work intuitively.**

---

### [Config Lifecycle](PLUGINS_DEV_CONFIG.md)
**For:** Understanding how plugins integrate
**Contains:**
- Plugin data flow diagram
- 6-step lifecycle: loading, validation, preparation, execution, parsing, mapping
- How `config.json` is processed
- Plugin output contract
- Plugin categories & execution
- Data sources in detail

**Read this to understand the deep architecture.**

---

### [Debugging Plugins](DEBUG_PLUGINS.md)
**For:** Troubleshooting when things don't work
**Contains:**
- Common errors & solutions
- Log file locations
- Commands to check status
- Validation tools
- Database queries for inspection
- Permission issues
- Performance troubleshooting

**Read this when your plugin isn't working.**


---

## Quick Reference: Key Concepts

### Plugin Output Format
```
Object_PrimaryID|Object_SecondaryID|DateTime|Watched_Value1|Watched_Value2|Watched_Value3|Watched_Value4|Extra|ForeignKey
```
9 required columns, 4 optional helpers = 13 max

See: [Data Contract](PLUGINS_DEV_DATA_CONTRACT.md)

### Plugin Metadata (config.json)
```json
{
  "code_name": "my_plugin",           // Folder name
  "unique_prefix": "MYPLN",           // Settings prefix
  "display_name": [...],              // UI label
  "data_source": "script",            // Where data comes from
  "settings": [...],                  // User configurable
  "database_column_definitions": [...] // How to display
}
```

See: [Full Guide](PLUGINS_DEV.md), [Settings](PLUGINS_DEV_SETTINGS.md)

### Reserved Settings
- `RUN` - When to execute (disabled, once, schedule, always_after_scan, etc.)
- `RUN_SCHD` - Cron schedule
- `CMD` - Command/script to execute
- `RUN_TIMEOUT` - Max execution time
- `WATCH` - Monitor for changes
- `REPORT_ON` - Notification trigger

See: [Settings System](PLUGINS_DEV_SETTINGS.md)

### Display Types
`label`, `device_mac`, `device_ip`, `url`, `threshold`, `replace`, `regex`, `textbox_save`, and more.

See: [UI Components](PLUGINS_DEV_UI_COMPONENTS.md)

---

## Tools & References

- **Template Plugin:** `/app/front/plugins/__template/` - Start here!
- **Helper Library:** `/app/front/plugins/plugin_helper.py` - Use for output formatting
- **Settings Helper:** `/app/server/helper.py` - Use `get_setting_value()` in scripts
- **Example Plugins:** `/app/front/plugins/*/` - Study working implementations
- **Logs:** `/tmp/log/plugins/` - Plugin output and execution logs
- **Backend Logs:** `/tmp/log/stdout.log` - Core system logs

---

