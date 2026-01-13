# Plugin Settings System

Learn how to let users configure your plugin via the NetAlertX UI Settings page.

> [!TIP]
> For the higher-level settings flow and lifecycle, see [Settings System Documentation](./SETTINGS_SYSTEM.md).

## Overview

Plugin settings allow users to configure:
- **Execution schedule** (when the plugin runs)
- **Runtime parameters** (API keys, URLs, thresholds)
- **Behavior options** (which features to enable/disable)
- **Command overrides** (customize the executed script)

All settings are defined in your plugin's `config.json` file under the `"settings"` array.

## Setting Definition Structure

Each setting is a JSON object with required and optional properties:

```json
{
  "function": "UNIQUE_CODE",
  "type": {
    "dataType": "string",
    "elements": [
      {
        "elementType": "input",
        "elementOptions": [],
        "transformers": []
      }
    ]
  },
  "default_value": "default_value_here",
  "options": [],
  "localized": ["name", "description"],
  "name": [
    {
      "language_code": "en_us",
      "string": "Display Name"
    }
  ],
  "description": [
    {
      "language_code": "en_us",
      "string": "Help text describing the setting"
    }
  ]
}
```

## Required Properties

| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `function` | string | Unique identifier for the setting. Used in manifest and when reading values. See [Reserved Function Names](#reserved-function-names) for special values | `"MY_CUSTOM_SETTING"` |
| `type` | object | Defines the UI component and data type | See [Component Types](#component-types) |
| `default_value` | varies | Initial value shown in UI | `"https://example.com"` |
| `localized` | array | Which properties have translations | `["name", "description"]` |
| `name` | array | Display name in Settings UI (localized) | See [Localized Strings](#localized-strings) |

## Optional Properties

| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `description` | array | Help text in Settings UI (localized) | See [Localized Strings](#localized-strings) |
| `options` | array | Valid values for select/checkbox controls | `["option1", "option2"]` |
| `events` | string | Trigger action button: `"test"` or `"run"` | `"test"` for notifications |
| `maxLength` | number | Character limit for input fields | `100` |
| `readonly` | boolean | Make field read-only | `true` |
| `override_value` | object | Template-based value override (advanced) | See [Templates](#templates) |

## Reserved Function Names

These function names have special meaning and control core plugin behavior:

### Core Execution Settings

| Function | Purpose | Type | Required | Options |
|----------|---------|------|----------|---------|
| `RUN` | **When to execute the plugin** | select | **YES** | `"disabled"`, `"once"`, `"schedule"`, `"always_after_scan"`, `"before_name_updates"`, `"on_new_device"`, `"before_config_save"` |
| `RUN_SCHD` | **Cron schedule** | input | If `RUN="schedule"` | Cron format: `"0 * * * *"` (hourly) |
| `CMD` | **Command/script to execute** | input | **YES** | Linux command or path to script |
| `RUN_TIMEOUT` | **Maximum execution time in seconds** | input | optional | Numeric: `"60"`, `"120"`, etc. |

### Data & Filtering Settings

| Function | Purpose | Type | Required | Options |
|----------|---------|------|----------|---------|
| `WATCH` | **Which columns to monitor for changes** | multi-select | optional | Column names from data contract |
| `REPORT_ON` | **When to send notifications** | select | optional | `"new"`, `"watched-changed"`, `"watched-not-changed"`, `"missing-in-last-scan"` |
| `DB_PATH` | **External database path** | input | If using SQLite plugin | File path: `"/etc/pihole/pihole-FTL.db"` |

### API & Data Settings

| Function | Purpose | Type | Required | Options |
|----------|---------|------|----------|---------|
| `API_SQL` | **Generate API JSON file** | (reserved) | Not implemented | — |

## Component Types

### Text Input

Simple text field for API keys, URLs, thresholds, etc.

```json
{
  "function": "URL",
  "type": {
    "dataType": "string",
    "elements": [
      {
        "elementType": "input",
        "elementOptions": [],
        "transformers": []
      }
    ]
  },
  "default_value": "https://api.example.com",
  "localized": ["name", "description"],
  "name": [{"language_code": "en_us", "string": "API URL"}],
  "description": [{"language_code": "en_us", "string": "The API endpoint to query"}]
}
```

### Password Input

Secure field with SHA256 hashing transformer.

```json
{
  "function": "API_KEY",
  "type": {
    "dataType": "string",
    "elements": [
      {
        "elementType": "input",
        "elementOptions": [{"type": "password"}],
        "transformers": ["sha256"]
      }
    ]
  },
  "default_value": "",
  "localized": ["name", "description"],
  "name": [{"language_code": "en_us", "string": "API Key"}],
  "description": [{"language_code": "en_us", "string": "Stored securely with SHA256 hashing"}]
}
```

### Dropdown/Select

Choose from predefined options.

```json
{
  "function": "RUN",
  "type": {
    "dataType": "string",
    "elements": [
      {
        "elementType": "select",
        "elementOptions": [],
        "transformers": []
      }
    ]
  },
  "default_value": "disabled",
  "options": ["disabled", "once", "schedule", "always_after_scan"],
  "localized": ["name", "description"],
  "name": [{"language_code": "en_us", "string": "When to run"}],
  "description": [{"language_code": "en_us", "string": "Select execution trigger"}]
}
```

### Multi-Select

Select multiple values (returns array).

```json
{
  "function": "WATCH",
  "type": {
    "dataType": "array",
    "elements": [
      {
        "elementType": "select",
        "elementOptions": [{"isMultiSelect": true}],
        "transformers": []
      }
    ]
  },
  "default_value": [],
  "options": ["Status", "IP_Address", "Response_Time"],
  "localized": ["name", "description"],
  "name": [{"language_code": "en_us", "string": "Watch columns"}],
  "description": [{"language_code": "en_us", "string": "Which columns trigger notifications on change"}]
}
```

### Checkbox

Boolean toggle.

```json
{
  "function": "ENABLED",
  "type": {
    "dataType": "boolean",
    "elements": [
      {
        "elementType": "input",
        "elementOptions": [{"type": "checkbox"}],
        "transformers": []
      }
    ]
  },
  "default_value": false,
  "localized": ["name", "description"],
  "name": [{"language_code": "en_us", "string": "Enable feature"}],
  "description": [{"language_code": "en_us", "string": "Toggle this feature on/off"}]
}
```

### Textarea

Multi-line text input.

```json
{
  "function": "CUSTOM_CONFIG",
  "type": {
    "dataType": "string",
    "elements": [
      {
        "elementType": "textarea",
        "elementOptions": [],
        "transformers": []
      }
    ]
  },
  "default_value": "",
  "localized": ["name", "description"],
  "name": [{"language_code": "en_us", "string": "Custom Configuration"}],
  "description": [{"language_code": "en_us", "string": "Enter configuration (one per line)"}]
}
```

### Read-Only Label

Display information without user input.

```json
{
  "function": "STATUS_DISPLAY",
  "type": {
    "dataType": "string",
    "elements": [
      {
        "elementType": "input",
        "elementOptions": [{"readonly": true}],
        "transformers": []
      }
    ]
  },
  "default_value": "Ready",
  "localized": ["name"],
  "name": [{"language_code": "en_us", "string": "Status"}]
}
```

## Using Settings in Your Script

### Method 1: Via `get_setting_value()` Helper

**Recommended approach** — clean and simple:

```python
from helper import get_setting_value

# Read the setting by function name with plugin prefix
api_url = get_setting_value('MYPLN_API_URL')
api_key = get_setting_value('MYPLN_API_KEY')
watch_columns = get_setting_value('MYPLN_WATCH')  # Returns list if multi-select

# Use in your script
mylog("none", f"Connecting to {api_url} with key {api_key}")
```

### Method 2: Via Command Parameters

For more complex scenarios where you need to **pass settings as command-line arguments**:

Define `params` in your `config.json`:

```json
{
  "params": [
    {
      "name": "api_url",
      "type": "setting",
      "value": "MYPLN_API_URL"
    },
    {
      "name": "timeout",
      "type": "setting",
      "value": "MYPLN_RUN_TIMEOUT"
    }
  ]
}
```

Update your `CMD` setting:

```json
{
  "function": "CMD",
  "default_value": "python3 /app/front/plugins/my_plugin/script.py --url={api_url} --timeout={timeout}"
}
```

The framework will replace `{api_url}` and `{timeout}` with actual values before execution.

### Method 3: Via Environment Variables (check with maintainer)

Settings are also available as environment variables:

```bash
# Environment variable format: <PREFIX>_<FUNCTION>
MY_PLUGIN_API_URL
MY_PLUGIN_API_KEY
MY_PLUGIN_RUN
```

In Python:
```python
import os

api_url = os.environ.get('MYPLN_API_URL', 'default_value')
```

## Localized Strings

Settings and UI text support multiple languages. Define translations in the `name` and `description` arrays:

```json
{
  "localized": ["name", "description"],
  "name": [
    {
      "language_code": "en_us",
      "string": "API URL"
    },
    {
      "language_code": "es_es",
      "string": "URL de API"
    },
    {
      "language_code": "de_de",
      "string": "API-URL"
    }
  ],
  "description": [
    {
      "language_code": "en_us",
      "string": "Enter the API endpoint URL"
    },
    {
      "language_code": "es_es",
      "string": "Ingrese la URL del endpoint de API"
    },
    {
      "language_code": "de_de",
      "string": "Geben Sie die API-Endpunkt-URL ein"
    }
  ]
}
```

- `en_us` - English (required)


## Examples

### Example 1: Website Monitor Plugin

```json
{
  "settings": [
    {
      "function": "RUN",
      "type": {"dataType": "string", "elements": [{"elementType": "select", "elementOptions": [], "transformers": []}]},
      "default_value": "disabled",
      "options": ["disabled", "once", "schedule"],
      "localized": ["name", "description"],
      "name": [{"language_code": "en_us", "string": "When to run"}],
      "description": [{"language_code": "en_us", "string": "Enable website monitoring"}]
    },
    {
      "function": "RUN_SCHD",
      "type": {"dataType": "string", "elements": [{"elementType": "input", "elementOptions": [], "transformers": []}]},
      "default_value": "*/5 * * * *",
      "localized": ["name", "description"],
      "name": [{"language_code": "en_us", "string": "Schedule"}],
      "description": [{"language_code": "en_us", "string": "Cron format (default: every 5 minutes)"}]
    },
    {
      "function": "CMD",
      "type": {"dataType": "string", "elements": [{"elementType": "input", "elementOptions": [], "transformers": []}]},
      "default_value": "python3 /app/front/plugins/website_monitor/script.py urls={urls}",
      "localized": ["name", "description"],
      "name": [{"language_code": "en_us", "string": "Command"}],
      "description": [{"language_code": "en_us", "string": "Command to execute"}]
    },
    {
      "function": "RUN_TIMEOUT",
      "type": {"dataType": "string", "elements": [{"elementType": "input", "elementOptions": [], "transformers": []}]},
      "default_value": "60",
      "localized": ["name", "description"],
      "name": [{"language_code": "en_us", "string": "Timeout"}],
      "description": [{"language_code": "en_us", "string": "Maximum execution time in seconds"}]
    },
    {
      "function": "URLS",
      "type": {"dataType": "array", "elements": [{"elementType": "input", "elementOptions": [], "transformers": []}]},
      "default_value": ["https://example.com"],
      "maxLength": 200,
      "localized": ["name", "description"],
      "name": [{"language_code": "en_us", "string": "URLs to monitor"}],
      "description": [{"language_code": "en_us", "string": "One URL per line"}]
    },
    {
      "function": "WATCH",
      "type": {"dataType": "array", "elements": [{"elementType": "select", "elementOptions": [{"isMultiSelect": true}], "transformers": []}]},
      "default_value": ["Status_Code"],
      "options": ["Status_Code", "Response_Time", "Certificate_Expiry"],
      "localized": ["name", "description"],
      "name": [{"language_code": "en_us", "string": "Watch columns"}],
      "description": [{"language_code": "en_us", "string": "Which changes trigger notifications"}]
    }
  ]
}
```

### Example 2: PiHole Integration Plugin

```json
{
  "settings": [
    {
      "function": "RUN",
      "type": {"dataType": "string", "elements": [{"elementType": "select", "elementOptions": [], "transformers": []}]},
      "default_value": "disabled",
      "options": ["disabled", "schedule"],
      "localized": ["name", "description"],
      "name": [{"language_code": "en_us", "string": "When to run"}],
      "description": [{"language_code": "en_us", "string": "Enable PiHole integration"}]
    },
    {
      "function": "DB_PATH",
      "type": {"dataType": "string", "elements": [{"elementType": "input", "elementOptions": [], "transformers": []}]},
      "default_value": "/etc/pihole/pihole-FTL.db",
      "localized": ["name", "description"],
      "name": [{"language_code": "en_us", "string": "Database path"}],
      "description": [{"language_code": "en_us", "string": "Path to pihole-FTL.db inside container"}]
    },
    {
      "function": "API_KEY",
      "type": {"dataType": "string", "elements": [{"elementType": "input", "elementOptions": [{"type": "password"}], "transformers": ["sha256"]}]},
      "default_value": "",
      "localized": ["name", "description"],
      "name": [{"language_code": "en_us", "string": "API Key"}],
      "description": [{"language_code": "en_us", "string": "PiHole API key (optional, stored securely)"}]
    }
  ]
}
```

## Validation & Testing

### Check Settings Are Recognized

After saving your `config.json`:

1. Restart the backend: Run task `[Dev Container] Start Backend (Python)`
2. Open Settings page in UI
3. Navigate to Plugin Settings
4. Look for your plugin's settings

### Read Setting Values in Script

Test that values are accessible:

```python
from helper import get_setting_value

# Try to read a setting
value = get_setting_value('MYPLN_API_URL')
mylog('none', f"Setting value: {value}")

# Should print the user-configured value or default
```

### Debug Settings

Check backend logs:

```bash
tail -f /tmp/log/stdout.log | grep -i "setting\|MYPLN"
```

## See Also

- [Settings System Documentation](./SETTINGS_SYSTEM.md) - Full settings flow and lifecycle
- [Quick Start Guide](PLUGINS_DEV_QUICK_START.md) - Get a working plugin quickly
- [Plugin Data Contract](PLUGINS_DEV_DATA_CONTRACT.md) - Output data format
- [UI Components](PLUGINS_DEV_UI_COMPONENTS.md) - Display plugin results
