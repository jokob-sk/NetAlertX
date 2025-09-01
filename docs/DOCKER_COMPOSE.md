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
    # use the below line if you want to test the latest dev image instead of the stable release
    # image: "ghcr.io/jokob-sk/netalertx-dev:latest" 
    image: "ghcr.io/jokob-sk/netalertx:latest"      
    network_mode: "host"        
    restart: unless-stopped
    volumes:
      - ${APP_FOLDER}/netalertx/config:/app/config
      - ${APP_FOLDER}/netalertx/db/:/app/db     
      # (optional) useful for debugging if you have issues setting up the container
      - ${APP_FOLDER}:/app/log
      # (API: OPTION 1) default -> use for performance
      - type: tmpfs
        target: /app/api
      # (API: OPTION 2) use when debugging issues 
      # -  ${APP_FOLDER}/api:/app/api
    environment:
      - TZ=${TZ}      
      - PORT=${PORT}
```

`.env` file

```yaml
APP_FOLDER=/path/to/local/NetAlertX/location

#ENVIRONMENT VARIABLES
PUID=300
PGID=200
TZ=America/New_York
LISTEN_ADDR=0.0.0.0
PORT=20211
#GLOBAL PATH VARIABLE
APP_FOLDER=/path/to/local/NetAlertX/location
APP_FOLDER=/big/netalertX/latest

# you may want to create a dedicated user and group to run the container with 
# sudo groupadd -g 300 nax-g 
# sudo useradd -u 200 -g 300 nax-u
# mkdir -p $APP_FOLDER/{db,config,log} 
# chown -R 200:300 $APP_FOLDER
# chmod -R 775 $APP_FOLDER

# DEVELOPMENT VARIABLES
# only uncomment the line below if this file is for a dev clone of your main install
# and remove the APP_FOLDER at the top... 
# APP_FOLDER=/path/to/my/dev/folder/clone1
# you can create  multiple env files called .env.dev1, .env.dev2 etc and use them by running:
# docker compose --env-file .env.dev1 up -d



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
