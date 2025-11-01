[![Docker Size](https://img.shields.io/docker/image-size/jokobsk/netalertx?label=Size&logo=Docker&color=0aa8d2&logoColor=fff&style=for-the-badge)](https://hub.docker.com/r/jokobsk/netalertx)
[![Docker Pulls](https://img.shields.io/docker/pulls/jokobsk/netalertx?label=Pulls&logo=docker&color=0aa8d2&logoColor=fff&style=for-the-badge)](https://hub.docker.com/r/jokobsk/netalertx)
[![GitHub Release](https://img.shields.io/github/v/release/jokob-sk/NetAlertX?color=0aa8d2&logoColor=fff&logo=GitHub&style=for-the-badge)](https://github.com/jokob-sk/NetAlertX/releases)
[![Discord](https://img.shields.io/discord/1274490466481602755?color=0aa8d2&logoColor=fff&logo=Discord&style=for-the-badge)](https://discord.gg/NczTUTWyRr)
[![Home Assistant](https://img.shields.io/badge/Repo-blue?logo=home-assistant&style=for-the-badge&color=0aa8d2&logoColor=fff&label=Add)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Falexbelgium%2Fhassio-addons)

# NetAlertX - Network scanner & notification framework

| [📑 Docker guide](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DOCKER_INSTALLATION.md) | [🚀 Releases](https://github.com/jokob-sk/NetAlertX/releases) | [📚 Docs](https://jokob-sk.github.io/NetAlertX/) | [🔌 Plugins](https://github.com/jokob-sk/NetAlertX/blob/main/docs/PLUGINS.md) | [🤖 Ask AI](https://gurubase.io/g/netalertx)
|----------------------| ----------------------|  ----------------------| ----------------------| ----------------------| 

<a href="https://raw.githubusercontent.com/jokob-sk/NetAlertX/main/docs/img/GENERAL/github_social_image.jpg" target="_blank">
  <img src="https://raw.githubusercontent.com/jokob-sk/NetAlertX/main/docs/img/GENERAL/github_social_image.jpg" width="1000px" />
</a>

Head to [https://netalertx.com/](https://netalertx.com/) for more gifs and screenshots 📷.

> [!NOTE]
> There is also an experimental 🧪 [bare-metal install](https://github.com/jokob-sk/NetAlertX/blob/main/docs/HW_INSTALL.md) method available. 

## 📕 Basic Usage 

> [!WARNING]
> You will have to run the container on the `host` network and specify `SCAN_SUBNETS` unless you use other [plugin scanners](https://github.com/jokob-sk/NetAlertX/blob/main/docs/PLUGINS.md). The initial scan can take a few minutes, so please wait 5-10 minutes for the initial discovery to finish.

```yaml
docker run -d --rm --network=host \
  -v local_path/config:/app/config \
  -v local_path/db:/app/db \
  --mount type=tmpfs,target=/app/api \
  -e PUID=200 -e PGID=300 \
  -e TZ=Europe/Berlin \
  -e PORT=20211 \
  ghcr.io/jokob-sk/netalertx:latest
```

See alternative [docked-compose examples](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DOCKER_COMPOSE.md).

### Docker environment variables

| Variable | Description | Example Value |
| :------------- |:------------------------| -----:|
| `PORT`      |Port of the web interface  |  `20211` |
| `PUID`      |Application User UID  |  `102` |
| `PGID`      |Application User GID  |  `82` |
| `LISTEN_ADDR`      |Set the specific IP Address for the listener address for the nginx webserver (web interface). This could be useful when using multiple subnets to hide the web interface from all untrusted networks. |  `0.0.0.0` |
|`TZ` |Time zone to display stats correctly. Find your time zone [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)  |  `Europe/Berlin` |
|`LOADED_PLUGINS` | Default [plugins](https://github.com/jokob-sk/NetAlertX/blob/main/docs/PLUGINS.md) to load. Plugins cannot be loaded with `APP_CONF_OVERRIDE`, you need to use this variable instead and then specify the plugins settings with `APP_CONF_OVERRIDE`. |  `["PIHOLE","ASUSWRT"]` |
|`APP_CONF_OVERRIDE` | JSON override for settings (except `LOADED_PLUGINS`).   |  `{"SCAN_SUBNETS":"['192.168.1.0/24 --interface=eth1']","GRAPHQL_PORT":"20212"}` |
|`ALWAYS_FRESH_INSTALL` | ⚠ If `true` will delete the content of the `/db` & `/config` folders. For testing purposes. Can be coupled with [watchtower](https://github.com/containrrr/watchtower) to have an always freshly installed `netalertx`/`netalertx-dev` image.   |    `true` |

> You can override the default GraphQL port setting `GRAPHQL_PORT` (set to `20212`) by using the `APP_CONF_OVERRIDE` env variable. `LOADED_PLUGINS` and settings in `APP_CONF_OVERRIDE` can be specified via the UI as well.

### Docker paths

> [!NOTE]
> See also [Backup strategies](https://github.com/jokob-sk/NetAlertX/blob/main/docs/BACKUPS.md).   

| Required | Path | Description |
| :------------- | :------------- | :-------------| 
| ✅ | `:/app/config` | Folder which will contain the `app.conf` & `devices.csv` ([read about devices.csv](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DEVICES_BULK_EDITING.md)) files  | 
| ✅ | `:/app/db` | Folder which will contain the `app.db` database file  | 
| | `:/app/log` |  Logs folder useful for debugging if you have issues setting up the container  | 
| | `:/app/api` |  A simple [API endpoint](https://github.com/jokob-sk/NetAlertX/blob/main/docs/API.md) containing static (but regularly updated) json and other files.   | 
| | `:/app/front/plugins/<plugin>/ignore_plugin` | Map a file `ignore_plugin` to ignore a plugin. Plugins can be soft-disabled via settings. More in the [Plugin docs](https://github.com/jokob-sk/NetAlertX/blob/main/docs/PLUGINS.md).  | 
| | `:/etc/resolv.conf` | Use a custom `resolv.conf` file for [better name resolution](https://github.com/jokob-sk/NetAlertX/blob/main/docs/REVERSE_DNS.md).  | 

> Use separate `db` and `config` directories, do not nest them.

### Initial setup

- If unavailable, the app generates a default `app.conf` and `app.db` file on the first run.
- The preferred way is to manage the configuration via the Settings section in the UI, if UI is inaccessible you can modify [app.conf](https://github.com/jokob-sk/NetAlertX/tree/main/back) in the `/app/config/` folder directly 

#### Setting up scanners

You have to specify which network(s) should be scanned. This is done by entering subnets that are accessible from the host. If you use the default `ARPSCAN` plugin, you have to specify at least one valid subnet and interface in the `SCAN_SUBNETS` setting. See the documentation on [How to set up multiple SUBNETS, VLANs and what are limitations](https://github.com/jokob-sk/NetAlertX/blob/main/docs/SUBNETS.md) for troubleshooting and more advanced scenarios. 

If you are running PiHole you can synchronize devices directly. Check the [PiHole configuration guide](https://github.com/jokob-sk/NetAlertX/blob/main/docs/PIHOLE_GUIDE.md) for details. 

> [!NOTE]
> You can bulk-import devices via the [CSV import method](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DEVICES_BULK_EDITING.md).

#### Community guides

You can read or watch several [community configuration guides](https://github.com/jokob-sk/NetAlertX/blob/main/docs/COMMUNITY_GUIDES.md) in Chinese, Korean, German, or French. 

> Please note these might be outdated. Rely on official documentation first. 
 
#### Common issues

- Before creating a new issue, please check if a similar issue was [already resolved](https://github.com/jokob-sk/NetAlertX/issues?q=is%3Aissue+is%3Aclosed). 
- Check also common issues and [debugging tips](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DEBUG_TIPS.md). 

## 💙 Support me 

| [![GitHub](https://i.imgur.com/emsRCPh.png)](https://github.com/sponsors/jokob-sk) | [![Buy Me A Coffee](https://i.imgur.com/pIM6YXL.png)](https://www.buymeacoffee.com/jokobsk) | [![Patreon](https://i.imgur.com/MuYsrq1.png)](https://www.patreon.com/user?u=84385063) | 
| --- | --- | --- | 

- Bitcoin: `1N8tupjeCK12qRVU2XrV17WvKK7LCawyZM`
- Ethereum: `0x6e2749Cb42F4411bc98501406BdcD82244e3f9C7`

> 📧 Email me at [netalertx@gmail.com](mailto:netalertx@gmail.com?subject=NetAlertX Donations) if you want to get in touch or if I should add other sponsorship platforms.
