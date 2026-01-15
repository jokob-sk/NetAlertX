## ⚙ Setting system

This is an explanation how settings are handled intended for anyone thinking about writing their own plugin or contributing to the project.

If you are a user of the app, settings have a detailed description in the _Settings_ section of the app. Open an issue if you'd like to clarify any of the settings.

### 🛢 Data storage

The source of truth for user-defined values is the `app.conf` file. Editing the file makes the App overwrite values in the `Settings` database table and in the `table_settings.json` file.

#### Settings database table

The `Settings` database table contains settings for App run purposes. The table is recreated every time the App restarts. The settings are loaded from the source-of-truth, that is the `app.conf` file. A high-level overview on the database structure can be found in the [database documentation](./DATABASE.md).

#### table_settings.json

This is the [API endpoint](./API.md) that reflects the state of the `Settings` database table. Settings can be accessed with the:

* `getSetting(key)` JavaScript method

The json file is also cached on the client-side local storage of the browser.

#### app.conf

> [!NOTE]
> This is the source of truth for settings. User-defined values in this files always override default values specified in the Plugin definition.

The App generates two `app.conf` entries for every setting (Since version 23.8+). One entry is the setting value, the second is the `__metadata` associated with the setting. This `__metadata` entry contains the full setting definition in JSON format. Currently unused, but intended to be used in future to extend the Settings system.

#### Plugin settings

> [!NOTE]
> This is the preferred way adding settings going forward. I'll be likely migrating all app settings into plugin-based settings.

Plugin settings are loaded dynamically from the `config.json` of individual plugins. If a setting isn't defined in the `app.conf` file, it is initialized via the `default_value` property of a setting from the `config.json` file. Check the [Plugins documentation](https://docs.netalertx.com/PLUGINS#-setting-object-structure), section `⚙ Setting object structure` for details on the structure of the setting.

![Screen 1][screen1]

### Settings Process flow

The process flow is mostly managed by the [initialise.py](/server/initialise.py) file.

The script is responsible for reading user-defined values from a configuration file (`app.conf`), initializing settings, and importing them into a database. It also handles plugins and their configurations.

Here's a high-level description of the code:

1. Function Definitions:
   - `ccd`: This function is used to handle user-defined settings and configurations. It takes several parameters related to the setting's name, default value, input type, options, group, and more. It saves the settings and their metadata in different lists (`conf.mySettingsSQLsafe` and `conf.mySettings`).

   - `importConfigs`: This function is the main entry point of the script. It imports user settings from a configuration file, processes them, and saves them to the database.

   - `read_config_file`: This function reads the configuration file (`app.conf`) and returns a dictionary containing the key-value pairs from the file.

2. Importing Configuration and Initializing Settings:
   - The `importConfigs` function starts by checking the modification time of the configuration file to determine if it needs to be re-imported. If the file has not been modified since the last import, the function skips the import process.

   - The function reads the configuration file using the `read_config_file` function, which returns a dictionary of settings.

   - The script then initializes various user-defined settings using the `ccd` function, based on the values read from the configuration file. These settings are categorized into groups such as "General," "Email," "Webhooks," "Apprise," and more.

3. Plugin Handling:
   - The script loads and handles plugins dynamically. It retrieves plugin configurations and iterates through each plugin.
   - For each plugin, it extracts the prefix and settings related to that plugin and processes them similarly to other user-defined settings.
   - It also handles scheduling for plugins with specific `RUN_SCHD` settings.

4. Saving Settings to the Database:
   - The script clears the existing settings in the database and inserts the updated settings into the database using SQL queries.

5. Updating the API and Performing Cleanup:
   - After importing the configurations, the script updates the API to reflect the changes in the settings.
   - It saves the current timestamp to determine the next import time.
   - Finally, it logs the successful import of the new configuration.


_____________________

[screen1]: https://raw.githubusercontent.com/jokob-sk/NetAlertX/main/docs/img/plugins_json_settings.png      "Screen 1"