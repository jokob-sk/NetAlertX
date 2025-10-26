# Creating a custom plugin

NetAlertX comes with a plugin system to feed events from third-party scripts into the UI and then send notifications, if desired. The highlighted core functionality this plugin system supports, is:

* dynamic creation of a simple UI to interact with the discovered objects,
* filtering of displayed values in the Devices UI
* surface settings of plugins in the UI, 
* different column types for reported values to e.g. link back to a device
* import objects into existing NetAlertX database tables 

> (Currently, update/overwriting of existing objects is only supported for devices via the `CurrentScan` table.)

> [!NOTE]
> For a high-level overview of how the `config.json` is used and it's lifecycle check the [config.json Lifecycle in NetAlertX Guide](PLUGINS_DEV_CONFIG.md).

### 🎥 Watch the video:

> [!TIP]
> Read this guide [Development environment setup guide](./DEV_ENV_SETUP.md) to set up your local environment for development. 👩‍💻

[![Watch the video](./img/YouTube_thumbnail.png)](https://youtu.be/cdbxlwiWhv8)

### 📸 Screenshots

| ![Screen 1][screen1] | ![Screen 2][screen2] | ![Screen 3][screen3] | 
|----------------------|----------------------| ----------------------| 
| ![Screen 4][screen4] |  ![Screen 5][screen5] | 

## Use cases

Example use cases for plugins could be:

* Monitor a web service and alert me if it's down
* Import devices from dhcp.leases files instead/complementary to using PiHole or arp-scans
* Creating ad-hoc UI tables from existing data in the NetAlertX database, e.g. to show all open ports on devices, to list devices that disconnected in the last hour, etc.
* Using other device discovery methods on the network and importing the data as new devices
* Creating a script to create FAKE devices based on user input via custom settings
* ...at this point the limitation is mostly the creativity rather than the capability (there might be edge cases and a need to support more form controls for user input off custom settings, but you probably get the idea)

If you wish to develop a plugin, please check the existing plugin structure. Once the settings are saved by the user they need to be removed from the `app.conf` file manually if you want to re-initialize them from the `config.json` of the plugin. 

## ⚠ Disclaimer

Please read the below carefully if you'd like to contribute with a plugin yourself. This documentation file might be outdated, so double-check the sample plugins as well. 

## Plugin file structure overview 

> ⚠️Folder name must be the same as the code name value in: `"code_name": "<value>"`
> Unique prefix needs to be unique compared to the other settings prefixes, e.g.: the prefix `APPRISE` is already in use. 

  | File | Required (plugin type) | Description | 
  |----------------------|----------------------|----------------------| 
  | `config.json` | yes | Contains the plugin configuration (manifest) including the settings available to the user. |
  | `script.py` |  no | The Python script itself. You may call any valid linux command.  |
  | `last_result.<prefix>.log` | no | The file used to interface between NetAlertX and the plugin. Required for a script plugin if you want to feed data into the app. Stored in the `/api/log/plugins/` |
  | `script.log` | no | Logging output (recommended) |
  | `README.md` | yes | Any setup considerations or overview  |

More on specifics below.

### Column order and values (plugins interface contract)

> [!IMPORTANT] 
> Spend some time reading and trying to understand the below table. This is the interface between the Plugins and the core application. The application expets 9 or 13 values The first 9 values are mandatory. The next 4 values (`HelpVal1` to `HelpVal4`) are optional. However, if you use any of these optional values (e.g., `HelpVal1`), you need to supply all optional values (e.g., `HelpVal2`, `HelpVal3`, and `HelpVal4`). If a value is not used, it should be padded with `null`.

  | Order | Represented Column | Value Required | Description | 
  |----------------------|----------------------|----------------------|----------------------| 
  | 0 | `Object_PrimaryID` | yes | The primary ID used to group Events under. |
  | 1 | `Object_SecondaryID` | no | Optional secondary ID to create a relationship beween other entities, such as a MAC address |
  | 2 | `DateTime` | yes | When the event occured in the format `2023-01-02 15:56:30` |
  | 3 | `Watched_Value1` | yes | A value that is watched and users can receive notifications if it changed compared to the previously saved entry. For example IP address |
  | 4 | `Watched_Value2` | no | As above |
  | 5 | `Watched_Value3` | no | As above  |
  | 6 | `Watched_Value4` | no | As above  |
  | 7 | `Extra` | no | Any other data you want to pass and display in NetAlertX and the notifications |
  | 8 | `ForeignKey` | no | A foreign key that can be used to link to the parent object (usually a MAC address) |
  | 9 | `HelpVal1` | no | (optional) A helper value |
  | 10 | `HelpVal2` | no | (optional) A helper value |
  | 11 | `HelpVal3` | no | (optional) A helper value |
  | 12 | `HelpVal4` | no | (optional) A helper value |
  

> [!NOTE] 
> De-duplication is run once an hour on the `Plugins_Objects` database table and duplicate entries with the same value in columns `Object_PrimaryID`, `Object_SecondaryID`, `Plugin` (auto-filled based on `unique_prefix` of the plugin), `UserData` (can be populated with the `"type": "textbox_save"` column type) are removed.

# config.json structure

The `config.json` file is the manifest of the plugin. It contains mainly settings definitions and the mapping of Plugin objects to NetAlertX objects. 

## Execution order

The execution order is used to specify when a plugin is executed. This is useful if a plugin has access and surfaces more information than others. If a device is detected by 2 plugins and inserted into the `CurrentScan` table, the plugin with the higher priority (e.g.: `Level_0` is a higher priority than `Level_1`) will insert it's values first. These values (devices) will be then prioritized over any values inserted later.

```json
{
    "execution_order" : "Layer_0"
}
```

## Supported data sources

Currently, these data sources are supported (valid `data_source` value). 

| Name | `data_source` value | Needs to return a "table"* | Overview (more details on this page below) | 
|----------------------|----------------------|----------------------|----------------------| 
| Script | `script` | no | Executes any linux command in the `CMD` setting. |
| NetAlertX DB query | `app-db-query` | yes | Executes a SQL query on the NetAlertX database in the `CMD` setting. |
| Template | `template` | no | Used to generate internal settings, such as default values. |
| External SQLite DB query | `sqlite-db-query` | yes | Executes a SQL query from the `CMD` setting on an external SQLite database mapped in the `DB_PATH` setting.  |
| Plugin type | `plugin_type` | no | Specifies the type of the plugin and in which section the Plugin settings are displayed ( one of `general/system/scanner/other/publisher` ). | 

> * "Needs to return a "table" means that the application expects a `last_result.<prefix>.log` file with some results. It's not a blocker, however warnings in the `app.log` might be logged.

> 🔎Example
>```json
>"data_source":  "app-db-query"
>```
If you want to display plugin objects or import devices into the app, data sources have to return a "table" of the exact structure as outlined above.

You can show or hide the UI on the "Plugins" page and "Plugins" tab for a plugin on devices via the `show_ui` property:

> 🔎Example
>```json
> "show_ui": true,
> ```

### "data_source":  "script"

 If the `data_source` is set to `script` the `CMD` setting (that you specify in the `settings` array section in the `config.json`) contains an executable Linux command, that usually generates a `last_result.<prefix>.log` file (not required if you don't import any data into the app). The `last_result.<prefix>.log` file needs to be saved in `/api/log/plugins`. 

> [!IMPORTANT]
> A lot of the work is taken care of by the [`plugin_helper.py` library](/front/plugins/plugin_helper.py). You don't need to manage the `last_result.<prefix>.log` file if using the helper objects. Check other `script.py` of other plugins for details.
 
 The content of the `last_result.<prefix>.log` file needs to contain the columns as defined in the "Column order and values" section above. The order of columns can't be changed. After every scan it should contain only the results from the latest scan/execution. 

- The format of the `last_result.<prefix>.log` is a `csv`-like file with the pipe `|` as a separator. 
- 9 (nine) values need to be supplied, so every line needs to contain 8 pipe separators. Empty values are represented by `null`.  
- Don't render "headers" for these "columns".
Every scan result/event entry needs to be on a new line.
- You can find which "columns" need to be present, and if the value is required or optional, in the "Column order and values" section. 
- The order of these "columns" can't be changed.

#### 🔎 last_result.prefix.log examples

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

### "data_source":  "app-db-query"

If the `data_source` is set to `app-db-query`, the `CMD` setting needs to contain a SQL query rendering the columns as defined in the "Column order and values" section above. The order of columns is important. 

This SQL query is executed on the `app.db` SQLite database file. 

>  🔎Example
> 
> SQL query example:
> 
> ```SQL
> SELECT  dv.devName as Object_PrimaryID, 
>     cast(dv.devLastIP as VARCHAR(100)) || ':' || cast( SUBSTR(ns.Port ,0, INSTR(ns.Port , '/')) as VARCHAR(100)) as Object_SecondaryID,  
>     datetime() as DateTime,  
>     ns.Service as Watched_Value1,        
>     ns.State as Watched_Value2,
>     'null' as Watched_Value3,
>     'null' as Watched_Value4,
>     ns.Extra as Extra,
>     dv.devMac as ForeignKey 
> FROM 
>     (SELECT * FROM Nmap_Scan) ns 
> LEFT JOIN 
>     (SELECT devName, devMac, devLastIP FROM Devices) dv 
> ON ns.MAC = dv.devMac
> ```
> 
> Required `CMD` setting example with above query (you can set `"type": "label"` if you want it to make uneditable in the UI):
> 
> ```json
> {
>             "function": "CMD",
>            "type": {"dataType":"string", "elements": [{"elementType" : "input", "elementOptions" : [] ,"transformers": []}]},
>            "default_value":"SELECT  dv.devName as Object_PrimaryID, cast(dv.devLastIP as VARCHAR(100)) || ':' || cast( SUBSTR(ns.Port ,0, INSTR(ns.Port , '/')) as VARCHAR(100)) as Object_SecondaryID,  datetime() as DateTime,  ns.Service as Watched_Value1,        ns.State as Watched_Value2,        'null' as Watched_Value3,        'null' as Watched_Value4,        ns.Extra as Extra        FROM (SELECT * FROM Nmap_Scan) ns LEFT JOIN (SELECT devName, devMac, devLastIP FROM Devices) dv   ON ns.MAC = dv.devMac",
>            "options": [],
>            "localized": ["name", "description"],
>            "name" : [{
>                "language_code":"en_us",
>                "string" : "SQL to run"
>            }],
>             "description": [{
>                 "language_code":"en_us",
>                 "string" : "This SQL query is used to populate the coresponding UI tables under the Plugins section."
>             }]
>         }
> ```

### "data_source":  "template"

In most cases, it is used to initialize settings. Check the `newdev_template` plugin for details.

### "data_source":  "sqlite-db-query"

You can execute a SQL query on an external database connected to the current NetAlertX database via a temporary `EXTERNAL_<unique prefix>.` prefix. 

For example for `PIHOLE` (`"unique_prefix": "PIHOLE"`) it is `EXTERNAL_PIHOLE.`. The external SQLite database file has to be mapped in the container to the path specified in the `DB_PATH` setting:

>  🔎Example
>
>```json
>  ...
>{
>        "function": "DB_PATH",
>        "type": {"dataType":"string", "elements": [{"elementType" : "input", "elementOptions" : [{"readonly": "true"}] ,"transformers": []}]},
>        "default_value":"/etc/pihole/pihole-FTL.db",
>        "options": [],
>        "localized": ["name", "description"],
>        "name" : [{
>            "language_code":"en_us",
>            "string" : "DB Path"
>        }],
>        "description": [{
>            "language_code":"en_us",
>            "string" : "Required setting for the <code>sqlite-db-query</code> plugin type. Is used to mount an external SQLite database and execute the SQL query stored in the <code>CMD</code> setting."
>        }]    
>    }
>  ...
>```

The actual SQL query you want to execute is then stored as a `CMD` setting, similar to a Plugin of the `app-db-query` plugin type. The format has to adhere to the format outlined in the "Column order and values" section above. 

>  🔎Example
>
> Notice the `EXTERNAL_PIHOLE.` prefix.
>
>```json
>{
>      "function": "CMD",
>      "type": {"dataType":"string", "elements": [{"elementType" : "input", "elementOptions" : [] ,"transformers": []}]},
>      "default_value":"SELECT hwaddr as Object_PrimaryID, cast('http://' || (SELECT ip FROM EXTERNAL_PIHOLE.network_addresses WHERE network_id = id ORDER BY lastseen DESC, ip LIMIT 1) as VARCHAR(100)) || ':' || cast( SUBSTR((SELECT name FROM EXTERNAL_PIHOLE.network_addresses WHERE network_id = id ORDER BY lastseen DESC, ip LIMIT 1), 0, INSTR((SELECT name FROM EXTERNAL_PIHOLE.network_addresses WHERE network_id = id ORDER BY lastseen DESC, ip LIMIT 1), '/')) as VARCHAR(100)) as Object_SecondaryID, datetime() as DateTime, macVendor as Watched_Value1, lastQuery as Watched_Value2, (SELECT name FROM EXTERNAL_PIHOLE.network_addresses WHERE network_id = id ORDER BY lastseen DESC, ip LIMIT 1) as Watched_Value3, 'null' as Watched_Value4, '' as Extra, hwaddr as ForeignKey FROM EXTERNAL_PIHOLE.network WHERE hwaddr NOT LIKE 'ip-%' AND hwaddr <> '00:00:00:00:00:00';            ",
>      "options": [],
>      "localized": ["name", "description"],
>      "name" : [{
>          "language_code":"en_us",
>          "string" : "SQL to run"
>      }],
>      "description": [{
>          "language_code":"en_us",
>          "string" : "This SQL query is used to populate the coresponding UI tables under the Plugins section. This particular one selects data from a mapped PiHole SQLite database and maps it to the corresponding Plugin columns."
>      }]
>  }
>  ```

## 🕳 Filters

Plugin entries can be filtered in the UI based on values entered into filter fields. The `txtMacFilter` textbox/field contains the Mac address of the currently viewed device, or simply a Mac address that's available in the `mac` query string (`<url>?mac=aa:22:aa:22:aa:22:aa`).

  | Property | Required | Description | 
  |----------------------|----------------------|----------------------| 
  | `compare_column` | yes | Plugin column name that's value is used for comparison (**Left** side of the equation) |
  | `compare_operator` |  yes | JavaScript comparison operator |
  | `compare_field_id` | yes | The `id` of a input text field containing a value is used for comparison (**Right** side of the equation)|
  | `compare_js_template` | yes | JavaScript code used to convert left and right side of the equation. `{value}` is replaced with input values. |
  | `compare_use_quotes` | yes | If `true` then the end result of the `compare_js_template` i swrapped in `"` quotes. Use to compare strings. |
  
  Filters are only applied if a filter is specified, and the `txtMacFilter` is not `undefined`, or empty (`--`).

> 🔎Example:
> 
> ```json
>     "data_filters": [
>         {
>             "compare_column" : "Object_PrimaryID",
>             "compare_operator" : "==",
>             "compare_field_id": "txtMacFilter",
>             "compare_js_template": "'{value}'.toString()", 
>             "compare_use_quotes": true 
>         }
>     ],
> ```
>
>1. On the `pluginsCore.php` page is an input field with the id `txtMacFilter`:
>
>```html
><input class="form-control" id="txtMacFilter" type="text" value="--">
>```
>
>2. This input field is initialized via the `&mac=` query string.
>
>3. The app then proceeds to use this Mac value from this field and compares it to the value of the `Object_PrimaryID` database field. The `compare_operator` is `==`.
>
>4. Both values, from the database field `Object_PrimaryID` and from the `txtMacFilter` are wrapped and evaluated with the `compare_js_template`, that is `'{value}.toString()'`.
>
>5. `compare_use_quotes` is set to `true` so `'{value}'.toString()` is wrappe dinto `"` quotes.
>
>6. This results in for example this code: 
>
>```javascript
>    // left part of the expression coming from compare_column and right from the input field
>    // notice the added quotes ()") around the left and right part of teh expression
>    "eval('ac:82:ac:82:ac:82".toString()')" == "eval('ac:82:ac:82:ac:82".toString()')"
>```
>


### 🗺 Mapping the plugin results into a database table

Plugin results are always inserted into the standard `Plugin_Objects` database table. Optionally, NetAlertX can take the results of the plugin execution, and insert these results into an additional database table. This is enabled by with the property `"mapped_to_table"` in the `config.json` file. The mapping of the columns is defined in the `database_column_definitions` array.

> [!NOTE] 
> If results are mapped to the `CurrentScan` table, the data is then included into the regular scan loop, so for example notification for devices are sent out.  


>🔍 Example:
>
>For example, this approach is used to implement the `DHCPLSS` plugin. The script parses all supplied "dhcp.leases" files, gets the results in the generic table format outlined in the "Column order and values" section above, takes individual values, and inserts them into the `CurrentScan` database table in the NetAlertX database. All this is achieved by:
>
>1. Specifying the database table into which the results are inserted by defining `"mapped_to_table": "CurrentScan"` in the root of the `config.json` file as shown below:
>
>```json
>{
>    "code_name": "dhcp_leases",
>    "unique_prefix": "DHCPLSS",
>    ...
>    "data_source":  "script",
>    "localized": ["display_name", "description", "icon"],
>    "mapped_to_table": "CurrentScan",    
>    ...
>}
>```
>2. Defining the target column with the `mapped_to_column` property for individual columns in the `database_column_definitions` array of the `config.json` file. For example in the `DHCPLSS` plugin, I needed to map the value of the `Object_PrimaryID` column returned by the plugin, to the `cur_MAC` column in the NetAlertX database table `CurrentScan`. Notice the  `"mapped_to_column": "cur_MAC"` key-value pair in the sample below.
>
>```json
>{
>            "column": "Object_PrimaryID",
>            "mapped_to_column": "cur_MAC", 
>            "css_classes": "col-sm-2",
>            "show": true,
>            "type": "device_mac",            
>            "default_value":"",
>            "options": [],
>            "localized": ["name"],
>            "name":[{
>                "language_code":"en_us",
>                "string" : "MAC address"
>                }]
>        }
>```
>
>3.  That's it. The app takes care of the rest. It loops thru the objects discovered by the plugin, takes the results line-by-line, and inserts them into the database table specified in `"mapped_to_table"`. The columns are translated from the generic plugin columns to the target table columns via the `"mapped_to_column"` property in the column definitions.

> [!NOTE] 
> You can create a column mapping with a default value via the `mapped_to_column_data` property. This means that the value of the given column will always be this value. That also means that the `"column": "NameDoesntMatter"` is not important as there is no database source column. 


>🔍 Example:
>
>```json
>{
>            "column": "NameDoesntMatter",
>            "mapped_to_column": "cur_ScanMethod",
>            "mapped_to_column_data": {
>                "value": "DHCPLSS"                
>            },  
>            "css_classes": "col-sm-2",
>            "show": true,
>            "type": "device_mac",            
>            "default_value":"",
>            "options": [],
>            "localized": ["name"],
>            "name":[{
>                "language_code":"en_us",
>                "string" : "MAC address"
>                }]
>        }
>```

#### params

> [!IMPORTANT] 
> An esier way to access settings in scripts is the `get_setting_value` method.
> ```python
> from helper import get_setting_value
>
>   ...
>   NTFY_TOPIC = get_setting_value('NTFY_TOPIC')
>   ...
>
> ``` 

The `params` array in the `config.json` is used to enable the user to change the parameters of the executed script. For example, the user wants to monitor a specific URL. 

> 🔎 Example:
> Passing user-defined settings to a command. Let's say, you want to have a script, that is called with a user-defined parameter called `urls`: 
> 
> ```bash
> root@server# python3 /app/front/plugins/website_monitor/script.py urls=https://google.com,https://duck.com
> ```

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
            "type": {"dataType":"string", "elements": [{"elementType" : "input", "elementOptions" : [] ,"transformers": []}]},
            "default_value":"python3 /app/front/plugins/website_monitor/script.py urls={urls}",
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

During script execution, the app will take the command `"python3 /app/front/plugins/website_monitor/script.py urls={urls}"`, take the `{urls}` wildcard and replace it with the value from the `WEBMON_urls_to_check` setting. This is because:

1. The app checks the `params` entries
2. It finds `"name"  : "urls"`
3. Checks the type of the `urls` params and finds `"type"  : "setting"`
4. Gets the setting name from  `"value" : "WEBMON_urls_to_check"` 
   - IMPORTANT: in the `config.json` this setting is identified by `"function":"urls_to_check"`, not `"function":"WEBMON_urls_to_check"`
   - You can also use a global setting, or a setting from a different plugin  
5. The app gets the user defined value from the setting with the code name `WEBMON_urls_to_check`
   - let's say the setting with the code name  `WEBMON_urls_to_check` contains 2 values entered by the user: 
   - `WEBMON_urls_to_check=['https://google.com','https://duck.com']`
6. The app takes the value from `WEBMON_urls_to_check` and replaces the `{urls}` wildcard in the setting where `"function":"CMD"`, so you go from:
   - `python3 /app/front/plugins/website_monitor/script.py urls={urls}`
   - to
   - `python3 /app/front/plugins/website_monitor/script.py urls=https://google.com,https://duck.com` 

Below are some general additional notes, when defining `params`: 

- `"name":"name_value"` - is used as a wildcard replacement in the `CMD` setting value by using curly brackets `{name_value}`. The wildcard is replaced by the result of the `"value" : "param_value"` and `"type":"type_value"` combo configuration below.
- `"type":"<sql|setting>"` - is used to specify the type of the params, currently only 2 supported (`sql`,`setting`).
  - `"type":"sql"` - will execute the SQL query specified in the `value` property. The sql query needs to return only one column. The column is flattened and separated by commas (`,`), e.g: `SELECT devMac from DEVICES` -> `Internet,74:ac:74:ac:74:ac,44:44:74:ac:74:ac`. This is then used to replace the wildcards in the `CMD` setting.  
  - `"type":"setting"` - The setting code name. A combination of the value from `unique_prefix` + `_` + `function` value, or otherwise the code name you can find in the Settings page under the Setting display name, e.g. `PIHOLE_RUN`. 
- `"value": "param_value"` - Needs to contain a setting code name or SQL query without wildcards.
- `"timeoutMultiplier" : true` - used to indicate if the value should multiply the max timeout for the whole script run by the number of values in the given parameter.
- `"base64": true` - use base64 encoding to pass the value to the script (e.g. if there are spaces)


> 🔎Example:
> 
> ```json
> {
>     "params" : [{
>            "name"              : "ips",
>            "type"              : "sql",
>            "value"             : "SELECT devLastIP from DEVICES",
>            "timeoutMultiplier" : true
>        },
>        {
>            "name"              : "macs",
>            "type"              : "sql",
>            "value"             : "SELECT devMac from DEVICES"            
>        },
>        {
>            "name"              : "timeout",
>            "type"              : "setting",
>            "value"             : "NMAP_RUN_TIMEOUT"
>        },
>        {
>            "name"              : "args",
>            "type"              : "setting",
>            "value"             : "NMAP_ARGS",
>            "base64"            : true
>        }]
> }
> ```


#### ⚙ Setting object structure

> [!NOTE] 
> The settings flow and when Plugin specific settings are applied is described under the [Settings system](./SETTINGS_SYSTEM.md).

Required attributes are:

| Property | Description |
| -------- | ----------- |
| `"function"` | Specifies the function the setting drives or a simple unique code name. See Supported settings function values for options. |
| `"type"` | Specifies the form control used for the setting displayed in the Settings page and what values are accepted. Supported options include: |
|  | - `{"dataType":"string", "elements": [{"elementType" : "input", "elementOptions" : [{"type":"password"}] ,"transformers": ["sha256"]}]}` |
| `"localized"` | A list of properties on the current JSON level that need to be localized. |
| `"name"` | Displayed on the Settings page. An array of localized strings. See Localized strings below. |
| `"description"` | Displayed on the Settings page. An array of localized strings. See Localized strings below. |
| (optional) `"events"` | Specifies whether to generate an execution button next to the input field of the setting. Supported values: |
|  | - `"test"` - For notification plugins testing |
|  | - `"run"` - Regular plugins testing |
| (optional) `"override_value"` | Used to determine a user-defined override for the setting. Useful for template-based plugins, where you can choose to leave the current value or override it with the value defined in the setting. (Work in progress) |
| (optional) `"events"` | Used to trigger the plugin. Usually used on the `RUN` setting. Not fully tested in all scenarios. Will show a play button next to the setting. After clicking, an event is generated for the backend in the `Parameters` database table to process the front-end event on the next run. |

### UI Component Types Documentation

This section outlines the structure and types of UI components, primarily used to build HTML forms or interactive elements dynamically. Each UI component has a `"type"` which defines its structure, behavior, and rendering options.

#### UI Component JSON Structure
The UI component is defined as a JSON object containing a list of `elements`. Each element specifies how it should behave, with properties like `elementType`, `elementOptions`, and any associated `transformers` to modify the data. The example below demonstrates how a component with two elements (`span` and `select`) is structured:

```json
{
      "function": "devIcon",
      "type": {
        "dataType": "string",
        "elements": [
          {
            "elementType": "span",
            "elementOptions": [
              { "cssClasses": "input-group-addon iconPreview" },
              { "getStringKey": "Gen_SelectToPreview" },
              { "customId": "NEWDEV_devIcon_preview" }
            ],
            "transformers": []
          },
          {
            "elementType": "select",
            "elementHasInputValue": 1,
            "elementOptions": [
              { "cssClasses": "col-xs-12" },
              {
                "onChange": "updateIconPreview(this)"
              },
              { "customParams": "NEWDEV_devIcon,NEWDEV_devIcon_preview" }
            ],
            "transformers": []
          }          
        ]
      }
}

```

### Rendering Logic

The code snippet provided demonstrates how the elements are iterated over to generate their corresponding HTML. Depending on the `elementType`, different HTML tags (like `<select>`, `<input>`, `<textarea>`, `<button>`, etc.) are created with the respective attributes such as `onChange`, `my-data-type`, and `class` based on the provided `elementOptions`. Events can also be attached to elements like buttons or select inputs.

### Key Element Types

- **`select`**: Renders a dropdown list. Additional options like `isMultiSelect` and event handlers (e.g., `onChange`) can be attached.
- **`input`**: Handles various types of input fields, including checkboxes, text, and others, with customizable attributes like `readOnly`, `placeholder`, etc.
- **`button`**: Generates clickable buttons with custom event handlers (`onClick`), icons, or labels.
- **`textarea`**: Creates a multi-line input box for text input.
- **`span`**: Used for inline text or content with customizable classes and data attributes.

Each element may also have associated events (e.g., running a scan or triggering a notification) defined under `Events`.

    
##### Supported settings `function` values

You can have any `"function": "my_custom_name"` custom name, however, the ones listed below have a specific functionality attached to them. 

| Setting | Description |
| ------- | ----------- |
| `RUN` | (required) Specifies when the service is executed. |
|  | Supported Options: |
|  | - "disabled" - do not run |
|  | - "once" - run on app start or on settings saved |
|  | - "schedule" - if included, then a `RUN_SCHD` setting needs to be specified to determine the schedule |
|  | - "always_after_scan" - run always after a scan is finished |
|  | - "before_name_updates" - run before device names are updated (for name discovery plugins) |
|  | - "on_new_device" - run when a new device is detected |
|  | - "before_config_save" - run before the config is marked as saved. Useful if your plugin needs to modify the `app.conf` file. |
| `RUN_SCHD` | (required if you include "schedule" in the above `RUN` function) Cron-like scheduling is used if the `RUN` setting is set to `schedule`. |
| `CMD` | (required) Specifies the command that should be executed. |
| `API_SQL` | (not implemented) Generates a `table_` + `code_name` + `.json` file as per [API docs](./API.md). |
| `RUN_TIMEOUT` | (optional) Specifies the maximum execution time of the script. If not specified, a default value of 10 seconds is used to prevent hanging. |
| `WATCH` | (optional) Specifies which database columns are watched for changes for this particular plugin. If not specified, no notifications are sent. |
| `REPORT_ON` | (optional) Specifies when to send a notification. Supported options are: |
|  | - `new` means a new unique (unique combination of PrimaryId and SecondaryId) object was discovered. |
|  | - `watched-changed` - means that selected `Watched_ValueN` columns changed |
|  | - `watched-not-changed` - reports even on events where selected `Watched_ValueN` did not change |
|  | - `missing-in-last-scan` - if the object is missing compared to previous scans |


> 🔎 Example:
> 
> ```json
> {
>     "function": "RUN",            
>     "type": {"dataType":"string", "elements": [{"elementType" : "select", "elementOptions" : [] ,"transformers": []}]},            
>     "default_value":"disabled",
>     "options": ["disabled", "once", "schedule", "always_after_scan", "on_new_device"],
>     "localized": ["name", "description"],
>     "name" :[{
>         "language_code":"en_us",
>         "string" : "When to run"
>     }],
>     "description": [{
>         "language_code":"en_us",
>         "string" : "Enable a regular scan of your services. If you select <code>schedule</code> the scheduling settings from below are applied. If you select <code>once</code> the scan is run only once on start of the application (container) for the time specified in <a href=\"#WEBMON_RUN_TIMEOUT\"><code>WEBMON_RUN_TIMEOUT</code> setting</a>."
>     }]
> }
> ```

##### 🌍Localized strings

- `"language_code":"<en_us|es_es|de_de>"`  - code name of the language string. Only these three are currently supported. At least the `"language_code":"en_us"` variant has to be defined. 
- `"string"`  - The string to be displayed in the given language.

> 🔎 Example:
> 
> ```json
> 
>     {
>         "language_code":"en_us",
>         "string" : "When to run"
>     }
> 
> ```

##### UI settings in database_column_definitions

The UI will adjust how columns are displayed in the UI based on the resolvers definition of the `database_column_definitions` object. These are the supported form controls and related functionality:

- Only columns with `"show": true` and also with at least an English translation will be shown in the UI.

| Supported Types | Description |
| -------------- | ----------- |
| `label` | Displays a column only. |
| `textarea_readonly` | Generates a read only text area and cleans up the text to display it somewhat formatted with new lines preserved. |
| See below for information on `threshold`, `replace`. | |
|  |  |
| `options` Property | Used in conjunction with types like `threshold`, `replace`, `regex`. |
| `options_params` Property | Used in conjunction with a `"options": "[{value}]"` template and `text.select`/`list.select`. Can specify SQL query (needs to return 2 columns `SELECT devName as name, devMac as id`) or Setting (not tested) to populate the dropdown. Check example below or have a look at the `NEWDEV` plugin `config.json` file. |
| `threshold` | The `options` array contains objects ordered from the lowest `maximum` to the highest. The corresponding `hexColor` is used for the value background color if it's less than the specified `maximum` but more than the previous one in the `options` array. |
| `replace` | The `options` array contains objects with an `equals` property, which is compared to the "value." If the values are the same, the string in `replacement` is displayed in the UI instead of the actual "value". |
| `regex` | Applies a regex to the value.  The `options` array contains objects with an `type` (must be set to `regex`) and `param` (must contain the regex itself) property. |
|  |  |
| Type Definitions |  |
| `device_mac` | The value is considered to be a MAC address, and a link pointing to the device with the given MAC address is generated. |
| `device_ip` | The value is considered to be an IP address. A link pointing to the device with the given IP is generated. The IP is checked against the last detected IP address and translated into a MAC address, which is then used for the link itself. |
| `device_name_mac` | The value is considered to be a MAC address, and a link pointing to the device with the given MAC is generated. The link label is resolved as the target device name. |
| `url` | The value is considered to be a URL, so a link is generated. |
| `textbox_save` | Generates an editable and saveable text box that saves values in the database. Primarily intended for the `UserData` database column in the `Plugins_Objects` table. |
| `url_http_https` | Generates two links with the `https` and `http` prefix as lock icons. |
| `eval` | Evaluates as JavaScript. Use the variable `value` to use the given column value as input (e.g. `'<b>${value}<b>'` (replace ' with ` in your code) ) |
            

> [!NOTE] 
> Supports chaining. You can chain multiple resolvers with `.`. For example `regex.url_http_https`. This will apply the `regex` resolver and then the `url_http_https` resolver.


```json
        "function": "devType",
        "type": {"dataType":"string", "elements": [{"elementType" : "select", "elementOptions" : [] ,"transformers": []}]},
        "maxLength": 30,
        "default_value": "",
        "options": ["{value}"],
        "options_params" : [
            {
                "name"  : "value",
                "type"  : "sql",
                "value" : "SELECT '' as id, '' as name UNION SELECT devType as id, devType as name FROM (SELECT devType FROM Devices UNION SELECT 'Smartphone' UNION SELECT 'Tablet' UNION SELECT 'Laptop' UNION SELECT 'PC' UNION SELECT 'Printer' UNION SELECT 'Server' UNION SELECT 'NAS' UNION SELECT 'Domotic' UNION SELECT 'Game Console' UNION SELECT 'SmartTV' UNION SELECT 'Clock' UNION SELECT 'House Appliance' UNION SELECT 'Phone' UNION SELECT 'AP' UNION SELECT 'Gateway' UNION SELECT 'Firewall' UNION SELECT 'Switch' UNION SELECT 'WLAN' UNION SELECT 'Router' UNION SELECT 'Other') AS all_devices ORDER BY id;"
            },
            {
                "name"  : "uilang",
                "type"  : "setting",
                "value" : "UI_LANG"
            }
        ]
```


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
        },
        {
            "column": "Watched_Value3",
            "css_classes": "col-sm-1",
            "show": true,
            "type": "regex.url_http_https",            
            "default_value":"",
            "options": [
                {
                    "type": "regex",
                    "param": "([\\d.:]+)"
                }          
            ],
            "localized": ["name"],
            "name":[{
                "language_code":"en_us",
                "string" : "HTTP/s links"
                },
	    	    {
                "language_code":"es_es",
                "string" : "N/A"
                }]
        }
```

[screen1]: https://raw.githubusercontent.com/jokob-sk/NetAlertX/main/docs/img/plugins.png                    "Screen 1"
[screen2]: https://raw.githubusercontent.com/jokob-sk/NetAlertX/main/docs/img/plugins_settings.png           "Screen 2"
[screen3]: https://raw.githubusercontent.com/jokob-sk/NetAlertX/main/docs/img/plugins_json_settings.png      "Screen 3"
[screen4]: https://raw.githubusercontent.com/jokob-sk/NetAlertX/main/docs/img/plugins_json_ui.png            "Screen 4"
[screen5]: https://raw.githubusercontent.com/jokob-sk/NetAlertX/main/docs/img/plugins_device_details.png     "Screen 5"
