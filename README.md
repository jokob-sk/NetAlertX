# Pi.Alert
<!--- --------------------------------------------------------------------- --->

💻🔍 WIFI / LAN intruder detector.

Scans for devices connected to your WIFI / LAN and alerts you if new and unknown devices are found.

![Main screen][main]


# 🐳 Docker image 
[![Docker](https://img.shields.io/github/actions/workflow/status/jokob-sk/Pi.Alert/docker_prod.yml?label=Build&logo=GitHub)](https://github.com/jokob-sk/Pi.Alert/actions/workflows/docker_prod.yml)
[![GitHub Committed](https://img.shields.io/github/last-commit/jokob-sk/Pi.Alert?color=40ba12&label=Committed&logo=GitHub&logoColor=fff)](https://github.com/jokob-sk/Pi.Alert)
[![Docker Size](https://img.shields.io/docker/image-size/jokobsk/pi.alert?label=Size&logo=Docker&color=0aa8d2&logoColor=fff)](https://hub.docker.com/r/jokobsk/pi.alert)
[![Docker Pulls](https://img.shields.io/docker/pulls/jokobsk/pi.alert?label=Pulls&logo=docker&color=0aa8d2&logoColor=fff)](https://hub.docker.com/r/jokobsk/pi.alert)
[![Docker Pushed](https://img.shields.io/badge/dynamic/json?color=0aa8d2&logoColor=fff&label=Pushed&query=last_updated&url=https%3A%2F%2Fhub.docker.com%2Fv2%2Frepositories%2Fjokobsk%2Fpi.alert%2F&logo=docker&link=http://left&link=https://hub.docker.com/repository/docker/jokobsk/pi.alert)](https://hub.docker.com/r/jokobsk/pi.alert)

🐳 [Docker hub](https://registry.hub.docker.com/r/jokobsk/pi.alert) | 📄 [Dockerfile](https://github.com/jokob-sk/Pi.Alert/blob/main/Dockerfile) | 📚 [Docker instructions](https://github.com/jokob-sk/Pi.Alert/blob/main//dockerfiles/README.md) | 🆕 [Release notes](https://github.com/jokob-sk/Pi.Alert/releases)

## 🔍 Scan Methods
The system continuously scans the network for, **New devices**, **New connections** (re-connections), **Disconnections**, **"Always Connected" devices down**, Devices **IP changes** and **Internet IP address changes**. Scanning methods are:
  - **Method 1: arp-scan**. The arp-scan system utility is used to search
        for devices on the network using arp frames.
  - **Method 2: Pi-hole**. This method is optional and complementary to
        method 1. If the Pi-hole DNS server is active, Pi.Alert examines its
        activity looking for active devices using DNS that have not been
        detected by method 1.
  - **Method 3. dnsmasq**. This method is optional and complementary to the
        previous methods. If the DHCP server dnsmasq is active, Pi.Alert
        examines the DHCP leases (addresses assigned) to find active devices
        that were not discovered by the other methods.


## 🧩 Integrations 
   - [Apprise](https://hub.docker.com/r/caronc/apprise), [Pushsafer](https://www.pushsafer.com/), [NTFY](https://ntfy.sh/)
   - [Webhooks](https://github.com/jokob-sk/Pi.Alert/blob/main/docs/WEBHOOK_N8N.md) ([sample JSON](docs/webhook_json_sample.json))
   - Home Assistant via [MQTT](https://www.home-assistant.io/integrations/mqtt/) - discovery ~10s per device, use [MQTT Explorer](https://mqtt-explorer.com/) to delete devices
   - [API endpoint](https://github.com/jokob-sk/Pi.Alert/blob/main/docs/API.md)
   - [Plugin system](https://github.com/jokob-sk/Pi.Alert/tree/main/front/plugins) for custom script monitoring


## 🔐 Security

- Configurable login to prevent unauthorized use. 

## 📑 Features   
  - Display:
    - Sessions, Connected devices, Favorites, Events, Presence, Concurrent devices, Down alerts, IP's
    - Manual Nmap scans, Optional speedtest for Device "Internet"
    - Simple Network relationship display
  - Maintenance tasks and Settings like:
    - Status Infos (active scans, database size, backup counter)
    - Theme Selection (blue, red, green, yellow, black, purple) and Light/Dark-Mode Switch
    - Language Selection (English, German, Spanish)    
    - Pause arp-scan
    - DB maintenance, Backup, Restore tools and CSV Export / Import
  - Help/FAQ Section 

  | ![Screen 1][screen1] | ![Screen 2][screen2] | 
  |----------------------|----------------------| 
  | ![Screen 3][screen3] | ![Screen 4][screen4] |
  | ![Screen 5][screen5] | ![Screen 6][screen6] |
  | ![Report 1][report1] | ![Report 2][report2] |
 

# 📥 Installation
<!--- --------------------------------------------------------------------- --->

 ⚠ This [fork (jokob-sk)](https://github.com/jokob-sk/Pi.Alert) is only tested as a [docker container](dockerfiles/README.md). Check out [leiweibau's fork](https://github.com/leiweibau/Pi.Alert/) if you want to install Pi.Alert on the server directly.

Instructions for [pucherot's original code can be found here](https://github.com/pucherot/Pi.Alert/)


## 🔗 Other


<!--- --------------------------------------------------------------------- --->

<!--- --------------------------------------------------------------------- --->
### Alternatives

  - [WatchYourLAN](https://github.com/aceberg/WatchYourLAN) - Lightweight network IP scanner with web GUI (Open source)
  - [Fing](https://www.fing.com/) - Network scanner app for your Internet security (Commercial, Phone App, Proprietary hardware)

### Old docs

  - [Device Management instructions](docs/DEVICE_MANAGEMENT.md)
  - [Versions History](docs/VERSIONS_HISTORY.md)

### License
  GPL 3.0
  - [Read more here](LICENSE.txt)
  - Source of the [animated GIF (Loading Animation)](https://commons.wikimedia.org/wiki/File:Loading_Animation.gif)  
  - Source of the [selfhosted Fonts](https://github.com/adobe-fonts/source-sans)
  
### 🥇 Special thanks 

  This code is a collaborative body of work, with special thanks to: 

   - 🏆 [pucherot/Pi.Alert](https://github.com/pucherot/Pi.Alert) is the original creator od PiAlert
      - [leiweibau](https://github.com/leiweibau/Pi.Alert): Dark mode (and much more)
      - [Macleykun](https://github.com/Macleykun): Help with Dockerfile clean-up
      - [Final-Hawk](https://github.com/Final-Hawk): Help with NTFY, styling and other fixes
      - [TeroRERO](https://github.com/terorero): Spanish translation
      - [jokob-sk](https://github.com/jokob-sk/Pi.Alert): DB Maintenance tools
      - Please see the [Git commit history](https://github.com/jokob-sk/Pi.Alert/commits/main) for a full list of people and their contributions to the project

<!--- --------------------------------------------------------------------- --->
[main]:    ./docs/img/devices_split.png       "Main screen"
[screen1]: ./docs/img/device_details.png      "Screen 1"
[screen2]: ./docs/img/events.png              "Screen 2"
[screen3]: ./docs/img/presence.png            "Screen 3"
[screen4]: ./docs/img/maintenance.png         "Screen 4"
[screen5]: ./docs/img/network.png             "Screen 5"
[screen6]: ./docs/img/settings.png            "Screen 6"
[screen7]: ./docs/img/help_faq.png            "Screen 6"
[report1]: ./docs/img/4_report_1.jpg          "Report sample 1"
[report2]: ./docs/img/4_report_2.jpg          "Report sample 2"
[main_dark]: /docs/img/1_devices_dark.jpg     "Main screen dark"
[maintain_dark]: /docs/img/5_maintain.jpg     "Maintain screen dark"

