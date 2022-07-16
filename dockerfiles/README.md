[![Docker](https://github.com/jokob-sk/Pi.Alert/actions/workflows/docker.yml/badge.svg)](https://github.com/jokob-sk/Pi.Alert/actions/workflows/docker.yml)
[![Docker Image Size](https://img.shields.io/docker/image-size/jokobsk/pi.alert?logo=Docker)](https://hub.docker.com/r/jokobsk/pi.alert)
  <a href="https://hub.docker.com/r/jokobsk/pi.alert">
    <img src="https://img.shields.io/docker/pulls/jokobsk/pi.alert?logo=docker&color=0aa8d2&logoColor=fff" alt="Docker Pulls">
  </a>

# :whale: A docker image for Pi.Alert 

All credit for Pi.Alert goes to: [pucherot/Pi.Alert](https://github.com/pucherot/Pi.Alert).
A pre-built image is available on :whale: Docker Hub: [jokobsk/Pi.Alert](https://registry.hub.docker.com/r/jokobsk/pi.alert).
The source :page_facing_up: Dockerfile is available [here](https://github.com/jokob-sk/Pi.Alert/blob/main/Dockerfile) with a detailed :books: [readme](https://github.com/jokob-sk/Pi.Alert/blob/main//dockerfiles/README.md) included.

## :information_source: Usage

Network
   - You will have to probably run the container on the host network, e.g: `sudo docker run --rm --net=host jokobsk/pi.alert`

Default Port 
   - The app is accessible on the port `:20211`.

> Please note - the cronjob is executed every 1, 5 and 15 minutes so wait that long for all of the scans to run.

## :floppy_disk: Setup and Backups

1. (**required**) Download `pialert.conf` and `version.conf` from [here](https://github.com/jokob-sk/Pi.Alert/tree/main/config).     
2. (**required**) In `pialert.config` specify your network adapter (will probably be `eth0` or `eth1`) and the network filter (which **significantly** speeds up the scan process), e.g. if your DHCP server assigns IPs in the 192.168.1.0 to 192.168.1.255 range specify it the following way: 
   * `SCAN_SUBNETS    = '192.168.1.0/24 --interface=eth0'`
3. (**required**) Use your configuration by: 
   * Mapping the container folder `/home/pi/pialert/config` to a persistent folder containing `pialert.conf` and `version.conf`,     
   * ... or by mapping the files individually `pialert.conf:/home/pi/pialert/config/pialert.conf` and `version.conf:/home/pi/pialert/config/version.conf` 
4. Set the `TZ` environment variable to your current time zone (e.g.`Europe/Paris`). Find your time zone [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).
5. Database backup
   * The DB is stored under `/home/pi/pialert/db/pialert.db`. Map this file to a persistent location (see [Examples](https://github.com/jokob-sk/Pi.Alert/tree/main/dockerfiles#page_facing_up-examples) for details). If facing issues (AJAX errors, can't write to DB, etc, make sure permissions are set correctly, alternatively check the logs under `/home/pi/pialert/log`)
   * Automated copy
     The docker image copies the DB once every 30 min to `/home/pi/pialert/config/pialert.db_bak`. If you have a backup already available, make sure you rename this file if you want to keep older backups before starting a new container. To restore the DB run: `cp /home/pi/pialert/config/pialert.db_bak /home/pi/pialert/db/pialert.db`   
6. The container supports mapping to local User nad Group IDs. Specify the enviroment variables `HOST_USER_ID` and `HOST_USER_GID` if needed.
7. You can override the port by specifying the `PORT` env variable.

Config examples can be found below.

## :page_facing_up: Examples

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
      - ${LOGS_LOCATION}/:/home/pi/pialert/log
    environment:
      - TZ=Europe/London
      - PORT=20211
      - HOST_USER_ID=1000
      - HOST_USER_GID=1000
```

`.env` file

```yaml

APP_DATA_LOCATION=/path/to/docker_appdata
APP_CONFIG_LOCATION=/path/to/docker_config
LOGS_LOCATION=/path/to/docker_logs

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

## :coffee: Support 

> Disclaimer: This is my second container and I might have used unconventional hacks so if anyone is more experienced, feel free to fork/create pull requests. Also, please only donate if you don't have any debt yourself. Support yourself first, then others.

<a href="https://www.buymeacoffee.com/jokobsk" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 30px !important;width: 117px !important;" width="150px" ></a>
