# ⚠ Disclaimer

Highly experimental feature. Follow the below very carefully and check example plugin(s). Plugin UI is not my priority right now, happy to approve PRs if you are interested in extending/improvintg the UI experience. 

## Overview

PiAlert comes with a simple plugin system to feed events from third-party scripts into the UI and then send notifications if desired.

If you wish to develop a plugin, please check the existing plugin structure. Once the settings are saved by the user they need to be removed from the `pialert.conf` file manually if you want to re-initialize them from the `config.json` of teh plugin.

## Plugin file structure overview 

> Folder name must be the same as the code name value in: `"code_name": "<value>"`
> Unique prefix needs to be unique compared to the other settings prefixes, e.g.: the prefix `APPRISE` is already in use. 

  | File | Required | Description | 
  |----------------------|----------------------|----------------------| 
  | `config.json` | yes | Contains the plugin configuration (manifest) including the settings available to the user. |
  | `script.py` |  yes | The Python script itself |
  | `last_result.log` | yes | The file used to interface between PiAlert and the plugin (script).  |
  | `script.log` | no | Logging output (recommended) |
  | `README.md` | no | Any setup considerations or overview (recommended) |


More on specific files below.

### script.log

Used to interface between PiAlert and the plugin (script). After every scan it should contain only the results from the latest scan/execution. 

- The format is a `csv`-like file with the pipe `|` separator. 8 (eight) values need to be supplied, so every line needs to contain 7 pipe separators. Empty values are represented by `null`  
- Don't render "headers" for these "columns"
- Every scan result / event entry needs to be on a new line
- You can find which "columns" need to be present in the script results and if the value is required below. 
- The order of these "columns" can't be changed


  | Order | Represented Column | Required | Description | 
  |----------------------|----------------------|----------------------|----------------------| 
  | 0 | `Object_PrimaryID` | yes | The primary ID used to group Events under. |
  | 1 | `Object_SecondaryID` | no | Optionalsecondary ID to create a relationship beween other entities, such as a MAC address |
  | 2 | `DateTime` | yes | When the event occured in the format `2023-01-02 15:56:30` |
  | 3 | `Watched_Value1` | yes | A value that is watched and users can receive notifications if it changed compared to the previously saved entry. For example IP address |
  | 4 | `Watched_Value2` | no | As above |
  | 5 | `Watched_Value3` | no | As above  |
  | 6 | `Watched_Value4` | no | As above  |
  | 7 | `Extra` | no | Any other data you want to pass and display in PiAlert and the notifcations |

#### Examples

Valid CSV:

```csv

https://www.google.com|null|2023-01-02 15:56:30|200|0.7898|null|null|null
https://www.duckduckgo.com|192.168.0.1|2023-01-02 15:56:30|200|0.9898|null|null|Best search engine

```

Invalid CSV with different errors on each line:

```csv

https://www.google.com|null|2023-01-02 15:56:30|200|0.7898||null|null
https://www.duckduckgo.com|null|2023-01-02 15:56:30|200|0.9898|null|null|Best search engine|
|https://www.duckduckgo.com|null|2023-01-02 15:56:30|200|0.9898|null|null|Best search engine
null|192.168.1.1|2023-01-02 15:56:30|200|0.9898|null|null|Best search engine
https://www.duckduckgo.com|192.168.1.1|2023-01-02 15:56:30|null|0.9898|null|null|Best search engine
https://www.google.com|null|2023-01-02 15:56:30|200|0.7898|||
https://www.google.com|null|2023-01-02 15:56:30|200|0.7898|

```

### config.json 

#### params

- `"name":"name_value"` - is used as a wildcard replacement in the `CMD` setting value by using curly brackets `{name_value}`. The wildcard is replaced by the result of the `"value" : "param_value"` and `"type":"type_value"` combo configuration below.
- `"type":"<sql|setting>"` - is used to specify the type of the params, currently only 2 supported (`sql`,`setting`).
  - `"type":"sql"` - will execute the SQL query specified in the `value` property. The sql query needs to return only one column. The column is flattened and separated by commas (`,`), e.g: `SELECT dev_MAC from DEVICES` -> `Internet,74:ac:74:ac:74:ac,44:44:74:ac:74:ac`. This is then used to replace the wildcards in the `CMD`setting.  
  - `"type":"setting"` - The setting code name. A combination of the value from `unique_prefix` + `_` + `function` value, or otherwise the code name you can find in the Settings page under the Setting dispaly name, e.g. `SCAN_CYCLE_MINUTES`. 
- `"value" : "param_value"` - Needs to contain a setting code name or sql query without wildcards.


Example:

```json
{
    "params" : [{
            "name"  : "macs",
            "type"  : "sql",
            "value" : "SELECT dev_MAC from DEVICES"
        },
        {
            "name"  : "urls",
            "type"  : "setting",
            "value" : "WEBMON_urls_to_check"
        },
        {
            "name"  : "internet_ip",
            "type"  : "setting",
            "value" : "WEBMON_SQL_internet_ip"
        }]
}
```


