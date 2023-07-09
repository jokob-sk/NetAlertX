## 📚 Docs for individual plugins 

### Script based plugins

- [website_monitor (WEBMON)](https://github.com/jokob-sk/Pi.Alert/blob/main/pialert/plugins/website_monitor/) 
- [dhcp_servers (DHCPSRVS)](https://github.com/jokob-sk/Pi.Alert/blob/main/pialert/plugins/dhcp_servers/) 
- [dhcp_leases (DHCPLSS)](https://github.com/jokob-sk/Pi.Alert/blob/main/pialert/plugins/dhcp_leases/) 
- [unifi_import (UNFIMP)](https://github.com/jokob-sk/Pi.Alert/blob/main/pialert/plugins/unifi_import/)
- [snmp_discovery (SNMPDSC)](https://github.com/jokob-sk/Pi.Alert/blob/main/pialert/plugins/snmp_discovery/)
- [undiscoverables (UNDIS)](https://github.com/jokob-sk/Pi.Alert/blob/main/pialert/plugins/undiscoverables/)

### SQL query based plugins
- [nmap_services (NMAPSERV)](https://github.com/jokob-sk/Pi.Alert/blob/main/pialert/plugins/nmap_services/) 

## 🌟 Create a custom plugin: Overview

| ![Screen 1][screen1] | ![Screen 2][screen2] | 
|----------------------|----------------------| 
| ![Screen 3][screen3] | ![Screen 4][screen4] | 

PiAlert comes with a plugin system to feed events from third-party scripts into the UI and then send notifications, if desired. The highlighted functionality this plugin system supports, is dynamic creation of a simple UI to interact with the discovered objects, a mechanism to surface settings of plugins in the UI, or to import objects into existing PiAlert database tables. (Currently update/overwriting of existing objects is not supported.)

Example use cases for plugins could be:

* Monitor a web service and alert me if it's down
* Import devices from dhcp.leases files instead/complementary to using PiHole or arp-scans
* Creating ad-hoc UI tables from existing data in the PiAlert database, e.g. to show all open ports on devices, to list devices that disconnected in the last hour, etc.
* Using other device discovery methods on the network and importing the data as new devices
* Creating a script to create FAKE devices based on user input via custom settings
* ...at this point the limitation is mostly the creativity than the capability (there might be edge cases and need to support more form controls for user input off custom settings, but you probably get the idea)

If you wish to develop a plugin, please check the existing plugin structure. Once the settings are saved by the user they need to be removed from the `pialert.conf` file manually if you want to re-initialize them from the `config.json` of the plugin. 

Again, please read the below carefully if you'd like to contribute with a plugin yourself. This documentation file might be outdated, so double check the sample plugins as well. 

## ⚠ Disclaimer

Experimental feature used also to speed up development  and to make the app more maintainable. Follow the below very carefully and check example plugin(s) if you'd like to write one yourself. Plugin UI is not my priority right now, happy to approve PRs if you are interested in extending/improvintg the UI experience. Example improvements for the taking:

* Making the tables sortable/filterable
* Using the same approach to display table  data as in the Devices section (solves above)
* Adding form controls supported to display the data (Currently supported ones are listed in the section "UI settings in database_column_definitions" below)
* ...

## ❗ Known issues:

These issues will be hopefully fixed with time, so please don't report them. Instead, if you know how, feel free to investigate and submit a PR to fix the below. Keep the PRs small as it's easier to approve them:

* Existing plugin objects sometimes not interpreted correctly and a new object is created instead, resulting in duplicate entries.
* Occasional (experienced twice) hanging of processing plugin script file.
* UI displaying outdated values until the API endpoints get refreshed. 

## Plugin file structure overview 

> Folder name must be the same as the code name value in: `"code_name": "<value>"`
> Unique prefix needs to be unique compared to the other settings prefixes, e.g.: the prefix `APPRISE` is already in use. 

  | File | Required | Description | 
  |----------------------|----------------------|----------------------| 
  | `config.json` | yes | Contains the plugin configuration (manifest) including the settings available to the user. |
  | `script.py` |  yes (script) | The Python script itself |
  | `last_result.log` | yes (script) | The file used to interface between PiAlert and the plugin (script).  |
  | `script.log` | no | Logging output (recommended) |
  | `README.md` | no | Any setup considerations or overview (recommended) |

More on specifics below.

### Column order and values

  | Order | Represented Column | Required | Description | 
  |----------------------|----------------------|----------------------|----------------------| 
  | 0 | `Object_PrimaryID` | yes | The primary ID used to group Events under. |
  | 1 | `Object_SecondaryID` | no | Optional secondary ID to create a relationship beween other entities, such as a MAC address |
  | 2 | `DateTime` | yes | When the event occured in the format `2023-01-02 15:56:30` |
  | 3 | `Watched_Value1` | yes | A value that is watched and users can receive notifications if it changed compared to the previously saved entry. For example IP address |
  | 4 | `Watched_Value2` | no | As above |
  | 5 | `Watched_Value3` | no | As above  |
  | 6 | `Watched_Value4` | no | As above  |
  | 7 | `Extra` | no | Any other data you want to pass and display in PiAlert and the notifications |
  | 8 | `ForeignKey` | no | A foreign key that can be used to link to the parent object (usually a MAC address) |


# config.json structure

## Supported data sources

Currently only two data sources are supported:

- Script
- SQL query on the PiAlert database

You need to set the `data_source` to either `pialert-db-query` or `python-script`:

```json
"data_source":  "pialert-db-query"
```
Any of the above datasources have to return a "table" of the exact structure as outlined above.

### "data_source":  "python-script"

 If the datasource is set to `python-script` the `CMD` setting (that you specify in the `settings` array section in the `config.json`) needs to contain a executable linux command, that generates a `last_result.log` file. This file needs to be stored in the same folder as the plugin. 
 
 The content of the `last_result.log` file needs to contain the columns as defined in the "Column order and values" section above. The order of columns can't be changed. After every scan it should contain only the results from the latest scan/execution. 

- The format of the `last_result.log` is a `csv`-like file with the pipe `|` as a separator. 
- 9 (nine) values need to be supplied, so every line needs to contain 8 pipe separators. Empty values are represented by `null`.  
- Don't render "headers" for these "columns".
- Every scan result / event entry needs to be on a new line.
- You can find which "columns" need to be present, and if the value is required or optional, in the "Column order and values" section. 
- The order of these "columns" can't be changed.

### 👍 Python script.py tips

The [Undicoverables plugins `script.py` file](https://github.com/jokob-sk/Pi.Alert/blob/main/pialert/plugins/undiscoverables/script.py) is a good and simple example to start with if you are considering creating a custom plugin. It uses the [`plugin_helper.py` library](https://github.com/jokob-sk/Pi.Alert/blob/main/pialert/plugins/plugin_helper.py) that significantly simplifies the creation of your custom script.

#### last_result.log examples

Valid CSV:

```csv

https://www.google.com|null|2023-01-02 15:56:30|200|0.7898|null|null|null|null
https://www.duckduckgo.com|192.168.0.1|2023-01-02 15:56:30|200|0.9898|null|null|Best search engine|ff:ee:ff:11:ff:11

```

Invalid CSV with different errors on each line:

```csv

https://www.google.com|null|2023-01-02 15:56:30|200|0.7898||null|null|null
https://www.duckduckgo.com|null|2023-01-02 15:56:30|200|0.9898|null|null|Best search engine|
|https://www.duckduckgo.com|null|2023-01-02 15:56:30|200|0.9898|null|null|Best search engine|null
null|192.168.1.1|2023-01-02 15:56:30|200|0.9898|null|null|Best search engine
https://www.duckduckgo.com|192.168.1.1|2023-01-02 15:56:30|null|0.9898|null|null|Best search engine
https://www.google.com|null|2023-01-02 15:56:30|200|0.7898|||
https://www.google.com|null|2023-01-02 15:56:30|200|0.7898|

```

### "data_source":  "pialert-db-query"

If the datasource is set to `pialert-db-query` the `CMD` setting needs to contain a SQL query rendering the columns as defined in the "Column order and values" section above. The order of columns is important. 

This SQL query is executed on the `pialert.db` SQLite database file. 

#### Examples

SQL query example:

```SQL
SELECT  dv.dev_Name as Object_PrimaryID, 
    cast(dv.dev_LastIP as VARCHAR(100)) || ':' || cast( SUBSTR(ns.Port ,0, INSTR(ns.Port , '/')) as VARCHAR(100)) as Object_SecondaryID,  
    datetime() as DateTime,  
    ns.Service as Watched_Value1,        
    ns.State as Watched_Value2,
    'null' as Watched_Value3,
    'null' as Watched_Value4,
    ns.Extra as Extra,
    dv.dev_MAC as ForeignKey 
FROM 
    (SELECT * FROM Nmap_Scan) ns 
LEFT JOIN 
    (SELECT dev_Name, dev_MAC, dev_LastIP FROM Devices) dv 
ON ns.MAC = dv.dev_MAC
```

Required `CMD` setting example with above query (you can set `"type": "label"` if you want it to make uneditable in the UI):

```json
{
            "function": "CMD",
            "type": "text",
            "default_value":"SELECT  dv.dev_Name as Object_PrimaryID, cast(dv.dev_LastIP as VARCHAR(100)) || ':' || cast( SUBSTR(ns.Port ,0, INSTR(ns.Port , '/')) as VARCHAR(100)) as Object_SecondaryID,  datetime() as DateTime,  ns.Service as Watched_Value1,        ns.State as Watched_Value2,        'null' as Watched_Value3,        'null' as Watched_Value4,        ns.Extra as Extra        FROM (SELECT * FROM Nmap_Scan) ns LEFT JOIN (SELECT dev_Name, dev_MAC, dev_LastIP FROM Devices) dv   ON ns.MAC = dv.dev_MAC",
            "options": [],
            "localized": ["name", "description"],
            "name" : [{
                "language_code":"en_us",
                "string" : "SQL to run"
            }],
            "description": [{
                "language_code":"en_us",
                "string" : "This SQL query is used to populate the coresponding UI tables under the Plugins section."
            }]
        }
```

### Mapping the plugin results into a database table

PiAlert will take the results of the plugin execution and insert these results into a database table, if a plugin contains the property `"mapped_to_table"` in the `config.json` root. The mapping of the columns is defined in the `database_column_definitions` array.

This approach is used to implement the `DHCPLSS` plugin. The script parses all supplied "dhcp.leases" files, get's the results in the generic table format outlined in the "Column order and values" section above and takes individual values and inserts them into the `"DHCP_Leases"` database table in the PiAlert database. All this is achieved by:

1) Specifying the database table into which the results are inserted by defining `"mapped_to_table": "DHCP_Leases"` in the root of the `config.json` file as shown below:

```json
{
    "code_name": "dhcp_leases",
    "unique_prefix": "DHCPLSS",
    ...
    "data_source":  "python-script",
    "localized": ["display_name", "description", "icon"],
    "mapped_to_table": "DHCP_Leases",    
    ...
}
```
2) Defining the target column with the `mapped_to_column` property for individual columns in the `database_column_definitions` array of the `config.json` file. For example in the `DHCPLSS` plugin, I needed to map the value of the `Object_PrimaryID` column returned by the plugin, to the `DHCP_MAC` column in the PiAlert database `DHCP_Leases` table. Notice the  `"mapped_to_column": "DHCP_MAC"` key-value pair in the sample below.

```json
{
            "column": "Object_PrimaryID",
            "mapped_to_column": "DHCP_MAC", 
            "css_classes": "col-sm-2",
            "show": true,
            "type": "devicemac",            
            "default_value":"",
            "options": [],
            "localized": ["name"],
            "name":[{
                "language_code":"en_us",
                "string" : "MAC address"
                }]
        }
```

3)  That's it. PiAlert takes care of the rest. It loops thru the objects discovered by the plugin, takes the results line, by line and inserts them into the database table specified in `"mapped_to_table"`. The columns are translated from the generic plugin columns to the target table via the `"mapped_to_column"` property in the column definitions.

#### params

The `params` array in the `config.json` is used to enable the user to change the parameters of the executed script. For example, the user wants to monitor a specific URL. 

##### Example:

Passing user defined settings to a command. Let's say, you want to have a script, that is called with a user-defined parameter called `urls`: 

```bash
root@server# python3 /home/pi/pialert/pialert/plugins/website_monitor/script.py urls=https://google.com,https://duck.com
```

* You can allow the user to add URLs to a setting with the `function` property set to a custom name, such as `urls_to_check` (this is not a reserved name from the section "Supported settings `function` values" below). 
* You specify the parameter `urls` in the `params` section of the `config.json` the following way (`WEBMON_` is the plugin prefix automatically added to all the settings):
```json
{
    "params" : [
        {
            "name"  : "urls",
            "type"  : "setting",
            "value" : "WEBMON_urls_to_check"
        }]
}
```
* Then you use this setting as an input parameter for your command in the `CMD` setting. Notice `urls={urls}` in the below json:

```json
 {
            "function": "CMD",
            "type": "text",
            "default_value":"python3 /home/pi/pialert/pialert/plugins/website_monitor/script.py urls={urls}",
            "options": [],
            "localized": ["name", "description"],
            "name" : [{
                "language_code":"en_us",
                "string" : "Command"
            }],
            "description": [{
                "language_code":"en_us",
                "string" : "Command to run"
            }]
        }
```

During script execution, the app will take the command `"python3 /home/pi/pialert/pialert/plugins/website_monitor/script.py urls={urls}"`, take the `{urls}` wildcard and replace it by with the value from the `WEBMON_urls_to_check` setting. This is because:

1) The app checks the `params` entries
2) It finds `"name"  : "urls"`
3) Checks the type of the `urls` params and finds `"type"  : "setting"`
4) Gets the setting name from  `"value" : "WEBMON_urls_to_check"` 
   - IMPORTANT: in the `config.json` this setting is identified by `"function":"urls_to_check"`, not `"function":"WEBMON_urls_to_check"`
   - You can also use a global setting, or a setting from a different plugin  
5) The app gets the user defined value from the setting with the code name `WEBMON_urls_to_check`
   - let's say the setting with the code name  `WEBMON_urls_to_check` contains 2 values entered by the user: 
   - `WEBMON_urls_to_check=['https://google.com','https://duck.com']`
