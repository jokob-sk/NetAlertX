# Logging

NetAlertX comes with several logs that help to identify application issues. 

For plugin-specific log debugging, please read the [Debug Plugins](./DEBUG_PLUGINS.md) guide.

When debugging any issue, increase the `LOG_LEVEL` Setting as per the [Debug tips](./DEBUG_TIPS.md) documentation.


## Main logs

You can find most of the logs exposed in the UI under _Maintenance -> Logs_. 

If the UI is inaccessible, you can access them under `/app/log`.

![Logs](./img/LOGGING/maintenance_logs.png)

In the _Maintennace -> Logs_ you can **Purge logs**, download the full log file or Filter the lines with some substring to narrow down your search. 

## Plugin logging

If a Plugin supplies data to the main app it's done either vie a SQL query or via a script that updates the `last_result.log` file in the plugin log folder (`app/log/plugins/`). These files are processed at the end of the scan and deleted on successful processing.

The data is in most of the cases then displayed in the application under _Integrations -> Plugins_ (or _Device -> Plugins_ if the plugin is supplying device-specific data). 

![Plugin objects](./img/LOGGING/logging_integrations_plugins.png)
