[![GitHub Committed](https://img.shields.io/github/last-commit/jokob-sk/NetAlertX?color=40ba12&label=Committed&logo=GitHub&logoColor=fff)](https://github.com/jokob-sk/NetAlertX)
[![Docker Size](https://img.shields.io/docker/image-size/jokobsk/netalertx?label=Size&logo=Docker&color=0aa8d2&logoColor=fff)](https://hub.docker.com/r/jokobsk/netalertx)
[![Docker Pulls](https://img.shields.io/docker/pulls/jokobsk/netalertx?label=Pulls&logo=docker&color=0aa8d2&logoColor=fff)](https://hub.docker.com/r/jokobsk/netalertx)
![GitHub Release](https://img.shields.io/github/v/release/jokob-sk/NetAlertX?color=0aa8d2&logoColor=fff&logo=GitHub)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/jokob-sk?style=social)](https://github.com/sponsors/jokob-sk)

# NetAlertX 🖧🔍 Network scanner & notification framework

  | 🐳 [Docker hub](https://registry.hub.docker.com/r/jokobsk/netalertx) |  📑 [Docker guide](https://github.com/jokob-sk/NetAlertX/blob/main/dockerfiles/README.md) |🆕 [Release notes](https://github.com/jokob-sk/NetAlertX/releases) | 📚 [All Docs](https://github.com/jokob-sk/NetAlertX/tree/main/docs) |
  |----------------------|----------------------| ----------------------|  ----------------------| 

<a href="https://raw.githubusercontent.com/jokob-sk/NetAlertX/main/docs/img/GENERAL/github_social_image.jpg" target="_blank">
  <img src="https://raw.githubusercontent.com/jokob-sk/NetAlertX/main/docs/img/GENERAL/github_social_image.jpg" width="1000px" />
</a>

Head to [https://netalertx.com/](https://netalertx.com/) for more gifs and screenshots 📷.

> [!NOTE]
> There is also an experimental 🧪 [bare-metal install](https://github.com/jokob-sk/NetAlertX/blob/main/docs/HW_INSTALL.md) method available. 

## 📕 Basic Usage 

> [!WARNING]
> You will have to run the container on the `host` network.

```yaml
docker run -d --rm --network=host \
  -v local/path/config:/app/config \
  -v local/path/db:/app/db \
  -e TZ=Europe/Berlin \
  -e PORT=20211 \
  jokobsk/netalertx:latest
```
- The initial scan can take up to 15min (with 50 devices and MQTT). Subsequent ones 3 and 5 minutes so wait that long for all of the scans to run.

### Docker environment variables

| Variable | Description | Default |
| :------------- |:-------------| -----:|
| `PORT`      |Port of the web interface  |  `20211` |
| `LISTEN_ADDR`      |Set the specific IP Address for the listener address for the nginx webserver (web interface). This could be useful when using multiple subnets to hide the web interface from all untrusted networks. |  `0.0.0.0` |
|`TZ` |Time zone to display stats correctly. Find your time zone [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)  |  `Europe/Berlin` |
|`ALWAYS_FRESH_INSTALL` | Setting  to `true` will delete the content of the `/db` & `/config` folders. For testing purposes. Can be coupled with [watchtower](https://github.com/containrrr/watchtower) to have an always freshly installed `netalertx`/`-dev` image.   |    `N/A` |

### Docker paths

> [!NOTE]
> See also [Backup strategies](https://github.com/jokob-sk/NetAlertX/blob/main/docs/BACKUPS.md).   

| Required | Path | Description |
| :------------- | :------------- | :-------------| 
| ✅ | `:/app/config` | Folder which will contain the `app.conf` & `devices.csv` ([read about devices.csv](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DEVICES_BULK_EDITING.md)) files (see below for details).  | 
| ✅ | `:/app/db` | Folder which will contain the `app.db` file  | 
| | `:/app/front/log` |  Logs folder useful for debugging if you have issues setting up the container  | 
| | `:/etc/pihole/pihole-FTL.db` |  PiHole's `pihole-FTL.db` database file. Required if you want to use PiHole DB mapping.  | 
| | `:/etc/pihole/dhcp.leases` |  PiHole's `dhcp.leases` file. Required if you want to use PiHole `dhcp.leases` file. This has to be matched with a corresponding `DHCPLSS_paths_to_check` setting entry (the path in the container must contain `pihole`)| 
| | `:/app/front/api` |  A simple [API endpoint](https://github.com/jokob-sk/NetAlertX/blob/main/docs/API.md) containing static (but regularly updated) json and other files.   | 
| | `:/app/front/plugins/<plugin>/ignore_plugin` | Map a file `ignore_plugin` to ignore a plugin. Plugins can be soft-disabled via settings. More in the [Plugin docs](https://github.com/jokob-sk/NetAlertX/blob/main/front/plugins/README.md).  | 
| | `:/etc/resolv.conf` | Use a custom `resolv.conf` file for [better name resolution](https://github.com/jokob-sk/NetAlertX/blob/main/docs/REVERSE_DNS.md).  | 

> Use separate `db` and `config` directories, don't nest them.

### (If UI is not available) Modify the config (`app.conf`) 

- The preferred way is to manage the configuration via the Settings section in the UI.
- You can modify [app.conf](https://github.com/jokob-sk/NetAlertX/tree/main/config) directly, if needed.
- If unavailable, the app generates a default `app.conf` and `app.db` file on the first run.

### ⚙ Important settings

These are the most important settings to get at least some output in your Devices screen. Usually, only one approach is used, but you can combine these approaches.

| Scan method | Setting | Description |
| :------------- | :------------- | :-------------| 
| arp-scan, nmap-scan | `SCAN_SUBNETS` | See the documentation on how [to setup SUBNETS, VLANs & limitations](https://github.com/jokob-sk/NetAlertX/blob/main/docs/SUBNETS.md) |
| PiHole | `PIHOLE_RUN` | There are 2 approaches how to get PiHole devices imported. Via the PiHole import (`PIHOLE`) plugin or DHCP leases (`DHCPLSS`) plugin. The `PIHOLE` plugin requires you to map the PiHole database, as mentioned above. |
| dhcp.leases | `DHCPLSS_RUN` | You need to map `:/etc/myfiles/dhcp.leases` in the `docker-compose.yml` file if you enable this setting. This path has to be matched with a corresponding `DHCPLSS_paths_to_check` setting entry (check the [DHCPLSS plugin readme](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/dhcp_leases#overview) for details). |


> [!NOTE]
> It's recommended to use the same schedule interval for all plugins responsible for discovering new devices.


#### 🧭 Community guides

Use the official installation guides at first and use community content as supplementary material. Open an issue if you'd like to add your link to the list 🙏 

- ▶ [Home Lab Network Monitoring - Scotti-BYTE Enterprise Consulting Services](https://www.youtube.com/watch?v=0DryhzrQSJA) (July 2024)
- 📄 [How to Install NetAlertX on Your Synology NAS - Marius hosting](https://mariushosting.com/how-to-install-pi-alert-on-your-synology-nas/) (Updated frequently)
- 📄 [Using the PiAlert Network Security Scanner on a Raspberry Pi - PiMyLifeUp](https://pimylifeup.com/raspberry-pi-pialert/)
- ▶ [How to Setup Pi.Alert on Your Synology NAS - Digital Aloha](https://www.youtube.com/watch?v=M4YhpuRFaUg) 
- 📄 [시놀/헤놀에서 네트워크 스캐너 Pi.Alert Docker로 설치 및 사용하기 (Korean)](https://blog.dalso.org/article/%EC%8B%9C%EB%86%80-%ED%97%A4%EB%86%80%EC%97%90%EC%84%9C-%EB%84%A4%ED%8A%B8%EC%9B%8C%ED%81%AC-%EC%8A%A4%EC%BA%90%EB%84%88-pi-alert-docker%EB%A1%9C-%EC%84%A4%EC%B9%98-%EB%B0%8F-%EC%82%AC%EC%9A%A9) (July 2023)
- 📄 [网络入侵探测器Pi.Alert (Chinese)](https://codeantenna.com/a/VgUvIAjZ7J) (May 2023)
- ▶ [Pi.Alert auf Synology & Docker by - Jürgen Barth (German)](https://www.youtube.com/watch?v=-ouvA2UNu-A) (March 2023)
- ▶ [Top Docker Container for Home Server Security - VirtualizationHowto](https://www.youtube.com/watch?v=tY-w-enLF6Q) (March 2023)
- ▶ [Pi.Alert or WatchYourLAN can alert you to unknown devices appearing on your WiFi or LAN network - Danie van der Merwe](https://www.youtube.com/watch?v=v6an9QG2xF0) (November 2022)

> Ordered by last update time. 
 
### **Common issues** 

💡 Before creating a new issue, please check if a similar issue was [already resolved](https://github.com/jokob-sk/NetAlertX/issues?q=is%3Aissue+is%3Aclosed). 

⚠ Check also common issues and [debugging tips](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DEBUG_TIPS.md). 

> [!NOTE]
> You can bulk-update devices via the [CSV import method](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DEVICES_BULK_EDITING.md).

## 📄 docker-compose.yml Examples

### Example 1

```yaml
version: "3"
services:
  netalertx:
    container_name: netalertx
    # use the below line if you want to test the latest dev image
    # image: "jokobsk/netalertx-dev:latest" 
    image: "jokobsk/netalertx:latest"      
    network_mode: "host"        
    restart: unless-stopped
    volumes:
      - local/path/config:/app/config
      - local/path/db:/app/db      
      # (optional) useful for debugging if you have issues setting up the container
      - local/path/logs:/app/front/log
    environment:
      - TZ=Europe/Berlin      
      - PORT=20211
```

To run the container execute: `sudo docker-compose up -d`

### Example 2

Example by [SeimuS](https://github.com/SeimusS).

```yaml
  netalertx:
    container_name: NetAlertX
    hostname: NetAlertX
    privileged: true
    # use the below line if you want to test the latest dev image
    # image: "jokobsk/netalertx-dev:latest" 
    image: jokobsk/netalertx:latest
    environment:
      - TZ=Europe/Bratislava
    restart: always
    volumes:
      - ./netalertx/db:/app/db
      - ./netalertx/config:/app/config
    network_mode: host
```

To run the container execute: `sudo docker-compose up -d`

### Example 3

`docker-compose.yml` 

```yaml
version: "3"
services:
  netalertx:
    container_name: netalertx
    # use the below line if you want to test the latest dev image
    # image: "jokobsk/netalertx-dev:latest" 
    image: "jokobsk/netalertx:latest"      
    network_mode: "host"        
    restart: unless-stopped
    volumes:
      - ${APP_DATA_LOCATION}/netalertx/config:/app/config
      - ${APP_DATA_LOCATION}/netalertx/db/:/app/db/      
      # (optional) useful for debugging if you have issues setting up the container
      - ${LOGS_LOCATION}:/app/front/log
    environment:
      - TZ=${TZ}      
      - PORT=${PORT}
```

`.env` file

```yaml
#GLOBAL PATH VARIABLES

APP_DATA_LOCATION=/path/to/docker_appdata
APP_CONFIG_LOCATION=/path/to/docker_config
LOGS_LOCATION=/path/to/docker_logs

#ENVIRONMENT VARIABLES

TZ=Europe/Paris
PORT=20211

#DEVELOPMENT VARIABLES

DEV_LOCATION=/path/to/local/source/code
```

To run the container execute: `sudo docker-compose --env-file /path/to/.env up`

### Example 4

Courtesy of [pbek](https://github.com/pbek). The volume `netalertx_db` is used by the db directory. The two config files are mounted directly from a local folder to their places in the config folder. You can backup the `docker-compose.yaml` folder and the docker volumes folder.

```yaml
  netalertx:
    # use the below line if you want to test the latest dev image
    # image: "jokobsk/netalertx-dev:latest" 
    image: jokobsk/netalertx
    ports:
      - "80:20211/tcp"
    environment:
      - TZ=Europe/Vienna
    networks:
      local:
        ipv4_address: 192.168.1.2
    restart: unless-stopped
    volumes:
      - netalertx_db:/app/db
      - ./netalertx/:/app/config/      
```

## 🏅 Recognitions

Big thanks to <a href="https://github.com/Macleykun">@Macleykun</a> & for help and tips & tricks for Dockerfile(s) and <a href="https://github.com/vladaurosh">@vladaurosh</a> for Alpine re-base help.

## ❤ Support me 

| [![GitHub](https://i.imgur.com/emsRCPh.png)](https://github.com/sponsors/jokob-sk) | [![Buy Me A Coffee](https://i.imgur.com/pIM6YXL.png)](https://www.buymeacoffee.com/jokobsk) | [![Patreon](https://i.imgur.com/MuYsrq1.png)](https://www.patreon.com/user?u=84385063) | 
| --- | --- | --- | 

- Bitcoin: `1N8tupjeCK12qRVU2XrV17WvKK7LCawyZM`
- Ethereum: `0x6e2749Cb42F4411bc98501406BdcD82244e3f9C7`

> 📧 Email me at [jokob@duck.com](mailto:jokob@duck.com?subject=NetAlertX) if you want to get in touch or if I should add other sponsorship platforms.