6) The app takes the value from `WEBMON_urls_to_check` and replaces the `{urls}` wildcard in the setting where `"function":"CMD"`, so you go from:
   - `python3 /home/pi/pialert/pialert/plugins/website_monitor/script.py urls={urls}`
   - to
   - `python3 /home/pi/pialert/pialert/plugins/website_monitor/script.py urls=https://google.com,https://duck.com` 

Below are some general additional notes, when definig `params`: 

- `"name":"name_value"` - is used as a wildcard replacement in the `CMD` setting value by using curly brackets `{name_value}`. The wildcard is replaced by the result of the `"value" : "param_value"` and `"type":"type_value"` combo configuration below.
- `"type":"<sql|setting>"` - is used to specify the type of the params, currently only 2 supported (`sql`,`setting`).
  - `"type":"sql"` - will execute the SQL query specified in the `value` property. The sql query needs to return only one column. The column is flattened and separated by commas (`,`), e.g: `SELECT dev_MAC from DEVICES` -> `Internet,74:ac:74:ac:74:ac,44:44:74:ac:74:ac`. This is then used to replace the wildcards in the `CMD` setting.  
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

You can have any `"function": "my_custom_name"` custom name, however, the ones listed below have a specific functionality attached to them. If you use a custom name, then the setting is mostly used as an input parameter for the `params` section.

