# `docker-compose.yaml` Examples

> [!NOTE] 
> The container needs to run in `network_mode:"host"`. This also means that not all functionality is supported on a Windows host as Docker for Windows doesn't support this networking option. 

### Example 1

```yaml
services:
  netalertx:
    container_name: netalertx
    # use the below line if you want to test the latest dev image
    # image: "ghcr.io/jokob-sk/netalertx-dev:latest" 
    image: "ghcr.io/jokob-sk/netalertx:latest"      
    network_mode: "host"        
    restart: unless-stopped
    volumes:
      - local_path/config:/app/config
      - local_path/db:/app/db      
      # (optional) useful for debugging if you have issues setting up the container
      - local_path/logs:/app/log
      # (API: OPTION 1) use for performance
      - type: tmpfs
        target: /app/api
      # (API: OPTION 2) use when debugging issues 
      # -  local_path/api:/app/api
    environment:
      - TZ=Europe/Berlin      
      - PORT=20211
```

To run the container execute: `sudo docker-compose up -d`

### Example 2

Example by [SeimuS](https://github.com/SeimusS).

```yaml
services:
  netalertx:
    container_name: NetAlertX
    hostname: NetAlertX
    privileged: true
    # use the below line if you want to test the latest dev image
    # image: "ghcr.io/jokob-sk/netalertx-dev:latest" 
    image: ghcr.io/jokob-sk/netalertx:latest
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
services:
  netalertx:
    container_name: netalertx
    # use the below line if you want to test the latest dev image
    # image: "ghcr.io/jokob-sk/netalertx-dev:latest" 
    image: "ghcr.io/jokob-sk/netalertx:latest"      
    network_mode: "host"        
    restart: unless-stopped
    volumes:
      - ${APP_CONFIG_LOCATION}/netalertx/config:/app/config
      - ${APP_DATA_LOCATION}/netalertx/db/:/app/db/      
      # (optional) useful for debugging if you have issues setting up the container
      - ${LOGS_LOCATION}:/app/log
      # (API: OPTION 1) use for performance
      - type: tmpfs
        target: /app/api
      # (API: OPTION 2) use when debugging issues 
      # -  local/path/api:/app/api
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


### Example 4: Docker swarm

Notice how the host network is defined in a swarm setup:

```yaml
services:
  netalertx:
    # Use the below line if you want to test the latest dev image
    # image: "jokobsk/netalertx-dev:latest"
    image: "ghcr.io/jokob-sk/netalertx:latest"
    volumes:
      - /mnt/MYSERVER/netalertx/config:/config:rw
      - /mnt/MYSERVER/netalertx/db:/netalertx/db:rw
      - /mnt/MYSERVER/netalertx/logs:/netalertx/front/log:rw
    environment:
      - TZ=Europe/London
      - PORT=20211
    networks:
      - outside
    deploy:
      mode: replicated
      replicas: 1
      restart_policy:
        condition: on-failure

networks:
  outside:
    external:
      name: "host"


```
### Example 5: same as 3 but with a single top level folder, fixed log ready to drop in portainer

`docker-compose.yml` 

```yaml
services:
  netalertx:
    container_name: netalertx
    # use the below line if you want to test the latest dev image instead of the stable release
    # image: "ghcr.io/jokob-sk/netalertx-dev:latest" 
    image: "ghcr.io/jokob-sk/netalertx:latest"      
    network_mode: "host"        
    restart: unless-stopped
    volumes:
      - ${APP_FOLDER}/netalertx/config:/app/config
      - ${APP_FOLDER}/netalertx/db:/app/db     
      # (optional) useful for debugging if you have issues setting up the container
      - ${APP_FOLDER}/netalertx/log:/app/log
      # (API: OPTION 1) default -> use for performance
      - type: tmpfs
        target: /app/api
      # (API: OPTION 2) use when debugging issues 
      # -  ${APP_FOLDER}/netalertx/api:/app/api
    environment:
      - TZ=${TZ}      
      - PORT=${PORT}
```

`.env` file

```yaml
APP_FOLDER=/path/to/local/NetAlertX/location

#ENVIRONMENT VARIABLES
PUID=200
PGID=300
TZ=America/New_York
LISTEN_ADDR=0.0.0.0
PORT=20211
#GLOBAL PATH VARIABLE

# you may want to create a dedicated user and group to run the container with 
# sudo groupadd -g 300 nax-g 
# sudo useradd -u 200 -g 300 nax-u
# mkdir -p $APP_FOLDER/{db,config,log} 
# chown -R 200:300 $APP_FOLDER
# chmod -R 775 $APP_FOLDER

# DEVELOPMENT VARIABLES
# you can create  multiple env files called .env.dev1, .env.dev2 etc and use them by running:
# docker compose --env-file .env.dev1 up -d
# you can then clone  multiple dev copies of NetAlertX just make sure to change the APP_FOLDER and PORT variables in each .env.devX file
```

To run the container execute: `sudo docker-compose --env-file /path/to/.env up`
