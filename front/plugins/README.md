## Overview

PiAlert comes with a simple plugin system to feed events from third-party scripts into the UI and then send notifications if desired.

If you wish to develop a plugin, please check the existing plugin structure.

## Plugin file structure overview 

  | File | Required | Description | 
  |----------------------|----------------------|----------------------| 
  | `config.json` | yes | Contains the plugin configuration including the settings available to the user. |
  | `script.py` |  yes | The Python script itself |
  | `last_result.log` | yes | The file used to interface between PiAlert and the plugin (script).  |
  | `script.log` | no | Logging output (recommended) |
  | `README.md` | no | Amy setup considerations or overview |


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

#### Supported settings types

- `RUN` 
- `RUN_SCHD` 
- `API_SQL` 
- `TIMEOUT` 
- `NOTIFY_ON` 
- `ARGS` 


#### Example

```json
{
    "code_name": "website_monitor",
    "settings_short_prefix": "WEBMON",
    "display_name" : "Website monitor",
    "font_awesome_icon_classses": "fa-solid fa-globe",
    "description": {
        "en_us" : "This plugin is to monitor status changes of different services or websites."
    },
    "database_column_aliases":{
        "Plugins_Events":{
            "Index":{
                "en_us" : "Index"
            },
            "Object_PrimaryID":{
                "en_us" : "Monitored URL"
            },
            "DateTime":{
                "en_us" : "Checked on"
            },
            "Watched_Value1":{
                "en_us" : "Status code"
            },
            "Watched_Value2":{
                "en_us" : "Latency"
            }
        }
    },
    "settings":[
        {
            "type": "RUN",
            "default_value":"none",
            "options": ["none","once","schedule"],
            "name" : {
                "en_us" : "Schedule"
            },
            "description": 
                {
                    "en_us" : "Enable a regular scan of your services. If you select <code>schedule</code> the scheduling settings from below are applied. If you select <code>once</code> the scan is run only once on start of the application (container) for the time specified in <a href=\"#WEBMON_TIMEOUT\"><code>WEBMON_TIMEOUT</code> setting</a>."
                }
            
        },
        {
            "type": "RUN_SCHD",
            "default_value":"0 2 * * *",
            "name" : {
                "en_us" : "Schedule"
            },
            "description": 
                {
                    "en_us" : "Only enabled if you select <code>schedule</code> in the <a href=\"#WEBMON_RUN\"><code>WEBMON_RUN</code> setting</a>. Make sure you enter the schedule in the correct cron-like format (e.g. validate at <a href=\"https://crontab.guru/\" target=\"_blank\">crontab.guru</a>). For example entering <code>0 4 * * *</code> will run the scan after 4 am in the <a onclick=\"toggleAllSettings()\" href=\"#TIMEZONE\"><code>TIMEZONE</code> you set above</a>. Will be run NEXT time the time passes."
                }
            
        },
        {
            "type": "API_SQL",
            "default_value":"SELECT * FROM plugin_website_monitor",
            "name" : {
                "en_us" : "API endpoint"
            },
            "description": 
                {
                    "en_us" : "You can specify a custom SQL query which will generate a JSON file and then expose it via the <a href=\"/api/plugin_website_monitor.json\" target=\"_blank\"><code>plugin_website_monitor.json</code> file endpoint</a>."
                }
            
        },
        {
            "type": "TIMEOUT",
            "default_value":5,
            "name" : {
                "en_us" : "Run timeout"
            },
            "description": 
                {
                    "en_us" : "Maximum time in seconds to wait for a Website monitor check to finish for any url."
                }
            
        },
        {
            "type": "NOTIFY_ON",
            "default_value":["Watched_Value1"],
            "options": ["Watched_Value1","Watched_Value2","Watched_Value3","Watched_Value4"],
            "name" : {
                "en_us" : "Notify on"
            },
            "description": 
                {
                    "en_us" : "Send a notification if selected values change. Use <code>CTRL + Click</code> to select/deselect. <ul> <li><code>Watched_Value1</code> is response status code (e.g.: 200, 404)</li><li><code>Watched_Value2</code> is Latency (not recommended)</li><li><code>Watched_Value3</code> unused </li><li><code>Watched_Value4</code> unused </li></ul>"
                }            
        },
        {
            "type": "ARGS",
            "default_value":"",
            "name" : {
                "en_us" : "Run timeout"
            },
            "description": 
                {
                    "en_us" : "Change the <a href=\"https://linux.die.net/man/1/dig\" target=\"_blank\">dig utility</a> arguments if you have issues resolving your Internet IP. Arguments are added at the end of the following command: <code>dig +short </code>."
                }            
        }

    ]
}



```
