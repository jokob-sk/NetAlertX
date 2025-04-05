# 🔌 Plugins

NetAlertX supports additional plugins to extend its functionality, each with its own settings and options. Plugins can be loaded via the General -> `LOADED_PLUGINS` setting. For custom plugin development, refer to the [Plugin development guide](./PLUGINS_DEV.md).   

>[!NOTE]
> Please check this [Plugins debugging guide](./DEBUG_PLUGINS.md) and the corresponding Plugin documentation in the below table if you are facing issues.  

## ⚡ Quick start

> [!TIP]
> You can load additional Plugins via the General -> `LOADED_PLUGINS` setting. 

1. Pick your `🔍 dev scanner` plugin (e.g. `ARPSCAN` or `NMAPDEV`), or import devices into the application with an `📥 importer` plugin. (See **✅Enabling plugins** below)
2. Pick a `▶️ publisher` plugin, if you want to send notifications. If you don't see a publisher you'd like to use, look at the  [📚_publisher_apprise](/front/plugins/_publisher_apprise/) plugin which is a proxy for over 80 notification services. 
3. Setup your [Network topology diagram](./NETWORK_TREE.md)
4. Fine-tune [Notifications](./NOTIFICATIONS.md)
5. [Backup your setup](./BACKUPS.md)
6. Contribute and [Create custom plugins](./PLUGINS_DEV.md)


## 📑 Available Plugins
 
Device-detecting plugins insert values into the `CurrentScan` database table.  The plugins that are not required are safe to ignore, however, it makes sense to have at least some device-detecting plugins enabled, such as `ARPSCAN` or `NMAPDEV`. 

> [!NOTE]
> See tables below for a description of what the icons in the below Plugins table mean. 


| ID            | Type    | Description                                | Features | Required | Data source  | Detailed docs                                                       |
|---------------|---------|--------------------------------------------|----------|----------|--------------|---------------------------------------------------------------------|
| `APPRISE`     | ▶️      | Apprise notification proxy                |           |          | Script       | [_publisher_apprise](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/_publisher_apprise/)          |
| `ARPSCAN`     | 🔍      | ARP-scan on current network               |           |          | Script       | [arp_scan](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/arp_scan/)                              |
| `AVAHISCAN`   | 🆎      | Avahi (mDNS-based) name resolution        |           |          | Script       | [avahi_scan](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/avahi_scan/)                          |
| `ASUSWRT`     | 🔍       | Import connected devices from AsusWRT    |           |          | Script       | [asuswrt_import](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/asuswrt_import/)                  |
| `CSVBCKP`     | ⚙       | CSV devices backup                        |           |          | Script       | [csv_backup](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/csv_backup/)                          |
| `CUSTPROP`    | ⚙       | Managing custom device properties values  |           |  Yes     | Template     | [custom_props](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/custom_props/)                      |
| `DBCLNP`      | ⚙       | Database cleanup                          |           |  Yes*    | Script       | [db_cleanup](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/db_cleanup/)                          |
| `DDNS`        | ⚙       | DDNS update                               |           |          | Script       | [ddns_update](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/ddns_update/)                        |
| `DHCPLSS`     | 🔍/📥/🆎| Import devices from DHCP leases          |           |          | Script       | [dhcp_leases](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/dhcp_leases/)                        |
| `DHCPSRVS`    | ♻       | DHCP servers                              |           |          | Script       | [dhcp_servers](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/dhcp_servers/)                      |
| `FREEBOX`     | 🔍/♻/🆎| Pull data and names from Freebox/Iliadbox |          |          | Script       | [freebox](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/freebox/)                                 |
| `ICMP`        | ♻      | ICMP (ping) status checker                |           |          | Script       | [icmp_scan](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/icmp_scan/)                            |
| `INTRNT`      | 🔍      | Internet IP scanner                       |           |          | Script       | [internet_ip](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/internet_ip/)                        |
| `INTRSPD`     | ♻       | Internet speed test                       |           |          | Script       | [internet_speedtest](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/internet_speedtest/)          |
| `IPNEIGH`     | 🔍       | Scan ARP (IPv4) and NDP (IPv6) tables    |           |          | Script       | [ipneigh](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/ipneigh/)                                |
| `LUCIRPC`     | 🔍       | Import connected devices from OpenWRT    |           |          | Script       | [luci_import](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/luci_import/)                        |
| `MAINT`       | ⚙       | Maintenance of logs, etc.                 |           |          | Script       | [maintenance](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/maintenance/)                        |
| `MQTT`        | ▶️      | MQTT for synching to Home Assistant       |           |          | Script       | [_publisher_mqtt](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/_publisher_mqtt/)                |
| `NBTSCAN`     | 🆎       | Nbtscan (NetBIOS-based) name resolution  |           |          | Script       | [nbtscan_scan](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/nbtscan_scan/)                      |
| `NEWDEV`      | ⚙       | New device template                       |           |  Yes     | Template     | [newdev_template](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/newdev_template/)                |
| `NMAP`        | ♻       | Nmap port scanning & discovery            |           |          | Script       | [nmap_scan](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/nmap_scan/)                            |
| `NMAPDEV`     | 🔍      | Nmap dev scan on current network          |           |          | Script       | [nmap_dev_scan](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/nmap_dev_scan/)                    |
| `NSLOOKUP`    | 🆎       | NSLookup (DNS-based) name resolution     |           |          | Script       | [nslookup_scan](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/nslookup_scan/)                    |
| `NTFPRCS`     | ⚙       | Notification processing                   |           |  Yes     | Template     | [notification_processing](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/notification_processing/)|
| `NTFY`        | ▶️      | NTFY notifications                        |           |          | Script       | [_publisher_ntfy](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/_publisher_ntfy/)                |
| `OMDSDN`      | 📥/🆎   | OMADA TP-Link import                      |   🖧 🔄  |          | Script       | [omada_sdn_imp](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/omada_sdn_imp/)                    |
| `OMDSDNOPENAPI`| 📥/🆎   | OMADA TP-Link import via OpenAPI        |   🖧      |          | Script       | [omada_sdn_openapi](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/omada_sdn_openapi/)                    |
| `PIHOLE`      | 🔍/🆎/📥| Pi-hole device import & sync             |           |          | SQLite DB    | [pihole_scan](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/pihole_scan/)                        |
| `PUSHSAFER`   | ▶️      | Pushsafer notifications                   |           |          | Script       | [_publisher_pushsafer](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/_publisher_pushsafer/)      |
| `PUSHOVER`    | ▶️      | Pushover notifications                    |           |          | Script       | [_publisher_pushover](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/_publisher_pushover/)        |
| `SETPWD`      | ⚙       | Set password                              |           |  Yes     | Template     | [set_password](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/set_password/)                      |
| `SMTP`        | ▶️      | Email notifications                       |           |          | Script       | [_publisher_email](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/_publisher_email/)              |
| `SNMPDSC`     | 🔍/📥   | SNMP device import & sync                 |           |          | Script       | [snmp_discovery](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/snmp_discovery/)                  |
| `SYNC`        | 🔍/⚙/📥| Sync & import from NetAlertX instances    |   🖧 🔄   | Yes     | Script        | [sync](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/sync/)                                      |
| `TELEGRAM`    | ▶️      | Telegram notifications                    |           |          | Script       | [_publisher_telegram](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/_publisher_telegram/)        |
| `UI`          | ♻       | UI specific settings                      |           |  Yes     | Template     | [ui_settings](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/ui_settings/)                        |
| `UNFIMP`      | 🔍/📥/🆎| UniFi device import & sync               |  🖧       |          | Script       | [unifi_import](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/unifi_import/)                      |
| `VNDRPDT`     | ⚙       | Vendor database update                    |           |          | Script       | [vendor_update](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/vendor_update/)                    |
| `WEBHOOK`     | ▶️      | Webhook notifications                     |           |          | Script       | [_publisher_webhook](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/_publisher_webhook/)          |
| `WEBMON`      | ♻       | Website down monitoring                   |           |          | Script       | [website_monitor](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/website_monitor/)                |
| `WOL`         | ♻       | Automatic wake-on-lan                     |           |          | Script       | [wake_on_lan](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/wake_on_lan/)                        |


