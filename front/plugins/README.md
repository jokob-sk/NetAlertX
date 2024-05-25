# 🔌 Plugins

>[!NOTE]
> Please check this [Plugins debugging guide](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DEBUG_PLUGINS.md) and the corresponding Plugin documentation in the below table if you are facing issues.  


## Plugin types

If you want to discover or import devices into the application enable some of the `🔍 dev scanner` plugins. The next step is to pick a notification plugin, or `💬 publisher` plugin, to get notified about network changes. If you don't see a publisher you'd like to use, look at the  [📚_publisher_apprise](/front/plugins/_publisher_apprise/) plugin which is a proxy for over 80 notification services. 

### Enabling plugins

Plugins can be enabled via Settings, and can be disabled as needed. 

1. Research which plugin you'd like to use below and then load the required plugins in Settings via the `LOADED_PLUGINS` setting.
1. Save the changes and review the Settings of the newly loaded plugins. 
1. Change the `<prefix>_RUN` Setting to the recommended or custom value as per the documentation of the given setting  
    - If using `schedule` on a `🔍 dev scanner` plugin, make sure the schedules are the same across all `🔍 dev scanner` plugins

### Disabling, Unloading and Ignoring plugins

1. Change the `<prefix>_RUN` Setting to `disabled` if you want to disable the plugin, but keep the settings
1. If you want to speed up the application, you can unload the plugin by unselecting it in the `LOADED_PLUGINS` setting.
    - Careful, once you save the Settings Unloaded plugin settings will be lost (old `app.conf` files are kept in the `/config` folder) 
1. You can completely ignore plugins by placing a `ignore_plugin` file into the plugin directory. Ignored plugins won't show up in the `LOADED_PLUGINS` setting.


## Available Plugins

Device-detecting plugins insert values into the `CurrentScan` database table.  The plugins that are not required are safe to ignore, however, it makes sense to have a least some device-detecting plugins enabled, such as `ARPSCAN` or `NMAPDEV`. 

| ID            | Type           | Description                  | Required | Data source        | Detailed docs                                                       |
|---------------|----------------|------------------------------|----------|--------------------|---------------------------------------------------------------------|
| `APPRISE`       | 💬 publisher   | Apprise publisher plugin     |          | Script             | [📚_publisher_apprise](/front/plugins/_publisher_apprise/)          |
| `ARPSCAN`       | 🔍 dev scanner | ARP scan plugin              |          | Script             | [📚arp_scan](/front/plugins/arp_scan/)                              |
| `CSVBCKP`       | ⚙ system       | CSV backup plugin            |          | Script             | [📚csv_backup](/front/plugins/csv_backup/)                          |
| `DBCLNP`        | ⚙ system       | Database cleanup plugin      |  Yes*    | Script             | [📚db_cleanup](/front/plugins/db_cleanup/)                          |
| `DDNS`          | ⚙ system       | DDNS update plugin           |          | Script             | [📚ddns_update](/front/plugins/ddns_update/)                        |
| `DHCPLSS`       | 🔍 dev scanner | DHCP leases plugin           |          | Script             | [📚dhcp_leases](/front/plugins/dhcp_leases/)                        |
| `DHCPSRVS`      | ♻ other        | DHCP servers plugin          |          | Script             | [📚dhcp_servers](/front/plugins/dhcp_servers/)                      |
| `INTRNT`        | 🔍 dev scanner | Internet IP scanner          |          | Script             | [📚internet_ip](/front/plugins/internet_ip/)                        |
| `INTRSPD`       | ♻ other        | Internet speed test plugin   |          | Script             | [📚internet_speedtest](/front/plugins/internet_speedtest/)          |
| `MAINT`         | ⚙ system       | Maintenance plugin           |          | Script             | [📚maintenance](/front/plugins/maintenance/)                        |
| `MQTT`          | 💬 publisher   | MQTT publisher plugin        |          | Script             | [📚_publisher_mqtt](/front/plugins/_publisher_mqtt/)                |
| `NEWDEV`        | ⚙ system       | New device template          |  Yes     | Template           | [📚newdev_template](/front/plugins/newdev_template/)                |
| `NMAP`          | ♻ other        | Nmap scan plugin             |          | Script             | [📚nmap_scan](/front/plugins/nmap_scan/)                            |
| `NMAPDEV`       | 🔍 dev scanner | Nmap device scan plugin      |          | Script             | [📚nmap_dev_scan](/front/plugins/nmap_dev_scan/)                    |
| `NSLOOKUP`      | ♻ other        | NSLookup scan plugin         |          | Script             | [📚nslookup_scan](/front/plugins/nslookup_scan/)                    |
| `NTFPRCS`       | ⚙ system       | Notification processing      |  Yes     | Template           | [📚notification_processing](/front/plugins/notification_processing/)|
| `NTFY`          | 💬 publisher   | NTFY publisher plugin        |          | Script             | [📚_publisher_ntfy](/front/plugins/_publisher_ntfy/)                |
| `PHOLUS`        | ♻ other        | Pholus scan plugin           |          | Script             | [📚pholus_scan](/front/plugins/pholus_scan/)                        |
| `PIHOLE`        | 🔍 dev scanner | Pi-hole scan plugin          |          | SQLite DB          | [📚pihole_scan](/front/plugins/pihole_scan/)                        |
| `PUSHSAFER`     | 💬 publisher   | Pushsafer publisher plugin   |          | Script             | [📚_publisher_pushsafer](/front/plugins/_publisher_pushsafer/)      |
| `PUSHOVER`      | 💬 publisher   | Pushover publisher plugin    |          | Script             | [📚_publisher_pushover](/front/plugins/_publisher_pushover/)        |
| `SETPWD`        | ⚙ system       | Set password template        |  Yes     | Template           | [📚set_password](/front/plugins/set_password/)                      |
| `SMTP`          | 💬 publisher   | Email publisher plugin       |          | Script             | [📚_publisher_email](/front/plugins/_publisher_email/)              |
| `SNMPDSC`       | 🔍 dev scanner | SNMP discovery plugin        |          | Script             | [📚snmp_discovery](/front/plugins/snmp_discovery/)                  |
| `UNDIS`         | ♻ other        | Undiscoverables scan plugin  |          | Script             | [📚undiscoverables](/front/plugins/undiscoverables/)                |
| `UNFIMP`        | 🔍 dev scanner | UniFi import plugin          |          | Script             | [📚unifi_import](/front/plugins/unifi_import/)                      |
| `VNDRPDT`       | ⚙ system       | Vendor update plugin         |          | Script             | [📚vendor_update](/front/plugins/vendor_update/)                    |
| `WEBHOOK`       | 💬 publisher   | Webhook publisher plugin     |          | Script             | [📚_publisher_webhook](/front/plugins/_publisher_webhook/)          |
| `WEBMON`        | ♻ other        | Website monitor plugin       |          | Script             | [📚website_monitor](/front/plugins/website_monitor/)                |



> \* The database cleanup plugin (`DBCLNP`) is not _required_ but the app will become unusable after a while if not executed.
>
> \** The Undiscoverables plugin (`UNDIS`) inserts only user-specified dummy devices.

> It's recommended to use the same schedule interval for all plugins responsible for discovering new devices.

## Developing custom plugins

If you want to develop a custom plugin, please read this [Plugin development guide](/docs/PLUGINS_DEV.md).