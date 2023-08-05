## ⚙ Settings 

This is an explanation how settings are handled intended for anyone thinking about writing their own plugin or contributing to the project. 

If you are a user of the app, settings should be described in the `Settings` section of the app. Open an issue if you'd like to clarify any of the settings. 

### 🛢 Data storage

The source of truth for user-defined values is the `pialert.conf` file. Editing the file overwrites values in the databse and in the `table_settings.json` file. 

#### Settings database table
#### table_settings.json
#### pialert.conf
#### Plugin settings


### Settings Process flow

The process flow is mostly managed by the [initialise.py](/pialert/initialise.py) file. 

The script is responsible for reading user-defined values from a configuration file (`pialert.conf`), initializing settings, and importing them into a database. It also handles plugins and their configurations.

Here's a high-level description of the code:

1. Function Definitions:
   - `ccd`: This function is used to handle user-defined settings and configurations. It takes several parameters related to the setting's name, default value, input type, options, group, and more. It saves the settings and their metadata in different lists (`conf.mySettingsSQLsafe` and `conf.mySettings`).

   - `importConfigs`: This function is the main entry point of the script. It imports user settings from a configuration file, processes them, and saves them to the database.

   - `read_config_file`: This function reads the configuration file (`pialert.conf`) and returns a dictionary containing the key-value pairs from the file.

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





