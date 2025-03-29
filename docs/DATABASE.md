  
# A high-level description of the database structure

  ⚠ Disclaimer: As I'm not the original author, some of the information might be inaccurate. Feel free to submit a PR to correct anything within this page or documentation in general. 

  The MAC address is used as a foreign key in most cases. 

## Devices database table

| Field Name              | Description |
|-------------------------|-------------|
| `devMac`               | MAC address of the device. |
| `devName`              | Name of the device. |
| `devOwner`             | Owner of the device. |
| `devType`              | Type of the device (e.g., phone, laptop, etc.). If set to a network type (e.g.: switch), it will become selectable as a Network Parent Node  |
| `devVendor`            | Vendor/manufacturer of the device. |
| `devFavorite`          | Whether the device is marked as a favorite. |
| `devGroup`             | Group the device belongs to. |
| `devComments`          | User comments or notes about the device. |
| `devFirstConnection`   | Timestamp of the device's first connection. |
| `devLastConnection`    | Timestamp of the device's last connection. |
| `devLastIP`            | Last known IP address of the device. |
| `devStaticIP`          | Whether the device has a static IP address. |
| `devScan`              | Whether the device should be scanned. |
| `devLogEvents`         | Whether events related to the device should be logged. |
| `devAlertEvents`       | Whether alerts should be generated for events. |
| `devAlertDown`         | Whether an alert should be sent when the device goes down. |
| `devSkipRepeated`      | Whether to skip repeated alerts for this device. |
| `devLastNotification`  | Timestamp of the last notification sent for this device. |
| `devPresentLastScan`   | Whether the device was present during the last scan. |
| `devIsNew`             | Whether the device is marked as new. |
| `devLocation`          | Physical or logical location of the device. |
| `devIsArchived`        | Whether the device is archived. |
| `devParentMAC`         | MAC address of the parent device (if applicable). |
| `devParentPort`        | Port of the parent device to which this device is connected. |
| `devIcon`              | Icon representing the device. |
| `devGUID`              | Unique identifier for the device. |
| `devSite`              | Site or location where the device is registered. |
| `devSSID`              | SSID of the Wi-Fi network the device is connected to. |
| `devSyncHubNode`       | The NetAlertX node ID used for synchronization between NetAlertX instances. |
| `devSourcePlugin`      | Source plugin that discovered the device. |


To understand how values of these fields influuence application behavior, such as Notifications or Network topology, see also: 

- [Device Management](./DEVICE_MANAGEMENT.md)
- [Network Tree Topology Setup](./NETWORK_TREE.md)
- [Notifications](./NOTIFICATIONS.md)


## Other Tables overview
  
  | Table name | Description  | Sample data |
  |----------------------|----------------------| ----------------------| 
  | CurrentScan | Result of the current scan | ![Screen1][screen1]  |  
  | Devices     | The main devices database that also contains the Network tree mappings. If `ScanCycle` is set to `0` device is not scanned. | ![Screen2][screen2]  |   
  | Events | Used to collect connection/disconnection events. | ![Screen4][screen4]  |   
  | Online_History   | Used to display the `Device presence` chart  | ![Screen6][screen6]  | 
  | Parameters       | Used to pass values between the frontend and backend. | ![Screen7][screen7]  | 
  | Plugins_Events   | For capturing events exposed by a plugin via the `last_result.log` file. If unique then saved into the `Plugins_Objects` table. Entries are deleted once processed and stored in the `Plugins_History` and/or `Plugins_Objects` tables.  | ![Screen10][screen10]  | 
  | Plugins_History  | History of all entries from the `Plugins_Events` table | ![Screen11][screen11]  | 
  | Plugins_Language_Strings  | Language strings collected from the plugin `config.json` files used for string resolution in the frontend. | ![Screen12][screen12]  | 
  | Plugins_Objects  | Unique objects detected by individual plugins. | ![Screen13][screen13]  | 
  | Sessions  | Used to display sessions in the charts | ![Screen15][screen15]  | 
  | Settings  | Database representation of the sum of all settings from `app.conf` and plugins coming from `config.json` files. | ![Screen16][screen16]  | 



  [screen1]: ./img/DATABASE/CurrentScan.png
  [screen2]: ./img/DATABASE/Devices.png
  [screen4]: ./img/DATABASE/Events.png  
  [screen6]: ./img/DATABASE/Online_History.png
  [screen7]: ./img/DATABASE/Parameters.png
  [screen10]: ./img/DATABASE/Plugins_Events.png
  [screen11]: ./img/DATABASE/Plugins_History.png
  [screen12]: ./img/DATABASE/Plugins_Language_Strings.png
  [screen13]: ./img/DATABASE/Plugins_Objects.png  
  [screen15]: ./img/DATABASE/Sessions.png
  [screen16]: ./img/DATABASE/Settings.png

