[![Docker](https://img.shields.io/github/workflow/status/jokob-sk/Pi.Alert/docker?label=Build&logo=GitHub)](https://github.com/jokob-sk/Pi.Alert/actions/workflows/docker.yml)
[![GitHub Committed](https://img.shields.io/github/last-commit/jokob-sk/Pi.Alert?color=40ba12&label=Committed&logo=GitHub&logoColor=fff)](https://github.com/jokob-sk/Pi.Alert)
[![Docker Size](https://img.shields.io/docker/image-size/jokobsk/pi.alert?label=Size&logo=Docker&color=0aa8d2&logoColor=fff)](https://hub.docker.com/r/jokobsk/pi.alert)
[![Docker Pulls](https://img.shields.io/docker/pulls/jokobsk/pi.alert?label=Pulls&logo=docker&color=0aa8d2&logoColor=fff)](https://hub.docker.com/r/jokobsk/pi.alert)
[![Docker Pushed](https://img.shields.io/badge/dynamic/json?color=0aa8d2&logoColor=fff&label=Pushed&query=last_updated&url=https%3A%2F%2Fhub.docker.com%2Fv2%2Frepositories%2Fjokobsk%2Fpi.alert%2F&logo=docker&link=http://left&link=https://hub.docker.com/repository/docker/jokobsk/pi.alert)](https://hub.docker.com/r/jokobsk/pi.alert)

# 🐳 A docker image for Pi.Alert 


🐳 [Docker hub](https://registry.hub.docker.com/r/jokobsk/pi.alert) | 📄 [Dockerfile](https://github.com/jokob-sk/Pi.Alert/blob/main/Dockerfile) | 📚 [Docker instructions](https://github.com/jokob-sk/Pi.Alert/blob/main//dockerfiles/README.md)

## ℹ Basic Usage 

### pialert.conf
 - Everytime you rebuilt the container with a new image check if new settings have been added in [pialert.conf](https://github.com/jokob-sk/Pi.Alert/blob/main/config/pialert.conf).

### Network
 - You will have to run the container on the host network, e.g: `sudo docker run --rm --net=host jokobsk/pi.alert`

### Default Port 
 - The app is accessible on the port `:20211`.

> Please note - the initial scan can take up-to 15min (with 50 devices and MQTT). Subsequent ones 3 and 5 minutes so wait that long for all of the scans to run.

## 💾 Setup and Backups

### ❗ **Required** 

1. Download `pialert.conf` from [here](https://github.com/jokob-sk/Pi.Alert/tree/main/config).     
2. In `pialert.conf` define your network adapter(s) with the `SCAN_SUBNETS` variable. 
   * The adapter will probably be `eth0` or `eth1`.  
   * Specify the network filter (which **significantly** speeds up the scan process). For example, the filter `192.168.1.0/24` covers IP ranges 192.168.1.0 to 192.168.1.255.
   * Examples for one and two subnets:
     * `SCAN_SUBNETS    = '192.168.1.0/24 --interface=eth0'`
     * `SCAN_SUBNETS    = ['192.168.1.0/24 --interface=eth0', '192.168.1.0/24 --interface=eth1']`

3. Use your configuration by: 
   * Mapping the container folder to a persistent folder containing `pialert.conf`:
     * `persistent/path/config:/home/pi/pialert/config`     
   * ... or by mapping the file directly: 
     * `pialert.conf:/home/pi/pialert/config/pialert.conf`

### 👍 **Recommended** 

1. Database backup
   * Download the [original DB from GitHub](https://github.com/jokob-sk/Pi.Alert/blob/main/db/pialert.db).
   * Map the `pialert.db` file (⚠ not folder) from above to `/home/pi/pialert/db/pialert.db` (see [Examples](https://github.com/jokob-sk/Pi.Alert/tree/main/dockerfiles#-examples) for details). 
   * If facing issues (AJAX errors, can't write to DB, etc,) make sure permissions are set correctly, and check the logs under `/home/pi/pialert/front/log`. 
   * To solve permission issues you can also try to create a DB backup and then run a DB Restore via the **Maintenance > Backup/Restore** section.
   * You can try also setting the owner and group of the `pialert.db` by executing the following on the host system: `docker exec pialert chown -R www-data:www-data /home/pi/pialert/db/pialert.db`. 
2. Map to local User nad Group IDs. Specify the enviroment variables `HOST_USER_ID` and `HOST_USER_GID` if needed.
3. Set the `TZ` environment variable to your current time zone (e.g.`Europe/Paris`). Find your time zone [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).
4. Use a custom port by specifying the `PORT` env variable.
5. Map an empty file with the name `setting_darkmode` if you want to force the dark mode on container rebuilt
   * `- persistent/path/db/setting_darkmode:/home/pi/pialert/db/setting_darkmode`
6. Check and enable notification service(s) in the `pialert.conf` file.

Docker-compose examples can be found below.

## 📄 Examples

### Example 1

`docker-compose.yml` 

```yaml
version: "3"
services:
  pialert:
    container_name: pialert
    image: "jokobsk/pi.alert:latest"      
    network_mode: "host"        
    restart: unless-stopped
    volumes:
      - ${APP_DATA_LOCATION}/pialert/config:/home/pi/pialert/config
      - ${APP_DATA_LOCATION}/pialert/db/pialert.db:/home/pi/pialert/db/pialert.db
      # (optional) map an empty file with the name 'setting_darkmode' if you want to force the dark mode on container rebuilt
      - ${APP_DATA_LOCATION}/pialert/db/setting_darkmode:/home/pi/pialert/db/setting_darkmode
      # (optional) useful for debugging if you have issues setting up the container
      - ${LOGS_LOCATION}:/home/pi/pialert/front/log
    environment:
      - TZ=${TZ}
      - PORT=${PORT}
      - HOST_USER_ID=${HOST_USER_ID}
      - HOST_USER_GID=${HOST_USER_GID}
```

`.env` file

```yaml
#GLOBAL PATH VARIABLES

APP_DATA_LOCATION=/path/to/docker_appdata
APP_CONFIG_LOCATION=/path/to/docker_config
LOGS_LOCATION=/path/to/docker_logs

#ENVIRONMENT VARIABLES

TZ=Europe/Paris
HOST_USER_ID=1000
HOST_USER_GID=1000
PORT=20211

#DEVELOPMENT VARIABLES

DEV_LOCATION=/path/to/local/source/code
```

To run the container execute: `sudo docker-compose --env-file /path/to/.env up`

### Example 2

Courtesy of [pbek](https://github.com/pbek). The volume `pialert_db` is used by the db directory. The two config files are mounted directly from a local folder to their places in the config folder. You can backup the `docker-compose.yaml` folder and the docker volumes folder.

```yaml
  pialert:
    image: jokobsk/pi.alert
    ports:
      - "80:20211/tcp"
    environment:
      - TZ=Europe/Vienna
    networks:
      local:
        ipv4_address: 192.168.1.2
    restart: unless-stopped
    volumes:
      - pialert_db:/home/pi/pialert/db
      - ./pialert/pialert.conf:/home/pi/pialert/config/pialert.conf      
```

## 🏅 Recognitions

Big thanks to <a href="https://github.com/Macleykun">@Macleykun</a> for help and tips&tricks for Dockerfile(s):

<a href="https://github.com/Macleykun">
  <img src="https://avatars.githubusercontent.com/u/26381427?size=50"> 
</a>

## ☕ Support me

Disclaimer: Please only donate if you don't have any debt yourself. Support yourself first, then others.

<a href="https://www.buymeacoffee.com/jokobsk" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 30px !important;width: 117px !important;" width="150px" ></a>

