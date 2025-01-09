[![Docker Size](https://img.shields.io/docker/image-size/jokobsk/netalertx?label=Size&logo=Docker&color=0aa8d2&logoColor=fff&style=for-the-badge)](https://hub.docker.com/r/jokobsk/netalertx)
[![Docker Pulls](https://img.shields.io/docker/pulls/jokobsk/netalertx?label=Pulls&logo=docker&color=0aa8d2&logoColor=fff&style=for-the-badge)](https://hub.docker.com/r/jokobsk/netalertx)
[![GitHub Release](https://img.shields.io/github/v/release/jokob-sk/NetAlertX?color=0aa8d2&logoColor=fff&logo=GitHub&style=for-the-badge)](https://github.com/jokob-sk/NetAlertX/releases)
[![Discord](https://img.shields.io/discord/1274490466481602755?color=0aa8d2&logoColor=fff&logo=Discord&style=for-the-badge)](https://discord.gg/NczTUTWyRr)

# NetAlertX - Network scanner & notification framework

Get visibility of what's going on on your WIFI/LAN network and enable presence detection of important devices. Schedule scans for devices, port changes and get alerts if unknown devices or changes are found. Write your own [Plugins](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins#readme) with auto-generated UI and in-build notification system. Build out and easily maintain your network source of truth (NSoT).


| [📑 Docker guide](https://github.com/jokob-sk/NetAlertX/blob/main/dockerfiles/README.md) | [🚀 Releases](https://github.com/jokob-sk/NetAlertX/releases) | [📚 Docs](https://github.com/jokob-sk/NetAlertX/tree/main/docs) | [🔌 Plugins](https://github.com/jokob-sk/NetAlertX/blob/main/front/plugins/README.md) | [🤖 Ask AI](https://gurubase.io/g/netalertx)
|----------------------| ----------------------|  ----------------------| ----------------------| ----------------------| 

![showcase][showcase] 

<details>
  <summary>📷 Click for more screenshots</summary>

  | ![Main screen][main] | ![device_details 1][device_details]  | ![Screen network][network] |
  |----------------------|----------------------|----------------------|
  | ![presence][presence] | ![maintenance][maintenance] | ![settings][settings]  |
  | ![sync_hub][sync_hub] | ![report1][report1] | ![device_nmap][device_nmap]  |

  Head to [https://netalertx.com/](https://netalertx.com/) for even more gifs and screenshots 📷.

</details>

## 📦 Features

### Scanners

The app scans your network for, **New devices**, **New connections** (re-connections), **Disconnections**, **"Always Connected" devices down**, Devices **IP changes** and **Internet IP address changes**. Discovery & scan methods include: **arp-scan**,  **Pi-hole - DB import**,  **Pi-hole - DHCP leases import**, **Generic DHCP leases import**. **UNIFI controller import**, **SNMP-enabled router import**. Check the [Plugins](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins#readme) docs for more info on individual scans. 

### Notification gateways

Send notifications to more than 80+ services, including Telegram via [Apprise](https://hub.docker.com/r/caronc/apprise), or use [Pushsafer](https://www.pushsafer.com/), [Pushover](https://www.pushover.net/), or [NTFY](https://ntfy.sh/). 

### Integrations and Plugins

Feed your data and device changes into [Home Assistant](https://github.com/jokob-sk/NetAlertX/blob/main/docs/HOME_ASSISTANT.md), read [API endpoints](https://github.com/jokob-sk/NetAlertX/blob/main/docs/API.md), or use [Webhooks](https://github.com/jokob-sk/NetAlertX/blob/main/docs/WEBHOOK_N8N.md) to setup custom automation flows.  |
Build your own scanners with the [Plugin system](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins#readme) |


## 📚 Documentation
<!--- --------------------------------------------------------------------- --->

Supported browsers: Chrome, Firefox

- [[Installation] Docker](https://github.com/jokob-sk/NetAlertX/blob/main/dockerfiles/README.md) 
- [[Installation] Bare metal](https://github.com/jokob-sk/NetAlertX/blob/main/docs/HW_INSTALL.md) 
- [[Installation] Unraid App](https://unraid.net/community/apps) 
- [[Setup] Usage and Configuration](https://github.com/jokob-sk/NetAlertX/blob/main/docs/README.md)
- [[Development] API docs](https://github.com/jokob-sk/NetAlertX/blob/main/docs/API.md)
- [[Development] Custom Plugins](https://github.com/jokob-sk/NetAlertX/blob/main/docs/PLUGINS_DEV.md)

## 🔔 Get notified what's new

Get notified about a new release, what new functionality you can use and about breaking changes. 

![Follow and star][follow_star] 

### ⭐ Sponsors

[![GitHub Sponsors](https://img.shields.io/github/sponsors/jokob-sk?style=social)](https://github.com/sponsors/jokob-sk)

Thank you to all the wonderful people who are sponsoring this project (private sponsors are hidden). 

<!-- SPONSORS-LIST DO NOT MODIFY BELOW -->
| All Sponsors |
|---|

<!-- SPONSORS-LIST DO NOT MODIFY ABOVE -->

<details>
  <summary>Click for more ways to donate</summary>
  
  <hr>

  | [![GitHub](https://i.imgur.com/emsRCPh.png)](https://github.com/sponsors/jokob-sk) | [![Buy Me A Coffee](https://i.imgur.com/pIM6YXL.png)](https://www.buymeacoffee.com/jokobsk) | [![Patreon](https://i.imgur.com/MuYsrq1.png)](https://www.patreon.com/user?u=84385063) | 
| --- | --- | --- | 

  - Bitcoin: `1N8tupjeCK12qRVU2XrV17WvKK7LCawyZM`
  - Ethereum: `0x6e2749Cb42F4411bc98501406BdcD82244e3f9C7`

  📧 Email me at [jokob@duck.com](mailto:jokob@duck.com?subject=NetAlertX) if you want to get in touch or if I should add other sponsorship platforms.

</details>

### 🙏Contributors

This project would be nothing without the amazing work of the community, with special thanks to: 

> [pucherot/Pi.Alert](https://github.com/pucherot/Pi.Alert) (the original creator of PiAlert), [leiweibau](https://github.com/leiweibau/Pi.Alert): Dark mode (and much more), [Macleykun](https://github.com/Macleykun) (Help with Dockerfile clean-up), [vladaurosh](https://github.com/vladaurosh) for Alpine re-base help, [Final-Hawk](https://github.com/Final-Hawk) (Help with NTFY, styling and other fixes), [TeroRERO](https://github.com/terorero) (Spanish translations), [Data-Monkey](https://github.com/Data-Monkey), (Split-up of the python.py file and more), [cvc90](https://github.com/cvc90) (Spanish translation and various UI work) to name a few. Check out all the [amazing contributors](https://github.com/jokob-sk/NetAlertX/graphs/contributors). 


## 📃 Everything else
<!--- --------------------------------------------------------------------- --->

### Other Alternative Apps

- [PiAlert by leiweibau](https://github.com/leiweibau/Pi.Alert/) (maintained, bare-metal install)
- [WatchYourLAN](https://github.com/aceberg/WatchYourLAN) - Lightweight network IP scanner with web GUI (Open source)
- [Fing](https://www.fing.com/) - Network scanner app for your Internet security (Commercial, Phone App, Proprietary hardware)
- [NetBox](https://netboxlabs.com/) - Network management software (Commercial)

### 🌍 Translations 

Proudly using [Weblate](https://hosted.weblate.org/projects/pialert/).

<a href="https://hosted.weblate.org/engage/pialert/">
  <img src="https://hosted.weblate.org/widget/pialert/core/multi-auto.svg" alt="Translation status" />
</a>

Help out and suggest languages in the [online portal of Weblate](https://hosted.weblate.org/projects/pialert/core/).

### License
>  GPL 3.0 | [Read more here](LICENSE.txt) | Source of the [animated GIF (Loading Animation)](https://commons.wikimedia.org/wiki/File:Loading_Animation.gif) | Source of the [selfhosted Fonts](https://github.com/adobe-fonts/source-sans)
  


<!--- --------------------------------------------------------------------- --->
[main]:                     ./docs/img/devices_split.png                  "Main screen"
[device_details]:           ./docs/img/device_details.png                 "Screen 1"
[events]:                   ./docs/img/events.png                         "Screen 2"
[presence]:                 ./docs/img/presence.png                       "Screen 3"
[maintenance]:              ./docs/img/maintenance.png                    "Screen 4"
[network]:                  ./docs/img/network.png                        "Screen 5"
[settings]:                 ./docs/img/settings.png                       "Screen 6"
[showcase]:                 ./docs/img/showcase.gif                       "Screen 6"
[help_faq]:                 ./docs/img/help_faq.png                       "Screen 7"
[sync_hub]:                 ./docs/img/sync_hub.png                       "Screen 8"
[notification_center]:      ./docs/img/notification_center.png            "Screen 8"
[sent_reports_text]:        ./docs/img/sent_reports_text.png              "Screen 8"
[device_nmap]:              ./docs/img/device_nmap.png                    "Screen 9"
[report1]:                  ./docs/img/report_sample.png                  "Report sample 1"
[main_dark]:                /docs/img/1_devices_dark.jpg                  "Main screen dark"
[maintain_dark]:            /docs/img/5_maintain.jpg                      "Maintain screen dark"
[follow_star]:              /docs/img/Follow_Releases_and_Star.gif        "Follow and Star"