#### Setting object struncture

- `"function": "<see Supported settings function values>"` - What function the setting drives or a simple unique code name
- `"type": "<text|integer|boolean|password|readonly|selectinteger|selecttext|multiselect|list>"` - The form control used for the setting displayed in the Settings page and what values are accepted.
- `"localized"` - a list of properties on the current JSON level which need to be localized
- `"name"` and `"description"` - Displayed in the Settings page. An array of localized strings. (see Localized strings below).
    
##### Supported settings `function` values

- `RUN` - (required) Specifies when the service is executed
    - Supported Options: "disabled", "once", "schedule" (if included then a `RUN_SCHD` setting needs to be specified), "always_after_scan", "on_new_device"
- `RUN_SCHD` - (required if you include the  `RUN`) Cron-like scheduling used if the `RUN` setting set to `schedule`
- `CMD` - (required) What command should be executed. 
- `API_SQL` - (optional) Generates a `table_` + code_name  + `.json` file as per [API docs](https://github.com/jokob-sk/Pi.Alert/blob/main/docs/API.md).
- `RUN_TIMEOUT` - (optional) Max execution time of the script. If not specified a default value of 10 seconds is used to prevent hanging.
- `WATCH` - (optional) Which database columns are watched for changes for this particular plugin. If not specified no notifications are sent. 


Example:

```json
{
    "function": "RUN",            
    "type": "selecttext",            
    "default_value":"disabled",
    "options": ["disabled", "once", "schedule", "always_after_scan", "on_new_device"],
    "localized": ["name", "description"],
    "name" :[{
        "language_code":"en_us",
        "string" : "When to run"
    }],
    "description": [{
        "language_code":"en_us",
        "string" : "Enable a regular scan of your services. If you select <code>schedule</code> the scheduling settings from below are applied. If you select <code>once</code> the scan is run only once on start of the application (container) for the time specified in <a href=\"#WEBMON_RUN_TIMEOUT\"><code>WEBMON_RUN_TIMEOUT</code> setting</a>."
    }]
}
```
##### Localized strings



- `"language_code":"<en_us|es_es|de_de>"`  - code name of the language string. Only these three currently supported. At least the `"language_code":"en_us"` variant has to be defined. 
- `"string"`  - The string to be displayed in the given language.

Example:

```json

    {
        "language_code":"en_us",
        "string" : "When to run"
    }

```
##### database_column_aliases

- Only columns specified in the `"localized"` parameter and also with at least an english translation will be shown in the UI.

```json
{  
        "localized": ["Index", "Object_PrimaryID", "DateTime", "Watched_Value1", "Watched_Value2"],      
        "Index":[{
            "language_code":"en_us",
            "string" : "Index"
        }],
        "Object_PrimaryID":[{
            "language_code":"en_us",
            "string" : "Monitored URL"
        }],
        "DateTime":[{
            "language_code":"en_us",
            "string" : "Checked on"
        }],
        "Watched_Value1":[{
            "language_code":"en_us",
            "string" : "Status code"
        }],
        "Watched_Value2":[{
            "language_code":"en_us",
            "string" : "Latency"
        }]        
    }
```

## Full Example

```json
{
    "code_name": "website_monitor",
    "unique_prefix": "WEBMON",
    "localized": ["display_name", "description", "icon"],
    "display_name" : [{
        "language_code":"en_us",
        "string" : "Website monitor"
    }],
    "icon":[{
        "language_code":"en_us",
        "string" : "<i class=\"fa-solid fa-globe\"></i>"
    }],     
    "description": [{
        "language_code":"en_us",
        "string" : "This plugin is to monitor status changes of different services or websites."
    }],
    "params" : [{
        "name"  : "macs",
        "type"  : "sql",
        "value" : "SELECT dev_MAC from DEVICES"
    },
    {
        "name"  : "urls",
        "type"  : "setting",
        "value" : "WEBMON_urls_to_check"
    },
    {
        "name"  : "internet_ip",
        "type"  : "setting",
        "value" : "WEBMON_SQL_internet_ip"
    }],  
    "database_column_aliases":{  
        "localized": ["Index", "Object_PrimaryID", "DateTime", "Watched_Value1", "Watched_Value2"],      
        "Index":[{
            "language_code":"en_us",
            "string" : "Index"
        }],
        "Object_PrimaryID":[{
            "language_code":"en_us",
            "string" : "Monitored URL"
        }],
        "DateTime":[{
            "language_code":"en_us",
            "string" : "Checked on"
        }],
        "Watched_Value1":[{
            "language_code":"en_us",
            "string" : "Status code"
        }],
        "Watched_Value2":[{
            "language_code":"en_us",
            "string" : "Latency"
        }]        
    },
    "settings":[
        {
            "function": "RUN",            
            "type": "selecttext",            
            "default_value":"disabled",
            "options": ["disabled", "once", "schedule", "always_after_scan", "on_new_device"],
            "localized": ["name", "description"],
            "name" :[{
                "language_code":"en_us",
                "string" : "When to run"
            }],
            "description": [{
                "language_code":"en_us",
                "string" : "Enable a regular scan of your services. If you select <code>schedule</code> the scheduling settings from below are applied. If you select <code>once</code> the scan is run only once on start of the application (container) for the time specified in <a href=\"#WEBMON_RUN_TIMEOUT\"><code>WEBMON_RUN_TIMEOUT</code> setting</a>."
            }]
        },
        {
            "function": "CMD",
            "type": "text",
            "default_value":"python3 /home/pi/pialert/front/plugins/website_monitor/script.py urls={urls}",
            "options": [],
            "localized": ["name", "description"],
            "name" : [{
                "language_code":"en_us",
                "string" : "Command"
            }],
            "description": [{
                "language_code":"en_us",
                "string" : "Comamnd to run"
            }]
        },
        {
            "function": "FORCE_REPORT",
            "type": "boolean",
            "default_value": false,
            "options": [],
            "localized": ["name", "description"],
            "name" : [{
                "language_code":"en_us",
                "string" : "Force report"
            },
            {
                "language_code":"de_de",
                "string" : "Zwing Bericht"
            }],
            "description": [{
                "language_code":"en_us",
                "string" : "Force a notification message even if there are no changes detected."
            }]
            
        },
        {
            "function": "RUN_SCHD",
            "type": "text",
            "default_value":"0 2 * * *",
            "options": [],
            "localized": ["name", "description"],
            "name" : [{
                "language_code":"en_us",
                "string" : "Schedule"
            }],
            "description": [{
                "language_code":"en_us",
                "string" : "Only enabled if you select <code>schedule</code> in the <a href=\"#WEBMON_RUN\"><code>WEBMON_RUN</code> setting</a>. Make sure you enter the schedule in the correct cron-like format (e.g. validate at <a href=\"https://crontab.guru/\" target=\"_blank\">crontab.guru</a>). For example entering <code>0 4 * * *</code> will run the scan after 4 am in the <a onclick=\"toggleAllSettings()\" href=\"#TIMEZONE\"><code>TIMEZONE</code> you set above</a>. Will be run NEXT time the time passes."
            }]
        },
        {
            "function": "API_SQL",
            "type": "text",
            "default_value":"SELECT * FROM plugin_website_monitor",
            "options": [],
            "localized": ["name", "description"],
            "name" : [{
                "language_code":"en_us",
                "string" : "API endpoint"
            }],
            "description": [{
                "language_code":"en_us",
                "string" : "You can specify a custom SQL query which will generate a JSON file and then expose it via the <a href=\"/api/plugin_website_monitor.json\" target=\"_blank\"><code>plugin_website_monitor.json</code> file endpoint</a>."
            }]            
        },
        {
            "function": "RUN_TIMEOUT",
            "type": "integer",
            "default_value":5,
            "options": [],
            "localized": ["name", "description"],
            "name" : [{
                "language_code":"en_us",
                "string" : "Run timeout"
            }],
            "description": [{
                "language_code":"en_us",
                "string" : "Maximum time in seconds to wait for a Website monitor check to finish for any url."
            }]
        },
        {
            "function": "WATCH",
            "type": "multiselect",
            "default_value":["Watched_Value1"],
            "options": ["Watched_Value1","Watched_Value2","Watched_Value3","Watched_Value4"],
            "localized": ["name", "description"],
            "name" :[{
                "language_code":"en_us",
                "string" : "Notify on"
            }] ,
            "description":[{
                "language_code":"en_us",
                "string" : "Send a notification if selected values change. Use <code>CTRL + Click</code> to select/deselect. <ul> <li><code>Watched_Value1</code> is response status code (e.g.: 200, 404)</li><li><code>Watched_Value2</code> is Latency (not recommended)</li><li><code>Watched_Value3</code> unused </li><li><code>Watched_Value4</code> unused </li></ul>"
            }] 
        },
        {
            "function": "urls_to_check",
            "type": "list",
            "default_value":[],
            "options": [],
            "localized": ["name", "description"],
            "name" : [{
                "language_code":"en_us",
                "string" : "Arguments"
            }],
            "description": [{
                "language_code":"en_us",
                "string" : "Services to watch. Enter full URL, e.g. <code>https://google.com</code>."
            }]
        },
        {
            "function": "SQL_internet_ip",
            "type": "readonly",
            "default_value":"SELECT dev_LastIP FROM Devices WHERE dev_MAC = 'Internet'",
            "options": [],
            "localized": ["name", "description"],
            "name" : [{
                "language_code":"en_us",
                "string" : "Helper variable"
            }],
            "description": [{
                "language_code":"en_us",
                "string" : "Getting the IP address of the Router / Internet"
            }]
        }

    ]
}



```
