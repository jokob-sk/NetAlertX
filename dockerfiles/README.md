[![Docker](https://github.com/jokob-skPi.Alert/actions/workflows/docker.yml/badge.svg)](https://github.com/jokob-sk/Pi.Alert/actions/workflows/docker.yml) [![Docker Image Size](https://img.shields.io/docker/image-size/jokobsk/pi.alert?logo=Docker)](https://hub.docker.com/r/jokobsk/pi.alert)

# :whale: A docker image for Pi.Alert 

All credit for Pi.Alert goes to: [pucherot/Pi.Alert](https://github.com/pucherot/Pi.Alert).
A pre-built image is available on :whale: Docker Hub: [jokobsk/Pi.Alert](https://registry.hub.docker.com/r/jokobsk/pi.alert).
The source :page_facing_up: Dockerfile is available [here](https://github.com/jokob-sk/Pi.Alert/blob/main/Dockerfile) with a detailed :books: [readme](https://github.com/jokob-sk/Pi.Alert/blob/main//dockerfiles/README.md) included.

## :white_check_mark: Usage

-  Network
   - You will have to probably run the container on the host network, e.g: `sudo docker run --rm --net=host jokobsk/pi.alert`
-  Port 
   - The container runs on the port `:20211`.
-  UI URL
   - The UI is located on `<host IP>:20211/pialert/`

> Please note - the cronjob is executed every 1, 5 and 15 minutes so wait that long for all of the scans to run.

## :floppy_disk: Setup and Backups

1. Download `pialert.conf` and `version.conf` from [here](https://github.com/jokob-sk/Pi.Alert/tree/main/config).
2. Backup your configuration by: 
   * Mapping the container folder `/home/pi/pialert/config` to your own folder containing `pialert.conf` and `version.conf`. 
    
    OR
    
   * Mapping the files individually `pialert.conf:/home/pi/pialert/config/pialert.conf` and `version.conf:/home/pi/pialert/config/version.conf`      
3. In `pialert.config` specify your network adapter (will probably be eth0 or eth1) and the network filter, e.g. if your DHCP server assigns IPs in the 192.168.1.0 to 192.168.1.255 range specify it the following way: 
   * `SCAN_SUBNETS    = '192.168.1.0/24 --interface=eth0'`
4. Set the `TZ` environment variable to your current time zone (e.g.`Europe/Paris`). Find your time zone [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).
5. Database backup
   * Automated copy
     The docker image creates a DB copy once every 30 min by copying the DB to `/home/pi/pialert/config/pialert.db_bak`. 
      > If you have a backup already available, make sure you rename this file if you want to keep older backups before starting a new container.

     - You can backup the DB by also ad-hoc by running the follow command in the container:

       - `cp /home/pi/pialert/db/pialert.db /home/pi/pialert/config/pialert.db_bak`

     - Restoring the DB:

       - `cp /home/pi/pialert/config/pialert.db_bak /home/pi/pialert/db/pialert.db`

   * Alternative approach: Storing the DB on your own volume

       ```yaml
           volumes:
             - pialert_db:/home/pi/pialert/db
       ```       

A full config example can be found below.

## :page_facing_up: Example Config

Courtesy of [pbek](https://github.com/pbek). The volume `pialert_db` is used the db directory. The two config files are mounted directly from a local folder to their places in the config folder. You can backup the `docker-compose.yaml` folder and the docker volumes folder.

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