- `RUN` - (required) Specifies when the service is executed
    - Supported Options: "disabled", "once", "schedule" (if included then a `RUN_SCHD` setting needs to be specified), "always_after_scan", "on_new_device"
- `RUN_SCHD` - (required if you include the above `RUN` function) Cron-like scheduling used if the `RUN` setting set to `schedule`
- `CMD` - (required) What command should be executed. 
- `API_SQL` - (optional) Generates a `table_` + code_name  + `.json` file as per [API docs](https://github.com/jokob-sk/Pi.Alert/blob/main/docs/API.md).
- `RUN_TIMEOUT` - (optional) Max execution time of the script. If not specified a default value of 10 seconds is used to prevent hanging.
- `WATCH` - (optional) Which database columns are watched for changes for this particular plugin. If not specified no notifications are sent. 
- `REPORT_ON` - (optional) Send a notification only on these statuses. Supported options are: 
  - `new` means a new unique (unique combination of PrimaryId and SecondaryId) object was discovered. 
  - `watched-changed` - means that selected `Watched_ValueN` columns changed
  - `watched-not-changed` - reports even on events where selected `Watched_ValueN` did not change


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
##### UI settings in database_column_definitions

The UI will adjust how columns are displayed in the UI based on the definition of the `database_column_definitions` object. Thease are the supported form controls and related functionality:

- Only columns with `"show": true` and also with at least an English translation will be shown in the UI.
- Supported types: `label`, `text`, `threshold`, `replace`, `deviceip`, `devicemac`, `url`. Check for details below, how columns behave based on the type.
  - `label` makes a column display only
  - `text` makes a column editable and a save icon is displayed next to it.
  - See below for information on `threshold`, `replace`
- The `options` property is used in conjunction with these types:
  - `threshold` - The `options` array contains objects from lowest `maximum` to highest with corresponding `hexColor` used for the value background color if it's less than the specified `maximum`, but more than the previous one in the `options` array
  - `replace` - The `options` array contains objects with an `equals` property, that is compared to the "value" and if the values are the same, the string in `replacement` is displayed in the UI instead of the actual "value"
- `devicemac` - The value is considered to be a mac address and a link pointing to the device with the given mac address is generated.
- `deviceip` - The value is considered to be an IP address and a link pointing to the device with the given IP is generated. The IP is cheked against the last detected IP addresses and translated into a mac address that is then used for the link itself.
- `url` - The value is considered to be a url so a link is generated.


```json
{
            "column": "Watched_Value1",
            "css_classes": "col-sm-2",
            "show": true,
            "type": "threshold",            
            "default_value":"",
            "options": [
                {
                    "maximum": 199,
                    "hexColor": "#792D86"                
                },
                {
                    "maximum": 299,
                    "hexColor": "#5B862D"
                },
                {
                    "maximum": 399,
                    "hexColor": "#7D862D"
                },
                {
                    "maximum": 499,
                    "hexColor": "#BF6440"
                },
                {
                    "maximum": 599,
                    "hexColor": "#D33115"
                }
            ],
            "localized": ["name"],
            "name":[{
                "language_code":"en_us",
                "string" : "Status code"
                }]
        },        
        {
            "column": "Status",
            "show": true,
            "type": "replace",            
            "default_value":"",
            "options": [
                {
                    "equals": "watched-not-changed",
                    "replacement": "<i class='fa-solid fa-square-check'></i>"
                },
                {
                    "equals": "watched-changed",
                    "replacement": "<i class='fa-solid fa-triangle-exclamation'></i>"
                },
                {
                    "equals": "new",
                    "replacement": "<i class='fa-solid fa-circle-plus'></i>"
                }
            ],
            "localized": ["name"],
            "name":[{
                "language_code":"en_us",
                "string" : "Status"
                }]
        }
```



[screen1]: https://raw.githubusercontent.com/jokob-sk/Pi.Alert/main/docs/img/plugins.png                "Screen 1"
[screen2]: https://raw.githubusercontent.com/jokob-sk/Pi.Alert/main/docs/img/plugins_settings.png       "Screen 2"
[screen3]: https://raw.githubusercontent.com/jokob-sk/Pi.Alert/main/docs/img/plugins_json_settings.png  "Screen 3"
[screen4]: https://raw.githubusercontent.com/jokob-sk/Pi.Alert/main/docs/img/plugins_json_ui.png        "Screen 4"
