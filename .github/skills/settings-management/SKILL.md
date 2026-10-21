---
name: netalertx-settings-management
description: Manage NetAlertX configuration settings. Use this when asked to add setting, read config, get_setting_value, ccd, or configure options.
---

# Settings Management

## Quick Reference

**Read a setting (backend):**
```python
from helper import get_setting_value
value = get_setting_value('SETTING_NAME')
```
Never hardcode ports, secrets, or configuration values. Always use `get_setting_value()`.

**Read a setting (frontend):**
```javascript
getSetting("SETTING_NAME")
```

**Add a core setting** — use `ccd()` in `server/initialise.py`:
```python
ccd('SETTING_NAME', 'default_value', 'description')
```

**Add a plugin setting** — define in the plugin's `config.json` under the `settings` key.

| File | Purpose |
|------|---------|
| `/data/config/app.conf` | Runtime config (source of truth, modified by app) |
| `back/app.conf` | Default config (template) |

Use `APP_CONF_OVERRIDE` for settings that must be set before startup.

---

# Development Guide

The goal is for every setting to be:

- Declarative and self-documenting
- Automatically rendered by the Settings UI
- Fully localized
- Backwards compatible
- Easy to maintain

---

## 1. Follow existing patterns

Before creating a new setting, search for similar ones. Reuse existing naming conventions, types, and validation patterns. Follow the style already used by similar plugins. Avoid introducing new setting types unless absolutely necessary.

---

## 2. Setting naming

Setting keys use uppercase snake case: `UI_DEV_SECTIONS`, `SCAN_INTERVAL`, `MQTT_HOST`.
Names should clearly describe the purpose.

---

## 3. Categories

Place settings into the most appropriate category. Keep related settings together. Avoid creating new categories unless there is a clear need.

---

## 4. Choose the correct type

Use the simplest type that correctly models the value: `string`, `integer`, `float`, `boolean`, `password`, `select`, `array`, `textarea`. Avoid encoding structured JSON inside string settings.

---

## 5. Validation

Always define validation whenever appropriate (min/max values, regex, allowed options). Reject invalid configuration rather than silently accepting it.

---

## 6. Defaults

Provide sensible defaults that work for a fresh installation. The `default_value` in `config.json` is the single source of truth — do not duplicate it in Python or JavaScript.

---

## 7. Names and descriptions

Names should be concise. Descriptions should explain what the setting does, when to use it, and any important side effects — not implementation details.

---

## 8. Boolean settings

Prefer verbs: Enable, Disable, Require, Allow, Ignore, Show, Hide. Examples: *Enable MQTT*, *Require NICs Online*, *Hide Offline Devices*.

---

## 9. Select settings

Use when users must choose from predefined values. Each option must have a meaningful label — never require users to remember internal values.

---

## 10. Array settings

Use only when multiple independent values are expected (e.g., ignored MACs, subnet lists, plugin lists).

---

## 11. Localization

Every setting must have localized language strings. If not defined directly in `config.json`, they must exist in `en_us.json`.

Example for `UI_DEV_SECTIONS`:
```json
"UI_DEV_SECTIONS_name": "Hide device sections",
"UI_DEV_SECTIONS_description": "Select which UI elements to hide on the Devices page."
```

When using external language files, `config.json` must reference:
```json
"name": [{ "string": "_GLOBAL_LANG_FILES_" }]
```

---

## 12. Source of truth

`app.conf` is the source of truth. User-defined values always come from `app.conf`; defaults from `config.json` apply only when a setting is absent. Never read `app.conf` directly — always go through `get_setting_value()`.

---

## 13. Plugin-first settings

Whenever possible, define new settings inside a plugin's `config.json`. Avoid adding hardcoded application settings unless there is a compelling architectural reason.

---

## 14. Runtime lifecycle

```text
config.json (defaults)
    → app.conf (source of truth)
    → Settings database table
    → table_settings.json API
    → Frontend getSetting() / Backend get_setting_value()
```

The database and API are runtime representations only, regenerated from `app.conf` at init.

---

## 15. Backwards compatibility

Avoid renaming settings, changing data types, or changing semantics. If unavoidable, provide migration logic and preserve compatibility where possible.

---

## 16. Pull request checklist

- [ ] Follows existing naming conventions (uppercase snake case)
- [ ] Correct category used
- [ ] Appropriate type selected, validation defined
- [ ] Sensible default — defined only once (in `config.json`)
- [ ] Name concise, description clear (no implementation details)
- [ ] Localization strings added; `_GLOBAL_LANG_FILES_` used where appropriate
- [ ] Plugin-first approach followed where applicable
- [ ] Frontend renders automatically without custom JavaScript
- [ ] Backend uses `get_setting_value()` — no direct `app.conf` reads
- [ ] Backwards compatibility maintained
- [ ] Documentation updated if required

---

## References

- https://docs.netalertx.com/PLUGINS_DEV_SETTINGS/
- https://docs.netalertx.com/SETTINGS_SYSTEM/
