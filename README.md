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

🐳 [Docker hub](https://registry.hub.docker.com/r/jokobsk/pi.alert) | 📄 [Dockerfile](https://github.com/jokob-sk/Pi.Alert/blob/main/Dockerfile) | 📚 [Docker instructions](https://github.com/jokob-sk/Pi.Alert/blob/main/dockerfiles/README.md) | 🆕 [Release notes](https://github.com/jokob-sk/Pi.Alert/releases)

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

# 📥 Installation
<!--- --------------------------------------------------------------------- --->

 ⚠ Only tested as a [docker container - follow these instructions here](dockerfiles/README.md). 
 > Check out [leiweibau's fork](https://github.com/leiweibau/Pi.Alert/) if you want to install Pi.Alert on the server directly or original instructions for [pucherot's original code](https://github.com/pucherot/Pi.Alert/)

# 📑 Features   
  - Display:
    - Sessions, Connected devices, Favorites, Events, Presence, Concurrent devices, Down alerts, IP's
    - Manual Nmap scans, Optional speedtest for Device "Internet"
    - Simple Network relationship display
  - Maintenance tasks and Settings like:    
    - Theme Selection (blue, red, green, yellow, black, purple) and Light/Dark-Mode Switch        
    - DB maintenance, Backup, Restore tools and CSV Export / Import
    - Simple login Support
  - 🌟(Experimental) [Plugin system](https://github.com/jokob-sk/Pi.Alert/tree/main/front/plugins)
    - Create custom plugins with automatically generated settings and UI. 
    - Monitor anything for changes
    - Check the instructions carefully if you are up for a challenge! Current plugins include:
      - Detecting Rogue DHCP servers
      - Monitoring HTTP status changes of domains/URLs        

  | ![Screen 1][screen1] | ![Screen 2][screen2] | ![Screen 5][screen5]  |
  |----------------------|----------------------| ----------------------| 
  | ![Screen 3][screen3] | ![Screen 4][screen4] | ![Screen 6][screen6]  |  
  | ![Screen 8][screen8] | ![Report 2][report2] | ![Screen 9][screen9]  | 
 

### 🔗 Other Alternatives

  - [WatchYourLAN](https://github.com/aceberg/WatchYourLAN) - Lightweight network IP scanner with web GUI (Open source)
  - [Fing](https://www.fing.com/) - Network scanner app for your Internet security (Commercial, Phone App, Proprietary hardware)

### Old docs

Device Management [instructions](docs/DEVICE_MANAGEMENT.md) | Old Versions [History](docs/VERSIONS_HISTORY.md)

### License
  GPL 3.0 | [Read more here](LICENSE.txt) | Source of the [animated GIF (Loading Animation)](https://commons.wikimedia.org/wiki/File:Loading_Animation.gif) | Source of the [selfhosted Fonts](https://github.com/adobe-fonts/source-sans)
  
### 🥇 Special thanks 

  This code is a collaborative body of work, with special thanks to: 

   - 🏆 [pucherot/Pi.Alert](https://github.com/pucherot/Pi.Alert) is the original creator od PiAlert
      - [leiweibau](https://github.com/leiweibau/Pi.Alert): Dark mode (and much more)
      - [Macleykun](https://github.com/Macleykun): Help with Dockerfile clean-up
      - [Final-Hawk](https://github.com/Final-Hawk): Help with NTFY, styling and other fixes
      - [TeroRERO](https://github.com/terorero): Spanish translation      
      - Please see the [Git contributors](https://github.com/jokob-sk/Pi.Alert/graphs/contributors) for a full list of people and their contributions to the project

## ☕ Support me

<a href="https://github.com/sponsors/jokob-sk" target="_blank"><img src="https://i.imgur.com/X6p5ACK.png" alt="Sponsor Me on GitHub" style="height: 30px !important;width: 117px !important;" width="150px" ></a>
<a href="https://www.buymeacoffee.com/jokobsk" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 30px !important;width: 117px !important;" width="117px" height="30px" ></a>
<a href="https://www.patreon.com/user?u=84385063" target="_blank"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Patreon_logo_with_wordmark.svg/512px-Patreon_logo_with_wordmark.svg.png" alt="Support me on patreon" style="height: 30px !important;width: 117px !important;" width="117px" ></a>

BTC: 1N8tupjeCK12qRVU2XrV17WvKK7LCawyZM

<!--- --------------------------------------------------------------------- --->
[main]:    ./docs/img/devices_split.png       "Main screen"
[screen1]: ./docs/img/device_details.png      "Screen 1"
[screen2]: ./docs/img/events.png              "Screen 2"
[screen3]: ./docs/img/presence.png            "Screen 3"
[screen4]: ./docs/img/maintenance.png         "Screen 4"
[screen5]: ./docs/img/network.png             "Screen 5"
[screen6]: ./docs/img/settings.png            "Screen 6"
[screen7]: ./docs/img/help_faq.png            "Screen 7"
[screen8]: ./docs/img/plugins_webmon.png      "Screen 8"
[screen9]: ./docs/img/device_nmap.png         "Screen 9"
[report1]: ./docs/img/4_report_1.jpg          "Report sample 1"
[report2]: ./docs/img/4_report_2.jpg          "Report sample 2"
[main_dark]: /docs/img/1_devices_dark.jpg     "Main screen dark"
[maintain_dark]: /docs/img/5_maintain.jpg     "Maintain screen dark"

