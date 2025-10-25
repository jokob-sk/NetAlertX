[![Docker Size](https://img.shields.io/docker/image-size/jokobsk/netalertx?label=Size&logo=Docker&color=0aa8d2&logoColor=fff&style=for-the-badge)](https://hub.docker.com/r/jokobsk/netalertx)
[![Docker Pulls](https://img.shields.io/docker/pulls/jokobsk/netalertx?label=Pulls&logo=docker&color=0aa8d2&logoColor=fff&style=for-the-badge)](https://hub.docker.com/r/jokobsk/netalertx)
[![GitHub Release](https://img.shields.io/github/v/release/jokob-sk/NetAlertX?color=0aa8d2&logoColor=fff&logo=GitHub&style=for-the-badge)](https://github.com/jokob-sk/NetAlertX/releases)
[![Discord](https://img.shields.io/discord/1274490466481602755?color=0aa8d2&logoColor=fff&logo=Discord&style=for-the-badge)](https://discord.gg/NczTUTWyRr)
[![Home Assistant](https://img.shields.io/badge/Repo-blue?logo=home-assistant&style=for-the-badge&color=0aa8d2&logoColor=fff&label=Add)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Falexbelgium%2Fhassio-addons)

# NetAlertX - Network, presence scanner and alert framework

Get visibility of what's going on on your WIFI/LAN network and enable presence detection of important devices. Schedule scans for devices, port changes and get alerts if unknown devices or changes are found. Write your own [Plugin](https://github.com/jokob-sk/NetAlertX/tree/main/docs/PLUGINS.md#readme) with auto-generated UI and in-build notification system. Build out and easily maintain your network source of truth (NSoT).

## 📋 Table of Contents

- [Features](#-features)
- [Documentation](#-documentation)
- [Quick Start](#-quick-start)
- [Alternative Apps](#-other-alternative-apps)
- [Security & Privacy](#-security--privacy)
- [FAQ](#-faq)
- [Known Issues](#-known-issues)
- [Donations](#-donations)
- [Contributors](#-contributors)
- [Translations](#-translations)
- [License](#license)


## 🚀 Quick Start

To launch NetAlertX in seconds, replace `local_path` with the absolute path on your system that contains your `config` and `db` folders, then run::

```bash
docker run -d --rm --network=host \
  -v local_path/config:/app/config \
  -v local_path/db:/app/db \
  --mount type=tmpfs,target=/app/api \
  -e PUID=200 -e PGID=300 \
  -e TZ=Europe/Berlin \
  -e PORT=20211 \
  ghcr.io/jokob-sk/netalertx:latest
```

Need help configuring it? Check the [usage guide](https://github.com/jokob-sk/NetAlertX/blob/main/docs/README.md) or [full documentation](https://jokob-sk.github.io/NetAlertX/).

For Home Assistant users: [Click here to add NetAlertX](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Falexbelgium%2Fhassio-addons)

For other install methods, check the [installation docs](#-documentation)


| [📑 Docker guide](https://github.com/jokob-sk/NetAlertX/blob/main/dockerfiles/README.md) | [🚀 Releases](https://github.com/jokob-sk/NetAlertX/releases) | [📚 Docs](https://jokob-sk.github.io/NetAlertX/) | [🔌 Plugins](https://github.com/jokob-sk/NetAlertX/blob/main/docs/PLUGINS.md) | [🤖 Ask AI](https://gurubase.io/g/netalertx)
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

The app scans your network for **New devices**, **New connections** (re-connections), **Disconnections**, **"Always Connected" devices down**, Devices **IP changes** and **Internet IP address changes**. Discovery & scan methods include: **arp-scan**,  **Pi-hole - DB import**,  **Pi-hole - DHCP leases import**, **Generic DHCP leases import**, **UNIFI controller import**, **SNMP-enabled router import**. Check the [Plugins](https://github.com/jokob-sk/NetAlertX/tree/main/docs/PLUGINS.md#readme) docs for a full list of avaliable plugins. 

### Notification gateways

Send notifications to more than 80+ services, including Telegram via [Apprise](https://hub.docker.com/r/caronc/apprise), or use native [Pushsafer](https://www.pushsafer.com/), [Pushover](https://www.pushover.net/), or [NTFY](https://ntfy.sh/) publishers. 

### Integrations and Plugins

Feed your data and device changes into [Home Assistant](https://github.com/jokob-sk/NetAlertX/blob/main/docs/HOME_ASSISTANT.md), read [API endpoints](https://github.com/jokob-sk/NetAlertX/blob/main/docs/API.md), or use [Webhooks](https://github.com/jokob-sk/NetAlertX/blob/main/docs/WEBHOOK_N8N.md) to setup custom automation flows. You can also 
build your own scanners with the [Plugin system](https://github.com/jokob-sk/NetAlertX/tree/main/docs/PLUGINS.md#readme) in as little as [15 minutes](https://www.youtube.com/watch?v=cdbxlwiWhv8).

### Workflows

The [workflows module](https://github.com/jokob-sk/NetAlertX/blob/main/docs/WORKFLOWS.md) allows to automate repetitive tasks, making network management more efficient. Whether you need to assign newly discovered devices to a specific Network Node, auto-group devices from a given vendor, unarchive a device if detected online, or automatically delete devices, this module provides the flexibility to tailor the automations to your needs.


## 📚 Documentation
<!--- --------------------------------------------------------------------- --->

Supported browsers: Chrome, Firefox

- [[Installation] Docker](https://github.com/jokob-sk/NetAlertX/blob/main/dockerfiles/README.md) 
- [[Installation] Home Assistant](https://github.com/alexbelgium/hassio-addons/tree/master/netalertx) 
- [[Installation] Bare metal](https://github.com/jokob-sk/NetAlertX/blob/main/docs/HW_INSTALL.md) 
- [[Installation] Unraid App](https://unraid.net/community/apps) 
- [[Setup] Usage and Configuration](https://github.com/jokob-sk/NetAlertX/blob/main/docs/README.md)
- [[Development] API docs](https://github.com/jokob-sk/NetAlertX/blob/main/docs/API.md)
- [[Development] Custom Plugins](https://github.com/jokob-sk/NetAlertX/blob/main/docs/PLUGINS_DEV.md)

...or explore all the [documentation here](https://jokob-sk.github.io/NetAlertX/).

## 🔐 Security & Privacy

NetAlertX scans your local network and can store metadata about connected devices. By default, all data is stored **locally**. No information is sent to external services unless you explicitly configure notifications or integrations.

To further secure your installation:
- Run it behind a reverse proxy with authentication
- Use firewalls to restrict access to the web UI
- Regularly update to the latest version for security patches

See [Security Best Practices](https://github.com/jokob-sk/NetAlertX/security) for more details.


## ❓ FAQ

**Q: Why don’t I see any devices?**  
A: Ensure the container has proper network access (e.g., use `--network host` on Linux). Also check that your scan method is properly configured in the UI.

**Q: Does this work on Wi-Fi-only devices like Raspberry Pi?**  
A: Yes, but some scanners (e.g. ARP) work best on Ethernet. For Wi-Fi, try SNMP, DHCP, or Pi-hole import.

**Q: Will this send any data to the internet?**  
A: No. All scans and data remain local, unless you set up cloud-based notifications.

**Q: Can I use this without Docker?**  
A: Yes! You can install it bare-metal. See the [bare metal installation guide](https://github.com/jokob-sk/NetAlertX/blob/main/docs/HW_INSTALL.md).

**Q: Where is the data stored?**  
A: In the `/config` and `/db` folders, mapped in Docker. Back up these folders regularly.


## 🐞 Known Issues

- Some scanners (e.g. ARP) may not detect devices on different subnets. See the [Remote networks guide](https://github.com/jokob-sk/NetAlertX/blob/main/docs/REMOTE_NETWORKS.md) for workarounds.
- Wi-Fi-only networks may require alternate scanners for accurate detection.
- Notification throttling may be needed for large networks to prevent spam.
- On some systems, elevated permissions (like `CAP_NET_RAW`) may be needed for low-level scanning.

Check the [GitHub Issues](https://github.com/jokob-sk/NetAlertX/issues) for the latest bug reports and solutions and consult [the official documentation](https://jokob-sk.github.io/NetAlertX/).

## 📃 Everything else
<!--- --------------------------------------------------------------------- --->

### 📧 Get notified what's new

Get notified about a new release, what new functionality you can use and about breaking changes. 

![Follow and star][follow_star] 

### 🔀 Other Alternative Apps

- [PiAlert by leiweibau](https://github.com/leiweibau/Pi.Alert/) (maintained, bare-metal install)
- [WatchYourLAN](https://github.com/aceberg/WatchYourLAN) - Lightweight network IP scanner with web GUI (Open source)
- [Fing](https://www.fing.com/) - Network scanner app for your Internet security (Commercial, Phone App, Proprietary hardware)
- [NetBox](https://netboxlabs.com/) - Network management software (Commercial)

### 💙 Donations

Thank you to everyone who appreciates this tool and donates. 

<details>
  <summary>Click for more ways to donate</summary>
  
  <hr>

  | [![GitHub](https://i.imgur.com/emsRCPh.png)](https://github.com/sponsors/jokob-sk) | [![Buy Me A Coffee](https://i.imgur.com/pIM6YXL.png)](https://www.buymeacoffee.com/jokobsk) | [![Patreon](https://i.imgur.com/MuYsrq1.png)](https://www.patreon.com/user?u=84385063) | 
| --- | --- | --- | 

  - Bitcoin: `1N8tupjeCK12qRVU2XrV17WvKK7LCawyZM`
  - Ethereum: `0x6e2749Cb42F4411bc98501406BdcD82244e3f9C7`

  📧 Email me at [jokob@duck.com](mailto:jokob@duck.com?subject=NetAlertX) if you want to get in touch or if I should add other sponsorship platforms.

</details>

### 🏗 Contributors

This project would be nothing without the amazing work of the community, with special thanks to: 

> [pucherot/Pi.Alert](https://github.com/pucherot/Pi.Alert) (the original creator of PiAlert), [leiweibau](https://github.com/leiweibau/Pi.Alert): Dark mode (and much more), [Macleykun](https://github.com/Macleykun) (Help with Dockerfile clean-up), [vladaurosh](https://github.com/vladaurosh) for Alpine re-base help, [Final-Hawk](https://github.com/Final-Hawk) (Help with NTFY, styling and other fixes), [TeroRERO](https://github.com/terorero) (Spanish translations), [Data-Monkey](https://github.com/Data-Monkey), (Split-up of the python.py file and more), [cvc90](https://github.com/cvc90) (Spanish translation and various UI work) to name a few. Check out all the [amazing contributors](https://github.com/jokob-sk/NetAlertX/graphs/contributors). 

### 🌍 Translations 

Proudly using [Weblate](https://hosted.weblate.org/projects/pialert/). Help out and suggest languages in the [online portal of Weblate](https://hosted.weblate.org/projects/pialert/core/).

<a href="https://hosted.weblate.org/engage/pialert/">
  <img src="https://hosted.weblate.org/widget/pialert/core/multi-auto.svg" alt="Translation status" />
</a>

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
[sync_hub]:                 ./docs/img/sync_hub.png                       "Screen 8"
[notification_center]:      ./docs/img/notification_center.png            "Screen 8"
[sent_reports_text]:        ./docs/img/sent_reports_text.png              "Screen 8"
[device_nmap]:              ./docs/img/device_nmap.png                    "Screen 9"
[report1]:                  ./docs/img/report_sample.png                  "Report sample 1"
[main_dark]:                /docs/img/1_devices_dark.jpg                  "Main screen dark"
[maintain_dark]:            /docs/img/5_maintain.jpg                      "Maintain screen dark"
[follow_star]:              /docs/img/Follow_Releases_and_Star.gif        "Follow and Star"
