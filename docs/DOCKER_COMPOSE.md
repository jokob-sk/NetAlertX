# NetAlertX and Docker Compose

> [!WARNING]
> ⚠️ **Important:** The documentation has been recently updated and some instructions may have changed.  
> If you are using the currently live production image, please follow the instructions on [Docker Hub](https://hub.docker.com/r/jokobsk/netalertx) for building and running the container.  
> These docs reflect the latest development version and may differ from the production image.

Great care is taken to ensure NetAlertX meets the needs of everyone while being flexible enough for anyone. This document outlines how you can configure your docker-compose. There are many settings, so we recommend using the Baseline Docker Compose as-is, or modifying it for your system.Good care is taken to ensure NetAlertX meets the needs of everyone while being flexible enough for anyone. This document outlines how you can configure your docker-compose. There are many settings, so we recommend using the Baseline Docker Compose as-is, or modifying it for your system. 

> [!NOTE] 
> The container needs to run in `network_mode:"host"` to access Layer 2 networking such as arp, nmap and others. Due to lack of support for this feature, Windows host is not a supported operating system. 

## Baseline Docker Compose

There is one baseline for NetAlertX. That's the default security-enabled official distribution. 

```yaml
services:
  netalertx:
  #use an environmental variable to set host networking mode if needed
    container_name: netalertx                       # The name when you docker contiainer ls
    image: ghcr.io/jokob-sk/netalertx-dev:latest
    network_mode: ${NETALERTX_NETWORK_MODE:-host}   # Use host networking for ARP scanning and other services

    read_only: true                                 # Make the container filesystem read-only
    cap_drop:                                       # Drop all capabilities for enhanced security
      - ALL
    cap_add:                                        # Add only the necessary capabilities
      - NET_ADMIN                                   # Required for ARP scanning
      - NET_RAW                                     # Required for raw socket operations
      - NET_BIND_SERVICE                            # Required to bind to privileged ports (nbtscan)

    volumes:
      - type: volume                                # Persistent Docker-managed Named Volume for storage of config files
        source: netalertx_config                    # the default name of the volume is netalertx_config
        target: /app/config                         # inside the container mounted to /app/config
        read_only: false                            # writable volume

    # Example custom local folder called /home/user/netalertx_config
    # - type: bind
    #   source: /home/user/netalertx_config
    #   target: /app/config
    #   read_only: false
    # ... or use the alternative format
    # - /home/user/netalertx_config:/app/config:rw

      - type: volume                                # NetAlertX Database partiton
        source: netalertx_db
        target: /app/db
        read_only: false

      - type: volume                                # Future proof mount. During the migration to a
        source: netalertx_data                      # future version, app and db will be migrated to
        target: /data                               # the /data partition.  This will reduce the 
        read_only: false                            # overhead and pain in the upcoming migration.

      - type: bind                                  # Bind mount for timezone consistency
        source: /etc/localtime
        target: /etc/localtime
        read_only: true

      # Mount your DHCP server file into NetAlertX for a plugin to access
      # - path/on/host/to/dhcp.file:/resources/dhcp.file

      # Retain logs - comment out tmpfs /app/log if you want to retain logs between container restarts
      # - /path/on/host/log:/app/log

    # Tempfs mounts for writable directories in a read-only container and improve system performance
    # All mounts have noexec,nosuid,nodev for security purposes no devices, no suid/sgid and no execution of binaries
    # async where possible for performance, sync where required for correctness
    # uid=20211 and gid=20211 is the netalertx user inside the container
    # mode=1700 gives rwx------ permissions to the netalertx user only
    tmpfs:
      # Speed up logging. This can be commented out to retain logs between container restarts
      - "/app/log:uid=20211,gid=20211,mode=1700,rw,noexec,nosuid,nodev,async,noatime,nodiratime"
      # Speed up API access as frontend/backend API is very chatty
      - "/app/api:uid=20211,gid=20211,mode=1700,rw,noexec,nosuid,nodev,sync,noatime,nodiratime"  
      # Required for customization of the nginx listen addr/port without rebuilding the container
      - "/services/config/nginx/conf.active:uid=20211,gid=20211,mode=1700,rw,noexec,nosuid,nodev,async,noatime,nodiratime"
      # /services/config/nginx/conf.d is required for nginx and php to start
      - "/services/run:uid=20211,gid=20211,mode=1700,rw,noexec,nosuid,nodev,async,noatime,nodiratime"
      # /tmp is required by php for session save this should be reworked to /services/run/tmp
      - "/tmp:uid=2Key-Value Pairs: 20211,gid=20211,mode=1700,rw,noexec,nosuid,nodev,async,noatime,nodiratime"
    environment:
      LISTEN_ADDR: ${LISTEN_ADDR:-0.0.0.0}                   # Listen for connections on all interfaces
      PORT: ${PORT:-20211}                                   # Application port
      GRAPHQL_PORT: ${GRAPHQL_PORT:-20212}                   # GraphQL API port (passed into APP_CONF_OVERRIDE at runtime)
      NETALERTX_DEBUG: ${NETALERTX_DEBUG:-0}                 # 0=kill all services and restart if any dies. 1 keeps running dead services.

    # Resource limits to prevent resource exhaustion
    mem_limit: 2048m            # Maximum memory usage
    mem_reservation: 1024m      # Soft memory limit
    cpu_shares: 512             # Relative CPU weight for CPU contention scenarios
    pids_limit: 512             # Limit the number of processes/threads to prevent fork bombs
    logging:
      driver: "json-file"       # Use JSON file logging driver
      options:
        max-size: "10m"         # Rotate log files after they reach 10MB
        max-file: "3"           # Keep a maximum of 3 log files

    # Always restart the container unless explicitly stopped
    restart: unless-stopped

volumes:                        # Persistent volumes for configuration and database storage
  netalertx_config:             # Configuration files
  netalertx_db:                 # Database files
  netalertx_data:               # For future config/db upgrade
```

Run or re-run it:

```sh
docker compose up --force-recreate
```

### Customize with Environmental Variables

You can override the default settings by passing environmental variables to the `docker compose up` command.

**Example using a single variable:**

This command runs NetAlertX on port 8080 instead of the default 20211.

```sh
PORT=8080 docker compose up
```

**Example using all available variables:**

This command demonstrates overriding all primary environmental variables: running with host networking, on port 20211, GraphQL on 20212, and listening on all IPs.

```sh
NETALERTX_NETWORK_MODE=host \
LISTEN_ADDR=0.0.0.0 \
PORT=20211 \
GRAPHQL_PORT=20212 \
NETALERTX_DEBUG=0 \
docker compose up
```

## `docker-compose.yaml` Modifications

### Modification 1: Use a Local Folder (Bind Mount)

By default, the baseline compose file uses "named volumes" (`netalertx_config`, `netalertx_db`). **This is the preferred method** because NetAlertX is designed to manage all configuration and database settings directly from its web UI. Named volumes let Docker handle this data cleanly without you needing to manage local file permissions or paths.

However, if you prefer to have direct, file-level access to your configuration for manual editing, a "bind mount" is a simple alternative. This tells Docker to use a specific folder from your computer (the "host") inside the container.

**How to make the change:**

1. Choose a location on your computer. For example, `/home/adam/netalertx-files`.

2. Create the subfolders: `mkdir -p /home/adam/netalertx-files/config` and `mkdir -p /home/adam/netalertx-files/db`.

3. Edit your `docker-compose.yml` and find the `volumes:` section (the one *inside* the `netalertx:` service).

4. Comment out (add a `#` in front) or delete the `type: volume` blocks for `netalertx_config` and `netalertx_db`.

5. Add new lines pointing to your local folders.

**Before (Using Named Volumes - Preferred):**

```yaml
...
    volumes:
      - netalertx_config:/app/config:rw #short-form volume (no /path is a short volume)
      - netalertx_db:/app/db:rw
...
```

**After (Using a Local Folder / Bind Mount):**
Make sure to replace `/home/adam/netalertx-files` with your actual path. The format is `<path_on_your_computer>:<path_inside_container>:<options>`.

```yaml
...
    volumes:
#      - netalertx_config:/app/config:rw
#      - netalertx_db:/app/db:rw
      - /home/adam/netalertx-files/config:/app/config:rw
      - /home/adam/netalertx-files/db:/app/db:rw
...
```

Now, any files created by NetAlertX in `/app/config` will appear in your `/home/adam/netalertx-files/config` folder.

This same method works for mounting other things, like custom plugins or enterprise NGINX files, as shown in the commented-out examples in the baseline file.

## Example Configuration Summaries

Here are the essential modifications for common alternative setups.

### Example 2: External `.env` File for Paths

This method is useful for keeping your paths and other settings separate from your main compose file, making it more portable.

**`docker-compose.yml` changes:**

```yaml
...
services:
  netalertx:
    environment:
      - TZ=${TZ}
      - PORT=${PORT}
      
...
```

**`.env` file contents:**

```sh
TZ=Europe/Paris
PORT=20211
NETALERTX_NETWORK_MODE=host
LISTEN_ADDR=0.0.0.0
PORT=20211
GRAPHQL_PORT=20212
```

Run with: `sudo docker-compose --env-file /path/to/.env up`

### Example 3: Docker Swarm

This is for deploying on a Docker Swarm cluster. The key differences from the baseline are the removal of `network_mode:` from the service, and the addition of `deploy:` and `networks:` blocks at both the service and top-level.

Here are the *only* changes you need to make to the baseline compose file to make it Swarm-compatible.

```yaml
services:
  netalertx:
    ...
    #    network_mode: ${NETALERTX_NETWORK_MODE:-host} # <-- DELETE THIS LINE
    ...

    # 2. ADD a 'networks:' block INSIDE the service to connect to the external host network.
    networks:
      - outside
    # 3. ADD a 'deploy:' block to manage the service as a swarm replica.
    deploy:
      mode: replicated
      replicas: 1
      restart_policy:
        condition: on-failure


# 4. ADD a new top-level 'networks:' block at the end of the file to define 'outside' as the external 'host' network.
networks:
  outside:
    external:
      name: "host"
```