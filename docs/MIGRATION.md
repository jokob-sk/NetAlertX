# Migration 

> [!WARNING]
> ⚠️ **Important:** The documentation has been recently updated and some instructions may have changed.  
> If you are using the currently live production image, please follow the instructions on [Docker Hub](https://hub.docker.com/r/jokobsk/netalertx) for building and running the container.  
> These docs reflect the latest development version and may differ from the production image.


When upgrading from older versions of NetAlertX (or PiAlert by jokob-sk), follow the migration steps below to ensure your data and configuration are properly transferred.

> [!TIP]
> It's always important to have a [backup strategy](./BACKUPS.md) in place.

## Migration scenarios

- You are running PiAlert (by jokob-sk)  
  → [Read the 1.1 Migration from PiAlert to NetAlertX `v25.5.24`](#11-migration-from-pialert-to-netalertx-v25524)

- You are running NetAlertX (by jokob-sk) `25.5.24` or older  
  → [Read the 1.2 Migration from NetAlertX `v25.5.24`](#12-migration-from-netalertx-v25524)

- You are running NetAlertX (by jokob-sk) (`v25.6.7` to `v25.10.1`)  
  → [Read the 1.3 Migration from NetAlertX `v25.10.1`](#13-migration-from-netalertx-v25101)


### 1.0 Manual Migration

You can migrate data manually, for example by exporting and importing devices using the [CSV import](./DEVICES_BULK_EDITING.md) method.


### 1.1 Migration from PiAlert to NetAlertX `v25.5.24`

#### STEPS: 

The application will automatically migrate the database, configuration, and all device information.
A banner message will appear at the top of the web UI reminding you to update your Docker mount points.

1. Stop the container 
2. [Back up your setup](./BACKUPS.md) 
3. Update the Docker file mount locations in your `docker-compose.yml` or docker run command (See below **New Docker mount locations**). 
4. Rename the DB and conf files to `app.db` and `app.conf` and place them in the appropriate location.
5. Start the container


> [!TIP] 
> If you have trouble accessing past backups, config or database files you can copy them into the newly mapped directories, for example by running this command in the container:  `cp -r /data/config /home/pi/pialert/config/old_backup_files`. This should create a folder in the `config` directory called `old_backup_files` containing all the files in that location. Another approach is to map the old location and the new one at the same time to copy things over. 

#### New Docker mount locations

The internal application path in the container has changed from `/home/pi/pialert` to `/app`. Update your volume mounts as follows:

 | Old mount point | New mount point | 
 |----------------------|---------------| 
 | `/home/pi/pialert/config` | `/data/config` |
 | `/home/pi/pialert/db` | `/data/db` |


 If you were mounting files directly, please note the file names have changed:

 | Old file name | New file name | 
 |----------------------|---------------| 
 | `pialert.conf` | `app.conf` |
 | `pialert.db` | `app.db` |


> [!NOTE] 
> The application automatically creates symlinks from the old database and config locations to the new ones, so data loss should not occur. Read the [backup strategies](./BACKUPS.md) guide to backup your setup.


#### Examples

Examples of docker files with the new mount points.

##### Example 1: Mapping folders

###### Old docker-compose.yml

```yaml
services:
  pialert:
    container_name: pialert
    # use the below line if you want to test the latest dev image
    # image: "ghcr.io/jokob-sk/netalertx-dev:latest" 
    image: "jokobsk/pialert:latest"      
    network_mode: "host"        
    restart: unless-stopped
    volumes:
      - /local/path/config:/home/pi/pialert/config  
      - /local/path/db:/home/pi/pialert/db         
      # (optional) useful for debugging if you have issues setting up the container
      - /local/path/logs:/home/pi/pialert/front/log
    environment:
      - TZ=Europe/Berlin      
      - PORT=20211
```

###### New docker-compose.yml

```yaml
services:
  netalertx:                                  # 🆕 This has changed  
    container_name: netalertx                 # 🆕 This has changed  
    image: "ghcr.io/jokob-sk/netalertx:25.5.24"         # 🆕 This has changed  
    network_mode: "host"        
    restart: unless-stopped
    volumes:
      - /local/path/config:/data/config         # 🆕 This has changed  
      - /local/path/db:/data/db                 # 🆕 This has changed  
      # (optional) useful for debugging if you have issues setting up the container
      - /local/path/logs:/tmp/log        # 🆕 This has changed  
    environment:
      - TZ=Europe/Berlin      
      - PORT=20211
```


##### Example 2: Mapping files

> [!NOTE] 
> The recommendation is to map folders as in Example 1, map files directly only when needed. 

###### Old docker-compose.yml

```yaml
services:
  pialert:
    container_name: pialert
    # use the below line if you want to test the latest dev image
    # image: "ghcr.io/jokob-sk/netalertx-dev:latest" 
    image: "jokobsk/pialert:latest"      
    network_mode: "host"        
    restart: unless-stopped
    volumes:
      - /local/path/config/pialert.conf:/home/pi/pialert/config/pialert.conf  
      - /local/path/db/pialert.db:/home/pi/pialert/db/pialert.db         
      # (optional) useful for debugging if you have issues setting up the container
      - /local/path/logs:/home/pi/pialert/front/log
    environment:
      - TZ=Europe/Berlin      
      - PORT=20211
```

###### New docker-compose.yml

```yaml
services:
  netalertx:                                  # 🆕 This has changed  
    container_name: netalertx                 # 🆕 This has changed  
    image: "ghcr.io/jokob-sk/netalertx:25.5.24"         # 🆕 This has changed  
    network_mode: "host"        
    restart: unless-stopped
    volumes:
      - /local/path/config/app.conf:/data/config/app.conf # 🆕 This has changed  
      - /local/path/db/app.db:/data/db/app.db             # 🆕 This has changed  
      # (optional) useful for debugging if you have issues setting up the container
      - /local/path/logs:/tmp/log                  # 🆕 This has changed  
    environment:
      - TZ=Europe/Berlin      
      - PORT=20211
```


### 1.2 Migration from NetAlertX `v25.5.24`

Versions before `v25.10.1` require an intermediate migration through `v25.5.24` to ensure database compatibility. Skipping this step may cause compatibility issues due to database schema changes introduced after `v25.5.24`.

#### STEPS: 

1. Stop the container 
2. [Back up your setup](./BACKUPS.md) 
3. Upgrade to `v25.5.24` by pinning the release version (See Examples below)
4. Start the container and verify everything works as expected.
5. Stop the container 
6. Upgrade to `v25.10.1` by pinning the release version (See Examples below)
7. Start the container and verify everything works as expected.

#### Examples

Examples of docker files with the tagged version.

##### Example 1: Mapping folders

###### docker-compose.yml changes

```yaml
services:
  netalertx:                                  
    container_name: netalertx                
    image: "ghcr.io/jokob-sk/netalertx:25.5.24"         # 🆕 This is important  
    network_mode: "host"        
    restart: unless-stopped
    volumes:
      - /local/path/config:/data/config         
      - /local/path/db:/data/db                 
      # (optional) useful for debugging if you have issues setting up the container
      - /local/path/logs:/tmp/log        
    environment:
      - TZ=Europe/Berlin      
      - PORT=20211
```

```yaml
services:
  netalertx:                                  
    container_name: netalertx                
    image: "ghcr.io/jokob-sk/netalertx:25.10.1"         # 🆕 This is important  
    network_mode: "host"        
    restart: unless-stopped
    volumes:
      - /local/path/config:/data/config         
      - /local/path/db:/data/db                 
      # (optional) useful for debugging if you have issues setting up the container
      - /local/path/logs:/tmp/log        
    environment:
      - TZ=Europe/Berlin      
      - PORT=20211
```

### 1.3 Migration from NetAlertX `v25.10.1`

Starting from v25.10.1, the container uses a [more secure, read-only runtime environment](./SECURITY_FEATURES.md), which requires all writable paths (e.g., logs, API cache, temporary data) to be mounted as `tmpfs` or permanent writable volumes, with sufficient access [permissions](./FILE_PERMISSIONS.md). 

#### STEPS: 

1. Stop the container 
2. [Back up your setup](./BACKUPS.md) 
3. Upgrade to `v25.10.1` by pinning the release version (See the example below)

```yaml
services:
  netalertx:                                  
    container_name: netalertx                
    image: "ghcr.io/jokob-sk/netalertx:25.10.1"         # 🆕 This is important  
    network_mode: "host"        
    restart: unless-stopped
    volumes:
      - /local/path/config:/data/config         
      - /local/path/db:/data/db                 
      # (optional) useful for debugging if you have issues setting up the container
      - /local/path/logs:/tmp/log        
    environment:
      - TZ=Europe/Berlin      
      - PORT=20211
```

4. Start the container and verify everything works as expected.
5. Stop the container.
6. Perform a one-off migration to the latest `netalertx` image and `20211` user:

> [!NOTE]
> The example below assumes your `/config` and `/db` folders are stored in `local/path`.  
> Replace this path with your actual configuration directory. `netalertx` is the container name, which might differ from your setup.

```sh
docker run -it --rm --name netalertx --user "0" \
  -v /local/path/config:/data/config \
  -v /local/path/db:/data/db \
  ghcr.io/jokob-sk/netalertx:latest
```

..or alternatively execute:

```bash
sudo chown -R 20211:20211 /local/path/config
sudo chown -R 20211:20211 /local/path/db
sudo chmod -R a+rwx /local/path/
```

7. Stop the container
8. Update the `docker-compose.yml` as per example below.

```yaml
services:
  netalertx:                                  
    container_name: netalertx                
    image: "ghcr.io/jokob-sk/netalertx"         # 🆕 This is important  
    network_mode: "host"       
    cap_add:                          # 🆕 New line
      - NET_RAW                       # 🆕 New line 
      - NET_ADMIN                     # 🆕 New line
      - NET_BIND_SERVICE              # 🆕 New line 
    restart: unless-stopped
    volumes:
      - /local/path/config:/data/config         
      - /local/path/db:/data/db                 
      # (optional) useful for debugging if you have issues setting up the container
      #- /local/path/logs:/tmp/log        
    environment:
      - TZ=Europe/Berlin      
      - PORT=20211
    # 🆕 New "tmpfs" section START 🔽
    tmpfs:
      # All writable runtime state resides under /tmp; comment out to persist logs between restarts
      - "/tmp:uid=20211,gid=20211,mode=1700,rw,noexec,nosuid,nodev,async,noatime,nodiratime"
    # 🆕 New "tmpfs" section END  🔼
```

9. Start the container and verify everything works as expected.