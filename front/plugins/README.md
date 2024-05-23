# 📚 Docs for individual plugins 

>[!NOTE]
> Please check this [Plugins debugging guide](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DEBUG_PLUGINS.md) and the corresponding Plugin documentation in the below table if you are facing issues.  

## 🔌 Plugins & 📚 Docs 

| Required | CurrentScan | Unique Prefix | Data source        |   Type         | Link + Docs                                                          | 
|----------|-------------|---------------|--------------------|----------------|---------------------------------------------------------------------|
|          |             | APPRISE       | Script             | 💬 publisher   | 📚[_publisher_apprise](/front/plugins/_publisher_apprise/)          |
|          |    Yes      | ARPSCAN       | Script             | 🔍dev scanner  | 📚[arp_scan](/front/plugins/arp_scan/)                              |
|          |             | CSVBCKP       | Script             | ⚙ system       | 📚[csv_backup](/front/plugins/csv_backup/)                          |
|  Yes*    |             | DBCLNP        | Script             | ⚙ system       | 📚[db_cleanup](/front/plugins/db_cleanup/)                          |
|          |             | DDNS          | Script             | ⚙ system       | 📚[ddns_update](/front/plugins/ddns_update/)                        |
|          |    Yes      | DHCPLSS       | Script             | 🔍dev scanner  | 📚[dhcp_leases](/front/plugins/dhcp_leases/)                        |
|          |             | DHCPSRVS      | Script             | ♻ other        | 📚[dhcp_servers](/front/plugins/dhcp_servers/)                      |
|          |    Yes      | INTRNT        | Script             | 🔍dev scanner  | 📚[internet_ip](/front/plugins/internet_ip/)                        |
|          |             | INTRSPD       | Script             | ♻ other        | 📚[internet_speedtest](/front/plugins/internet_speedtest/)          |
|          |             | MAINT         | Script             | ⚙ system       | 📚[maintenance](/front/plugins/maintenance/)                        |
|          |             | MQTT          | Script             | 💬 publisher   | 📚[_publisher_mqtt](/front/plugins/_publisher_mqtt/)                |
|  Yes     |             | NEWDEV        | Template           | ⚙ system       | 📚[newdev_template](/front/plugins/newdev_template/)                |
|          |             | NMAP          | Script             | ♻ other        | 📚[nmap_scan](/front/plugins/nmap_scan/)                            |
|          |    Yes      | NMAPDEV       | Script             | 🔍dev scanner  | 📚[nmap_dev_scan](/front/plugins/nmap_dev_scan/)                    |
|          |             | NSLOOKUP      | Script             | ♻ other        | 📚[nslookup_scan](/front/plugins/nslookup_scan/)                    |
|  Yes     |             | NTFPRCS       | Template           | ⚙ system       | 📚[notification_processing](/front/plugins/notification_processing/)|
|          |             | NTFY          | Script             | 💬 publisher   | 📚[_publisher_ntfy](/front/plugins/_publisher_ntfy/)                |
|          |             | PHOLUS        | Script             | ♻ other        | 📚[pholus_scan](/front/plugins/pholus_scan/)                        |
|          |    Yes      | PIHOLE        | External SQLite DB | 🔍dev scanner  | 📚[pihole_scan](/front/plugins/pihole_scan/)                        |
|          |             | PUSHSAFER     | Script             | 💬 publisher   | 📚[_publisher_pushsafer](/front/plugins/_publisher_pushsafer/)      |
|          |             | PUSHOVER      | Script             | 💬 publisher   | 📚[_pushover_pushsafer](/front/plugins/_publisher_pushover/)        |
|  Yes     |             | SETPWD        | Template           | ⚙ system       | 📚[set_password](/front/plugins/set_password/)                      |
|          |             | SMTP          | Script             | 💬 publisher   | 📚[_publisher_email](/front/plugins/_publisher_email/)              |
|          |    Yes      | SNMPDSC       | Script             | 🔍dev scanner  | 📚[snmp_discovery](/front/plugins/snmp_discovery/)                  |
|          |    Yes**    | UNDIS         | Script             | ♻ other        | 📚[undiscoverables](/front/plugins/undiscoverables/)                |
|          |    Yes      | UNFIMP        | Script             | 🔍dev scanner  | 📚[unifi_import](/front/plugins/unifi_import/)                      |
|          |             | VNDRPDT       | Script             | ⚙ system       | 📚[vendor_update](/front/plugins/vendor_update/)                    |
|          |             | WEBHOOK       | Script             | 💬 publisher   | 📚[_publisher_webhook](/front/plugins/_publisher_webhook/)          |
|          |             | WEBMON        | Script             | ♻ other        | 📚[website_monitor](/front/plugins/website_monitor/)                |
|  N/A     |             | N/A           | SQL query          |                 | N/A, but the External SQLite DB plugins work similarly              |


> \* The database cleanup plugin (`DBCLNP`) is not _required_ but the app will become unusable after a while if not executed.
>
> \** The Undiscoverables plugin (`UNDIS`) inserts only user-specified dummy devices.

> [!NOTE] 
> You soft-disable plugins via Settings or completely ignore plugins by placing a `ignore_plugin` file into the plugin directory. The difference is that ignored plugins don't show up anywhere in the UI (Settings, Device details, Plugins pages). The app skips ignored plugins completely. Device-detecting plugins insert values into the `CurrentScan` database table.  The plugins that are not required are safe to ignore, however it makes sense to have a least some device-detecting plugins (that insert entries into the `CurrentScan` table) enabled, such as `ARPSCAN` or `PIHOLE`. You can also load/unload Plugins with the `LOADED_PLUGINS` setting.

> It's recommended to use the same schedule interval for all plugins responsible for discovering new devices.

If you want to develop a custom plugin, please read this [Plugin development guide](/docs/PLUGINS_DEV.md).