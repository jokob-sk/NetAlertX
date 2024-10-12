# 🔌 Plugins

NetAlertX supports additional plugins to extend its functionality, each with its own settings and options. Plugins can be loaded via the General -> `LOADED_PLUGINS` setting by using Ctrl + Click. For custom plugin development, refer to the [Plugin development guide](/docs/PLUGINS_DEV.md).   

>[!NOTE]
> Please check this [Plugins debugging guide](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DEBUG_PLUGINS.md) and the corresponding Plugin documentation in the below table if you are facing issues.  

## ⚡ Quick start

> [!TIP]
> You can load additional Plugins via the General -> `LOADED_PLUGINS` setting. 

1. Pick your `🔍 dev scanner` plugin (e.g. `ARPSCAN` or `NMAPDEV`), or import devices into the application with an `📥 importer` plugin. (See **✅Enabling plugins** below)
2. Pick a `▶️ publisher` plugin, if you want to send notifications. If you don't see a publisher you'd like to use, look at the  [📚_publisher_apprise](/front/plugins/_publisher_apprise/) plugin which is a proxy for over 80 notification services. 
3. Setup your [Network topology diagram](/docs/NETWORK_TREE.md)
4. Fine-tune [Notifications](/docs/NOTIFICATIONS.md)
5. [Backup your setup](/docs/BACKUPS.md)
6. Contribute and [Create custom plugins](/docs/PLUGINS_DEV.md)
7. Consider [donating](https://github.com/jokob-sk/NetAlertX?tab=readme-ov-file#-sponsors) to keep me going


## 📑 Available Plugins
 
Device-detecting plugins insert values into the `CurrentScan` database table.  The plugins that are not required are safe to ignore, however, it makes sense to have at least some device-detecting plugins enabled, such as `ARPSCAN` or `NMAPDEV`. 


| ID            | Type    | Description                                | Features | Required | Data source  | Detailed docs                                                       |
|---------------|---------|--------------------------------------------|----------|----------|--------------------|---------------------------------------------------------------|
| `APPRISE`     | ▶️      | Apprise notification proxy                |           |          | Script       | [_publisher_apprise](/front/plugins/_publisher_apprise/)          |
| `ARPSCAN`     | 🔍      | ARP-scan on current network               |           |          | Script       | [arp_scan](/front/plugins/arp_scan/)                              |
| `AVAHISCAN`   | ♻       | Avahi (mDNS-based) name resolution        |           |          | Script       | [avahi_scan](/front/plugins/avahi_scan/)                          |
| `CSVBCKP`     | ⚙       | CSV devices backup                        |           |          | Script       | [csv_backup](/front/plugins/csv_backup/)                          |
| `DBCLNP`      | ⚙       | Database cleanup                          |           |  Yes*    | Script       | [db_cleanup](/front/plugins/db_cleanup/)                          |
| `DDNS`        | ⚙       | DDNS update                               |           |          | Script       | [ddns_update](/front/plugins/ddns_update/)                        |
| `DHCPLSS`     | 🔍/📥   | Import devices from DHCP leases           |           |          | Script       | [dhcp_leases](/front/plugins/dhcp_leases/)                        |
| `DHCPSRVS`    | ♻       | DHCP servers                              |           |          | Script       | [dhcp_servers](/front/plugins/dhcp_servers/)                      |
| `INTRNT`      | 🔍      | Internet IP scanner                       |           |          | Script       | [internet_ip](/front/plugins/internet_ip/)                        |
| `INTRSPD`     | ♻       | Internet speed test                       |           |          | Script       | [internet_speedtest](/front/plugins/internet_speedtest/)          |
| `MAINT`       | ⚙       | Maintenance of logs, etc.                 |           |          | Script       | [maintenance](/front/plugins/maintenance/)                        |
| `MQTT`        | ▶️      | MQTT for synching to Home Assistant       |           |          | Script       | [_publisher_mqtt](/front/plugins/_publisher_mqtt/)                |
| `NBTSCAN`     | ♻       | Nbtscan (NetBIOS-based) name resolution   |           |          | Script       | [nbtscan_scan](/front/plugins/nbtscan_scan/)                      |
| `NEWDEV`      | ⚙       | New device template                       |           |  Yes     | Template     | [newdev_template](/front/plugins/newdev_template/)                |
| `NMAP`        | ♻       | Nmap port scanning & discovery            |           |          | Script       | [nmap_scan](/front/plugins/nmap_scan/)                            |
| `NMAPDEV`     | 🔍      | Nmap dev scan on current network          |           |          | Script       | [nmap_dev_scan](/front/plugins/nmap_dev_scan/)                    |
| `NSLOOKUP`    | ♻       | NSLookup (DNS-based) name resolution      |           |          | Script       | [nslookup_scan](/front/plugins/nslookup_scan/)                    |
| `NTFPRCS`     | ⚙       | Notification processing                   |           |  Yes     | Template     | [notification_processing](/front/plugins/notification_processing/)|
| `NTFY`        | ▶️      | NTFY notifications                        |           |          | Script       | [_publisher_ntfy](/front/plugins/_publisher_ntfy/)                |
| `OMDSDN`      | 📥      | OMADA TP-Link import                      |   🖧 🔄   |          | Script       | [omada_sdn_imp](/front/plugins/omada_sdn_imp/)                    |
| `PHOLUS`      | ♻       | Pholus name resolution                    |           |          | Script       | [pholus_scan](/front/plugins/pholus_scan/)                        |
| `PIHOLE`      | 🔍/📥   | Pi-hole device import & sync              |           |          | SQLite DB    | [pihole_scan](/front/plugins/pihole_scan/)                        |
| `PUSHSAFER`   | ▶️      | Pushsafer notifications                   |           |          | Script       | [_publisher_pushsafer](/front/plugins/_publisher_pushsafer/)      |
| `PUSHOVER`    | ▶️      | Pushover notifications                    |           |          | Script       | [_publisher_pushover](/front/plugins/_publisher_pushover/)        |
| `SETPWD`      | ⚙       | Set password                              |           |  Yes     | Template     | [set_password](/front/plugins/set_password/)                      |
| `SMTP`        | ▶️      | Email notifications                       |           |          | Script       | [_publisher_email](/front/plugins/_publisher_email/)              |
| `SNMPDSC`     | 🔍/📥   | SNMP device import & sync                 |           |          | Script       | [snmp_discovery](/front/plugins/snmp_discovery/)                  |
| `SYNC`        | 🔍/⚙/📥| Sync & import from NetAlertX instances    |   🖧 🔄    |          | Script       | [sync](/front/plugins/sync/)                                     |
| `TELEGRAM`    | ▶️      | Telegram notifications                    |          |          | Script    | [_publisher_telegram](/front/plugins/_publisher_telegram/)             |
| `UNDIS`       | 🔍/📥   | Create dummy devices                      |           |          | Script       | [undiscoverables](/front/plugins/undiscoverables/)                |
| `UNFIMP`      | 🔍/📥   | UniFi device import & sync                |  🖧       |          | Script       | [unifi_import](/front/plugins/unifi_import/)                      |
| `VNDRPDT`     | ⚙       | Vendor database update                    |           |          | Script       | [vendor_update](/front/plugins/vendor_update/)                    |
| `WEBHOOK`     | ▶️      | Webhook notifications                     |           |          | Script       | [_publisher_webhook](/front/plugins/_publisher_webhook/)          |
| `WEBMON`      | ♻       | Website down monitoring                   |           |          | Script       | [website_monitor](/front/plugins/website_monitor/)                |
  

> \* The database cleanup plugin (`DBCLNP`) is not _required_ but the app will become unusable after a while if not executed.
>
> \** The Undiscoverables plugin (`UNDIS`) inserts only user-specified dummy devices.

> ⌚It's recommended to use the same schedule interval for all plugins responsible for discovering new devices.

## Plugin types


| Plugin type   | Icon  | Description                                                   |  When to run         | Required | Data source [?](/docs/PLUGINS_DEV.md) |
|---------------|------|----------------------------------------------------------------|--------------------------|----|---------|
|  publisher    | ▶️ | Sending notifications to services.                               | `on_notification`       |  ✖ | Script | 
|  dev scanner  | 🔍 | Create devices in the app, manages online/offline device status. | `schedule`             |  ✖ | Script / SQLite DB  | 
|  importer     | 📥 | Importing devices from another service.                          | `schedule`             |  ✖ | Script / SQLite DB  | 
|  system       | ⚙  | Providing core system functionality.                             | `schedule` / always on  |  ✖/✔ | Script / Template | 
|  other        | ♻  | Other scanners, e.g. for name resolution                         | misc                    |  ✖ | Script / Template | 

## Features

| Icon  | Description                                                  | 
|------|---------------------------------------------------------------|
| 🖧    | Auto-imports the network topology diagram                     |
| 🔄   | Has the option to sync some data back into the plugin source  |


## ✅Enabling plugins

Plugins can be enabled via Settings, and can be disabled as needed. 

1. Research which plugin you'd like to use and load the required plugins in Settings via the `LOADED_PLUGINS` setting.
1. Save the changes and review the Settings of the newly loaded plugins. 
1. Change the `<prefix>_RUN` Setting to the recommended or custom value as per the documentation of the given setting  
    - If using `schedule` on a `🔍 dev scanner` plugin, make sure the schedules are the same across all `🔍 dev scanner` plugins

### Disabling, Unloading and Ignoring plugins

1. Change the `<prefix>_RUN` Setting to `disabled` if you want to disable the plugin, but keep the settings
1. If you want to speed up the application, you can unload the plugin by unselecting it in the `LOADED_PLUGINS` setting.
    - Careful, once you save the Settings Unloaded plugin settings will be lost (old `app.conf` files are kept in the `/config` folder) 
1. You can completely ignore plugins by placing a `ignore_plugin` file into the plugin directory. Ignored plugins won't show up in the `LOADED_PLUGINS` setting.

## 🆕 Developing new custom plugins

If you want to develop a custom plugin, please read this [Plugin development guide](/docs/PLUGINS_DEV.md).