[![Docker](https://github.com/jokob-sk/Pi.Alert/actions/workflows/docker.yml/badge.svg)](https://github.com/jokob-sk/Pi.Alert/actions/workflows/docker.yml)
<a href="https://github.com/jokob-sk/Pi.Alert">
  <img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/jokob-sk/pi.alert/main?logo=github">
</a>
[![Docker Image Size](https://img.shields.io/docker/image-size/jokobsk/pi.alert?logo=Docker)](https://hub.docker.com/r/jokobsk/pi.alert)
<a href="https://hub.docker.com/r/jokobsk/pi.alert">
  <img src="https://img.shields.io/docker/pulls/jokobsk/pi.alert?logo=docker&color=0aa8d2&logoColor=fff" alt="Docker Pulls">
</a>
<a href="https://hub.docker.com/r/jokobsk/pi.alert">
  <img alt="Docker last pushed" src="https://img.shields.io/badge/dynamic/json?color=blue&label=Last%20pushed&query=last_updated&url=https%3A%2F%2Fhub.docker.com%2Fv2%2Frepositories%2Fjokobsk%2Fpi.alert%2F&logo=docker&?link=http://left&link=https://hub.docker.com/repository/docker/jokobsk/pi.alert">
</a>

# 🐳 A docker image for Pi.Alert 

🥇 Pi.Alert credit goes to [pucherot/Pi.Alert](https://github.com/pucherot/Pi.Alert). <br/>
🐳 Docker Image: [jokobsk/Pi.Alert](https://registry.hub.docker.com/r/jokobsk/pi.alert). <br/>
📄 [Dockerfile](https://github.com/jokob-sk/Pi.Alert/blob/main/Dockerfile) <br/>
📚 [Dockerfile instructions](https://github.com/jokob-sk/Pi.Alert/blob/main//dockerfiles/README.md).

Big thanks to <a href="https://github.com/Macleykun">@Macleykun</a> for help and tips&tricks for Dockerfile(s):

<a href="https://github.com/Macleykun">
  <img src="https://avatars.githubusercontent.com/u/26381427?size=50"> 
</a>

## ℹ Usage 

pialert.conf
 - Everytime you rebuilt the container with a new image check if new settings have been added in [pialert.conf](https://github.com/jokob-sk/Pi.Alert/blob/main/config/pialert.conf).

Network
 - You will have to run the container on the host network, e.g: `sudo docker run --rm --net=host jokobsk/pi.alert`

Default Port 
 - The app is accessible on the port `:20211`.

> Please note - the cronjob is executed every 3 and 5 minutes so wait that long for all of the scans to run.

## 💾 Setup and Backups

1. (**required**) Download `pialert.conf` and `version.conf` from [here](https://github.com/jokob-sk/Pi.Alert/tree/main/config).     
2. (**required**) In `pialert.conf` specify your network adapter (will probably be `eth0` or `eth1`) and the network filter (which **significantly** speeds up the scan process), e.g. if your DHCP server assigns IPs in the 192.168.1.0 to 192.168.1.255 range specify it the following way: 
   * `SCAN_SUBNETS    = '192.168.1.0/24 --interface=eth0'`
3. (**required**) Use your configuration by: 
   * Mapping the container folder `/home/pi/pialert/config` to a persistent folder containing `pialert.conf` and `version.conf`,     
   * ... or by mapping the files individually `pialert.conf:/home/pi/pialert/config/pialert.conf` and `version.conf:/home/pi/pialert/config/version.conf` 
4. Set the `TZ` environment variable to your current time zone (e.g.`Europe/Paris`). Find your time zone [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).
5. Database backup
   * Download the [original DB from GitHub](https://github.com/jokob-sk/Pi.Alert/blob/main/db/pialert.db).
   * Map the `pialert.db` file (⚠ not folder) from above to `/home/pi/pialert/db/pialert.db` (see [Examples](https://github.com/jokob-sk/Pi.Alert/tree/main/dockerfiles#-examples) for details). 
   * If facing issues (AJAX errors, can't write to DB, etc,) make sure permissions are set correctly, alternatively check the logs under `/home/pi/pialert/log`. 
   * To solve permission issues you can also try to create a DB backup and then run a DB Restore via the **Maintenance > Backup/Restore** section.
6. The container supports mapping to local User nad Group IDs. Specify the enviroment variables `HOST_USER_ID` and `HOST_USER_GID` if needed.
7. You can override the port by specifying the `PORT` env variable.

Config examples can be found below.

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
    restart: always
    volumes:
      - ${APP_DATA_LOCATION}/pialert/config:/home/pi/pialert/config
      - ${APP_DATA_LOCATION}/pialert/db/pialert.db:/home/pi/pialert/db/pialert.db
      - ${LOGS_LOCATION}/tmp:/home/pi/pialert/log
    environment:
      - TZ=${TZ}
      - PORT=${PORT}
      - HOST_USER_ID=${HOST_USER_ID}
      - HOST_USER_GID=${HOST_USER_GID}
```

`.env` file

```yaml
#GLOBAL
APP_DATA_LOCATION=/path/to/docker_appdata
APP_CONFIG_LOCATION=/path/to/docker_config
LOGS_LOCATION=/path/to/docker_logs
TZ=Europe/Paris
HOST_USER_ID=1000
HOST_USER_GID=1000
PORT=20211
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
      - ./pialert/version.conf:/home/pi/pialert/config/version.conf
```

## ☕ Support 

> Disclaimer: This is my second container and I might have used unconventional hacks so if anyone is more experienced, feel free to fork/create pull requests. Also, please only donate if you don't have any debt yourself. Support yourself first, then others.

<a href="https://www.buymeacoffee.com/jokobsk" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 30px !important;width: 117px !important;" width="150px" ></a>
