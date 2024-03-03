# 💻🔍 Network security scanner & notification framework

Get visibility of what's going on on your WIFI/LAN network. Scan for devices, port changes and get alerts if unknown devices or changes are found. Write your own [Plugins](https://github.com/jokob-sk/Pi.Alert/tree/main/front/plugins#readme) with auto-generated UI and in-build notification system. 

[![GitHub Committed](https://img.shields.io/github/last-commit/jokob-sk/Pi.Alert?color=40ba12&label=Committed&logo=GitHub&logoColor=fff)](https://github.com/jokob-sk/Pi.Alert)
[![Docker Size](https://img.shields.io/docker/image-size/jokobsk/pi.alert?label=Size&logo=Docker&color=0aa8d2&logoColor=fff)](https://hub.docker.com/r/jokobsk/pi.alert)
[![Docker Pulls](https://img.shields.io/docker/pulls/jokobsk/pi.alert?label=Pulls&logo=docker&color=0aa8d2&logoColor=fff)](https://hub.docker.com/r/jokobsk/pi.alert)
[![GitHub Release](https://img.shields.io/github/v/release/jokob-sk/Pi.Alert?color=0aa8d2&logoColor=fff&logo=GitHub)](https://github.com/jokob-sk/Pi.Alert/releases)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/jokob-sk?style=social)](https://github.com/sponsors/jokob-sk)

  | 🐳 [Docker hub](https://registry.hub.docker.com/r/jokobsk/pi.alert) |  📑 [Docker guide](https://github.com/jokob-sk/Pi.Alert/blob/main/dockerfiles/README.md) |🆕 [Release notes](https://github.com/jokob-sk/Pi.Alert/releases) | 📚 [All Docs](https://github.com/jokob-sk/Pi.Alert/tree/main/docs) | 
  |----------------------|----------------------| ----------------------|  ----------------------| 


  | ![Main screen][main] | ![Screen 1][screen1]  | ![Screen 5][screen5] |
  |----------------------|----------------------| ----------------------| 

<details>
  <summary>📷 Click for more screenshots</summary>

  | ![Screen 3][screen3] | ![Screen 4][screen4] | ![Screen 6][screen6]  |
  |----------------------|----------------------|----------------------|
  | ![Screen 8][screen8] | ![Report 2][report2] | ![Screen 9][screen9]  |

</details>

<details>
  <summary>❓ Why use PiAlert?</summary>

  <hr>

  Most of us don't know what's going on on our home network, but we want our family and data to be safe.  _Command-line tools_ are great, but the output can be _hard to understand_ and action if you are not a network specialist.

  PiAlert gives you peace of mind. _Visualize and immediately report 📬_ what is going on in your network - this is the first step to enhance your _network security 🔐_. 

  PiAlert combines several network and other scanning tools 🔍 with notifications 📧 into one user-friendly package 📦. 

  Set up a _kill switch ☠_ for your network via a smart plug with the available [Home Assistant](https://github.com/jokob-sk/Pi.Alert/blob/main/docs/HOME_ASSISTANT.md) integration. Implement custom automations with the [CSV device Exports 📤](https://github.com/jokob-sk/Pi.Alert/tree/main/front/plugins/csv_backup), [Webhooks](https://github.com/jokob-sk/Pi.Alert/blob/main/docs/WEBHOOK_N8N.md), or [API endpoints](https://github.com/jokob-sk/Pi.Alert/blob/main/docs/API.md) features. 

  Extend the app if you want to create your own scanner [Plugin](https://github.com/jokob-sk/Pi.Alert/tree/main/front/plugins#readme) and handle the results and notifications in PiAlert. 

  Looking forward to your contributions if you decide to share your work with the community ❤.

</details>

## Scan Methods, Notifications, Integration, Extension system

| Features    | Details    | 
|-------------|-------------|
|      🔍     |   The app scans your network for, **New devices**, **New connections** (re-connections), **Disconnections**, **"Always Connected" devices down**, Devices **IP changes** and **Internet IP address changes**. Discovery & scan methods include: **arp-scan**.  **Pi-hole - DB import**,  **Pi-hole - DHCP leases import**, **Generic DHCP leases import**. **UNIFI controller import**, **SNMP-enabled router import**. Check the [Plugins](https://github.com/jokob-sk/Pi.Alert/tree/main/front/plugins#readme) docs for more info on individual scans. |
|📧           | Send notifications to more than 80+ services, including Telegram via [Apprise](https://hub.docker.com/r/caronc/apprise), or use [Pushsafer](https://www.pushsafer.com/), [Pushover](https://www.pushover.net/), or [NTFY](https://ntfy.sh/). |
|🧩           | Feed your data and device changes into [Home Assistant](https://github.com/jokob-sk/Pi.Alert/blob/main/docs/HOME_ASSISTANT.md), read [API endpoints](https://github.com/jokob-sk/Pi.Alert/blob/main/docs/API.md), or use [Webhooks](https://github.com/jokob-sk/Pi.Alert/blob/main/docs/WEBHOOK_N8N.md) to setup custom automation flows.  |
|➕           | Build your own scanners with the [Plugin system](https://github.com/jokob-sk/Pi.Alert/tree/main/front/plugins#readme) |


## Installation & Documentation
<!--- --------------------------------------------------------------------- --->

| Docs        | Link    | 
|-------------|-------------|
| 📥🐳  | [Docker instructions](https://github.com/jokob-sk/Pi.Alert/blob/main/dockerfiles/README.md) 
| 📥💻  | [HW install (experimental 🧪)](https://github.com/jokob-sk/Pi.Alert/blob/main/docs/HW_INSTALL.md) |
| 📚     | [All Documentation](https://github.com/jokob-sk/Pi.Alert/blob/main/docs/README.md) (App Usage and Configuration) |
 
> Other Alternatives
>
> - Check out [leiweibau's on HW installed fork](https://github.com/leiweibau/Pi.Alert/) (maintained)
> - Check instructions for [pucherot's original code](https://github.com/pucherot/Pi.Alert/) (unmaintained)
> - [WatchYourLAN](https://github.com/aceberg/WatchYourLAN) - Lightweight network IP scanner with web GUI (Open source)
> - [Fing](https://www.fing.com/) - Network scanner app for your Internet security (Commercial, Phone App, Proprietary hardware)

## ❤ Support me for...

- I don't get burned out and the app survives longer🔥🤯
- Regular updates to keep your data and family safe 🔄 
- Better and more functionality➕
- Quicker and better support with issues 🆘

| [![GitHub](https://i.imgur.com/emsRCPh.png)](https://github.com/sponsors/jokob-sk) | [![Buy Me A Coffee](https://i.imgur.com/pIM6YXL.png)](https://www.buymeacoffee.com/jokobsk) | [![Patreon](https://i.imgur.com/MuYsrq1.png)](https://www.patreon.com/user?u=84385063) | 
| --- | --- | --- | 

<details>
  <summary>Click for more ways to donate</summary>
  
  <hr>

  - Bitcoin: `1N8tupjeCK12qRVU2XrV17WvKK7LCawyZM`
  - Ethereum: `0x6e2749Cb42F4411bc98501406BdcD82244e3f9C7`

  📧 Email me at [jokob@duck.com](mailto:jokob@duck.com?subject=PiAlert) if you want to get in touch or if I should add other sponsorship platforms.

</details>



### ⭐ Sponsors

[![GitHub Sponsors](https://img.shields.io/github/sponsors/jokob-sk?style=social)](https://github.com/sponsors/jokob-sk)

Thank you to all the wonderful people who are sponsoring this project (=preventing my burnout🔥🤯):

<!-- SPONSORS-LIST DO NOT MODIFY BELOW -->
| All Sponsors |
|---|

<!-- SPONSORS-LIST DO NOT MODIFY ABOVE -->

### 🙏Contributors

This project would be nothing without the amazing work of the community, with special thanks to: 

> [pucherot/Pi.Alert](https://github.com/pucherot/Pi.Alert) (the original creator of PiAlert), [leiweibau](https://github.com/leiweibau/Pi.Alert): Dark mode (and much more), [Macleykun](https://github.com/Macleykun) (Help with Dockerfile clean-up) [Final-Hawk](https://github.com/Final-Hawk) (Help with NTFY, styling and other fixes), [TeroRERO](https://github.com/terorero) (Spanish translations), [Data-Monkey](https://github.com/Data-Monkey), (Split-up of the python.py file and more), [cvc90](https://github.com/cvc90) (Spanish translation and various UI work) to name a few...

Here is every one that helped and contributed to this project:

<a href="https://github.com/jokob-sk/pi.alert/graphs/contributors">
  <img src="https://contri-graphy.yourselfhosted.com/graph?repo=jokob-sk/pi.alert&format=svg" />
</a>

## Everything else
<!--- --------------------------------------------------------------------- --->

### 🌍 Translations 

Proudly using [Weblate](https://hosted.weblate.org/projects/pialert/).

<a href="https://hosted.weblate.org/engage/pialert/">
  <img src="https://hosted.weblate.org/widget/pialert/core/multi-auto.svg" alt="Translation status" />
</a>

Help out and suggest languages in the [online portal of Weblate](https://hosted.weblate.org/projects/pialert/core/).

### License
>  GPL 3.0 | [Read more here](LICENSE.txt) | Source of the [animated GIF (Loading Animation)](https://commons.wikimedia.org/wiki/File:Loading_Animation.gif) | Source of the [selfhosted Fonts](https://github.com/adobe-fonts/source-sans)
  


<!--- --------------------------------------------------------------------- --->
[main]:    ./docs/img/devices_split.png       "Main screen"
[screen1]: ./docs/img/device_details.png      "Screen 1"
[screen2]: ./docs/img/events.png              "Screen 2"
[screen3]: ./docs/img/presence.png            "Screen 3"
[screen4]: ./docs/img/maintenance.png         "Screen 4"
[screen5]: ./docs/img/network.png             "Screen 5"
[screen6]: ./docs/img/settings.png            "Screen 6"
[screen7]: ./docs/img/help_faq.png            "Screen 7"
[screen8]: ./docs/img/plugins_rogue_dhcp.png  "Screen 8"
[screen9]: ./docs/img/device_nmap.png         "Screen 9"
[report1]: ./docs/img/4_report_1.jpg          "Report sample 1"
[report2]: ./docs/img/4_report_2.jpg          "Report sample 2"
[main_dark]: /docs/img/1_devices_dark.jpg     "Main screen dark"
[maintain_dark]: /docs/img/5_maintain.jpg     "Maintain screen dark"

