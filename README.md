# Pi.Alert
<!--- --------------------------------------------------------------------- --->

WIFI / LAN intruder detector.

Scan the devices connected to your WIFI / LAN and alert you the connection of
unknown devices. It also warns the disconnection of "always connected" devices.

![Main screen][main]

*(Apologies for my English and my limited knowledge of Python, php and
JavaScript)*

## How it worksz

The system continuously scans the network for:

- New devices
- New connections (re-connections)
- Disconnections
- "Always Connected" devices down
- Devices IP changes
- Internet IP address changes

## Scan Methods

Up to three scanning methods are used:

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

## Components

The system consists of two parts:

### Back

In charge of:

- Scan the network searching connected devices using the scanning methods
    described
- Store the information in the DB
- Report the changes detected by e-mail

  | ![Report 1][report1] | ![Report 2][report2] |
  | -------------------- | -------------------- |
  
### Front

A web frontal that allows:

- Manage the devices inventory and the characteristics
- Display in a visual way all the information collected by the back
  - Sessions
  - Connected devices
  - Favorites
  - Events
  - Presence
  - Concurrent devices
  - Down alerts
  - IP's
  - ...

  | ![Screen 1][screen1] | ![Screen 2][screen2] |
  | -------------------- | -------------------- |
  | ![Screen 3][screen3] | ![Screen 4][screen4] |

# Installation
<!--- --------------------------------------------------------------------- --->
Initially designed to run on a Raspberry Pi, probably it can run on many other
Linux distributions.

- One-step Automated Install:

#### `curl -sSL https://github.com/pucherot/Pi.Alert/raw/main/install/pialert_install.sh | bash`

- [Installation Guide (step by step)](docs/INSTALL.md)

# Update
<!--- --------------------------------------------------------------------- --->
- One-step Automated Update:

#### `curl -sSL https://github.com/pucherot/Pi.Alert/raw/main/install/pialert_update.sh | bash`

# Uninstall process
<!--- --------------------------------------------------------------------- --->
- [Unistall process](docs/UNINSTALL.md)

# Device Management
<!--- --------------------------------------------------------------------- --->
- [Device Management instructions](docs/DEVICE_MANAGEMENT.md)

## Other useful info
<!--- --------------------------------------------------------------------- --->

### [Versions History](docs/VERSIONS_HISTORY.md)

### Powered by

  | Product      | Objetive                               |
  | ------------ | -------------------------------------- |
  | Python       | Programming language for the Back      |
  | PHP          | Programming language for the Front-end |
  | JavaScript   | Programming language for the Front-end |
  | Bootstrap    | Front-end framework                    |
  | Admin.LTE    | Bootstrap template                     |
  | FullCalendar | Calendar component                     |
  | Sqlite       | DB engine                              |
  | Lighttpd     | Webserver                              |
  | arp-scan     | Scan network using arp commands        |
  | Pi.hole      | DNS Server with Ad-block               |
  | dnsmasq      | DHCP Server                            |

### License

  GPL 3.0
  [Read more here](LICENSE.txt)

### Contact

  pi.alert.application@gmail.com
  
  ***Suggestions and comments are welcome***
  
# :whale: A docker image for Pi.Alert
>
> - All credit for Pi.Alert goes to [pucherot/Pi.Alert](https://github.com/pucherot/Pi.Alert).
> - The Docker image is available at [jokobsk/Pi.Alert - Docker Hub](https://registry.hub.docker.com/r/jokobsk/pi.alert).
> - The source Docker file is available on GitHub [jokob-sk/

## :white_check_mark: Usage

- Network
  - You will have to probably run the container on the host network, e.g: `sudo docker run --rm --net=host jokobsk/pi.alert`
- Port
  - The container runs on the port `:20211`.
- UI URL
  - The UI is located on `<host IP>:20211/pialert/`

> Please note - the cronjob is executed every 1, 5 and 15 minutes so wait that long for all of the scans to run.

## :floppy_disk: Setup and Backups

1. Download `pialert.conf` and `version.conf` from [here](https://github.com/jokob-sk/Pi.Alert/tree/main/config).
2. Backup your configuration by:
   - Mapping the container folder `/home/pi/pialert/config` to your own folder containing `pialert.conf` and `version.conf`.

    OR

   - Mapping the files individually `pialert.conf:/home/pi/pialert/config/pialert.conf` and `version.conf:/home/pi/pialert/config/version.conf`
3. In `pialert.config` specify your network adapter (will probably be eth0 or eth1) and the network filter, e.g. if your DHCP server assigns IPs in the 192.168.1.0 to 192.168.1.255 range specify it the following way:
   - `SCAN_SUBNETS    = '192.168.1.0/24 --interface=eth0'`
4. Set the `TZ` environment variable to your current time zone (e.g.`Europe/Paris`). Find your time zone [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).
5. Database backup
   - Automated copy
     The docker image creates a DB copy once every 30 min by copying the DB to `/home/pi/pialert/config/pialert.db_bak`.
      > If you have a backup already available, make sure you rename this file if you want to keep older backups before starting a new container.

     - You can backup the DB by also ad-hoc by running the follow command in the container:

       - `cp /home/pi/pialert/db/pialert.db /home/pi/pialert/config/pialert.db_bak`

     - Restoring the DB:

       - `cp /home/pi/pialert/config/pialert.db_bak /home/pi/pialert/db/pialert.db`

   - Alternative approach: Storing the DB on your own volume

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

<!--- --------------------------------------------------------------------- --->
[main]:    ./docs/img/1_devices.jpg           "Main screen"
[screen1]: ./docs/img/2_1_device_details.jpg  "Screen 1"
[screen2]: ./docs/img/2_2_device_sessions.jpg "Screen 2"
[screen3]: ./docs/img/2_3_device_presence.jpg "Screen 3"
[screen4]: ./docs/img/3_presence.jpg          "Screen 4"
[report1]: ./docs/img/4_report_1.jpg          "Report sample 1"
[report2]: ./docs/img/4_report_2.jpg          "Report sample 2"