> \* The database cleanup plugin (`DBCLNP`) is not _required_ but the app will become unusable after a while if not executed.
> ❌ marked for removal
> ⌚It's recommended to use the same schedule interval for all plugins responsible for discovering new devices.

## Plugin types


| Plugin type    | Icon | Description                                                      | When to run                         | Required | Data source [?](./PLUGINS_DEV.md) |
| -------------- | ---- | ---------------------------------------------------------------- | ----------------------------------- | -------- | ------------------------------------- |
| publisher      | ▶️    | Sending notifications to services.                               | `on_notification`                   | ✖        | Script                                |
| dev scanner    | 🔍    | Create devices in the app, manages online/offline device status. | `schedule`                          | ✖        | Script / SQLite DB                    |
| name discovery | 🆎    | Discovers names of devices via various protocols.                | `before_name_updates`, `schedule`   | ✖        | Script                                |
| importer       | 📥    | Importing devices from another service.                          | `schedule`                          | ✖        | Script / SQLite DB                    |
| system         | ⚙    | Providing core system functionality.                             | `schedule` / always on              | ✖/✔      | Script / Template                     |
| other          | ♻    | Other plugins                                                    | misc                                | ✖        | Script / Template                     |

## Features

| Icon | Description                                                  |
| ---- | ------------------------------------------------------------ |
| 🖧    | Auto-imports the network topology diagram                    |
| 🔄    | Has the option to sync some data back into the plugin source |


## ✅Enabling plugins

Plugins can be enabled via Settings, and can be disabled as needed. 

1. Research which plugin you'd like to use, enable `DISCOVER_PLUGINS` and load the required plugins in Settings via the `LOADED_PLUGINS` setting.
1. Save the changes and review the Settings of the newly loaded plugins. 
1. Change the `<prefix>_RUN` Setting to the recommended or custom value as per the documentation of the given setting  
    - If using `schedule` on a `🔍 dev scanner` plugin, make sure the schedules are the same across all `🔍 dev scanner` plugins

### Disabling, Unloading and Ignoring plugins

1. Change the `<prefix>_RUN` Setting to `disabled` if you want to disable the plugin, but keep the settings
1. If you want to speed up the application, you can unload the plugin by unselecting it in the `LOADED_PLUGINS` setting.
    - Careful, once you save the Settings Unloaded plugin settings will be lost (old `app.conf` files are kept in the `/config` folder) 
1. You can completely ignore plugins by placing a `ignore_plugin` file into the plugin directory. Ignored plugins won't show up in the `LOADED_PLUGINS` setting.

## 🆕 Developing new custom plugins

If you want to develop a custom plugin, please read this [Plugin development guide](./PLUGINS_DEV.md).