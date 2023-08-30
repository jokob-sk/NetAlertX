  
  # A high-level description of the datbase structure

  ⚠ Disclaimer: As I'm not the original author, some of the information might be inaccurate. Feel free to submit a PR to correct anything within this page or documentation in general. 

  The MAC address is used as a foreign key in most cases. 

  ## 🔍Tables overview
  
  | Table name | Description  | Sample data |
  |----------------------|----------------------| ----------------------| 
  | CurrentScan | Result of the current scan | ![Screen1][screen1]  |  
  | Devices     | The main devices database that also contains the Network tree mappings. If `ScanCycle` is set to `0` device is not scanned. | ![Screen2][screen2]  |   
  | Events | Used to collect connection/disconnection events. | ![Screen4][screen4]  |   
  | Online_History   | Used to display the `Device presence over time` chart  | ![Screen6][screen6]  | 
  | Parameters       | Used to pass values between the frontend and backend. | ![Screen7][screen7]  | 
  | Pholus_Scan      | Scan results of the Pholus python network penetration script. | ![Screen8][screen8]  |   
  | Plugins_Events   | For capturing events exposed by a plugin via the `last_result.log` file. If unique then saved into the `Plugins_Objects` table. Entries are deleted once processed and stored in the `Plugins_History` and/or `Plugins_Objects` tables.  | ![Screen10][screen10]  | 
  | Plugins_History  | History of all entries from the `Plugins_Events` table | ![Screen11][screen11]  | 
  | Plugins_Language_Strings  | Language strings colelcted from the plugin `config.json` files used for string resolution in the frontend. | ![Screen12][screen12]  | 
  | Plugins_Objects  | Unique objects detected by individual plugins. | ![Screen13][screen13]  | 
  | Sessions  | Used to display sessions in the charts | ![Screen15][screen15]  | 
  | Settings  | Database representation of the sum of all settings from `pialert.conf` and plugins coming from `config.json` files. | ![Screen16][screen16]  | 



  [screen1]: /docs/img/DATABASE/CurrentScan.png
  [screen2]: /docs/img/DATABASE/Devices.png
  [screen4]: /docs/img/DATABASE/Events.png  
  [screen6]: /docs/img/DATABASE/Online_History.png
  [screen7]: /docs/img/DATABASE/Parameters.png
  [screen8]: /docs/img/DATABASE/Pholus_Scan.png  
  [screen10]: /docs/img/DATABASE/Plugins_Events.png
  [screen11]: /docs/img/DATABASE/Plugins_History.png
  [screen12]: /docs/img/DATABASE/Plugins_Language_Strings.png
  [screen13]: /docs/img/DATABASE/Plugins_Objects.png  
  [screen15]: /docs/img/DATABASE/Sessions.png
  [screen16]: /docs/img/DATABASE/Settings.png

