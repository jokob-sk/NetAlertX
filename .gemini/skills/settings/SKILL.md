---
name: nax-settings-development
description: Best practices for creating and maintaining NetAlertX settings (config.json), including UI, validation, localization, runtime behavior, and implementation consistency.
---

# NetAlertX Settings Development

This skill defines the conventions and best practices for adding or modifying settings in NetAlertX.

The goal is for every setting to be:

- Declarative
- Self-documenting
- Automatically rendered by the Settings UI
- Fully localized
- Backwards compatible
- Easy to maintain

---

## Quick Reference

**Read a setting (backend):**
```python
from helper import get_setting_value
value = get_setting_value('SETTING_NAME')
```
Never read `app.conf` directly. Always use `get_setting_value()`.

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
| `/data/config/app.conf` | Runtime config (source of truth) |
| `back/app.conf` | Default config (template) |

Use `APP_CONF_OVERRIDE` for settings that must be set before startup.

---

# 1. Follow existing patterns

Before creating a new setting:

- Search for similar settings.
- Reuse existing naming conventions.
- Reuse existing setting types.
- Reuse existing validation patterns.
- Follow the style already used by similar plugins.

Avoid introducing new setting types unless absolutely necessary.

---

# 2. Setting naming

Setting keys use uppercase snake case.

Good:

```text
UI_DEV_SECTIONS
SCAN_INTERVAL
MQTT_HOST
```

Avoid:

```text
uiDevSections
scanInterval
ScanInterval
```

Names should clearly describe the purpose.

---

# 3. Categories

Place settings into the most appropriate category.

Keep related settings together.

Avoid creating new categories unless there is a clear need.

---

# 4. Choose the correct type

Use the simplest type that correctly models the value.

Common types include:

- string
- integer
- float
- boolean
- password
- select
- array
- textarea

Avoid encoding structured JSON inside string settings.

---

# 5. Validation

Always define validation whenever appropriate.

Examples include:

- minimum values
- maximum values
- regex validation
- allowed options

Reject invalid configuration rather than silently accepting it.

---

# 6. Defaults

Provide sensible defaults that work for a fresh installation.

Avoid defaults that require external services or additional configuration.

A default value should exist in exactly one place.

Use the `default_value` defined in `config.json`.

Do not duplicate the same default value elsewhere in Python or JavaScript.

---

# 7. Names and descriptions

Setting names should be concise.

Examples:

- Scan interval
- MQTT Host
- Hide device sections

Descriptions should explain:

- what the setting does
- when it should be used
- important side effects

Avoid implementation details.

Good:

> Interval between network scans in seconds.

Bad:

> Calls scheduler.py every X seconds.

---

# 8. Boolean settings

Boolean settings should read naturally.

Prefer verbs such as:

- Enable
- Disable
- Require
- Allow
- Ignore
- Show
- Hide

Examples:

- Enable MQTT
- Require NICs Online
- Hide Offline Devices

---

# 9. Select settings

When users must choose from predefined values, use a select setting.

Never require users to remember internal values.

Each option should have a meaningful label.

---

# 10. Array settings

Use arrays only when multiple independent values are expected.

Examples:

- ignored MAC addresses
- subnet lists
- plugin lists

---

# 11. Localization

Every setting must have localized language strings.

If the language strings are **not** defined directly inside `config.json`, they must exist in `en_us.json`.

For example, for:

```text
UI_DEV_SECTIONS
```

add:

```json
"UI_DEV_SECTIONS_name": "Hide device sections",
"UI_DEV_SECTIONS_description": "Select which UI elements to hide on the Devices page."
```

When using external language files, `config.json` must reference:

```json
"name": [
  {
    "string": "_GLOBAL_LANG_FILES_"
  }
]
```

This tells NetAlertX to resolve the display name from the language files.

---

# 12. Source of truth

`app.conf` is the source of truth.

Keep the following in mind:

- User-defined values always come from `app.conf`.
- Default values from `config.json` are only used when the setting is missing from `app.conf`.
- Never assume settings are permanently stored in the database.

---

# 13. Plugin-first settings

Whenever possible, define new settings inside a plugin's `config.json`.

Avoid adding hardcoded application settings unless there is a compelling architectural reason.

Plugin settings are the preferred and future-proof approach.

---

# 14. Runtime lifecycle

Understand how settings flow through the application.

```text
config.json
        │
        │ default values
        ▼
app.conf (source of truth)
        │
        ▼
Settings database table
        │
        ▼
table_settings.json API
        │
        ▼
Frontend (getSetting())
```

The database and API are runtime representations only.

They are regenerated from `app.conf` during initialization.

---

# 15. Access

Code should never read `app.conf` directly.

In the Frontend, always retrieve settings through:

```javascript
getSetting("SETTING_NAME")
```

And in the backend, always retrieve settings through:

```python
get_setting_value("SETTING_NAME")
```

This guarantees the value comes from the generated settings API.

---

# 16. Metadata

Each setting automatically has a corresponding `__metadata` entry generated in `app.conf`.

Do not manually create or modify metadata entries unless working on the settings framework itself.

---

# 17. Backend

Backend code should:

- use the existing configuration helpers
- avoid duplicated parsing logic
- gracefully handle missing values
- avoid hardcoded defaults

---

# 18. Frontend

A correctly defined setting should render automatically in the existing Settings UI.

Avoid writing custom JavaScript unless absolutely necessary.

---

# 19. Prefer configuration over code

If a behaviour can reasonably be controlled through an existing setting type (boolean, select, integer, array, etc.), introduce a setting instead of hardcoding special-case logic.

Configuration is preferred over implementation-specific behaviour whenever practical.

---

# 20. Backwards compatibility

Avoid:

- renaming settings
- changing data types
- changing semantics

If unavoidable:

- provide migration logic
- preserve compatibility where possible

---

# 21. Documentation

Every user-facing setting should eventually be documented.

Include:

- purpose
- accepted values
- default value
- examples when useful

---

# 22. Pull request checklist

Before submitting a PR, verify:

- [ ] Setting follows existing conventions.
- [ ] Correct category used.
- [ ] Appropriate type selected.
- [ ] Validation defined.
- [ ] Sensible default provided.
- [ ] Default defined only once.
- [ ] Name is concise.
- [ ] Description is clear.
- [ ] Localization strings added.
- [ ] `_GLOBAL_LANG_FILES_` used where appropriate.
- [ ] Plugin-first approach followed where applicable.
- [ ] Frontend renders automatically.
- [ ] Backend uses existing configuration helpers.
- [ ] No unnecessary frontend code added.
- [ ] No duplicated parsing logic.
- [ ] Backwards compatibility maintained.
- [ ] Documentation updated if required.

---

# References

- https://docs.netalertx.com/PLUGINS_DEV_SETTINGS/
- https://docs.netalertx.com/SETTINGS_SYSTEM/
- https://docs.netalertx.com/PLUGINS_OVERVIEW/