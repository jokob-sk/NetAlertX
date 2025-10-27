# Migration 

If upgrading from older versions of NetAlertX (or PiAlert (by jokob-sk)) the following data and setup migration steps need to be followed.

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
A ticker message will appear at the top of the web UI until you update your Docker mount points.

1. Stop the container 
2. [Back up your setup](./BACKUPS.md) 
3. Update the Docker file mount locations in your `docker-compose.yml` or docker run command (See below **New Docker mount locations**). 
4. Rename the DB and conf files to `app.db` and `app.conf` and place them in the appropriate location.
5. Start the container


> [!TIP] 
> If you have troubles accessing past backups, config or database files you can copy them into the newly mapped directories, for example by running this command in the container:  `cp -r /app/config /home/pi/pialert/config/old_backup_files`. This should create a folder in the `config` directory called `old_backup_files` containing all the files in that location. Another approach is to map the old location and the new one at the same time to copy things over. 

#### New Docker mount locations

The internal application path in the container has changed from `/home/pi/pialert` to `/app`. Update your volume mounts as follows:

 | Old mount point | New mount point | 
 |----------------------|---------------| 
 | `/home/pi/pialert/config` | `/app/config` |
 | `/home/pi/pialert/db` | `/app/db` |


 If you were mounting files directly, please note the file names have changed:

 | Old file name | New file name | 
 |----------------------|---------------| 
 | `pialert.conf` | `app.conf` |
 | `pialert.db` | `app.db` |


> [!NOTE] 
> The application uses symlinks linking the old db and config locations to the new ones, so data loss should not occur. [Backup strategies](./BACKUPS.md) are still recommended to backup your setup.


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
      - local/path/config:/home/pi/pialert/config  
      - local/path/db:/home/pi/pialert/db         
      # (optional) useful for debugging if you have issues setting up the container
      - local/path/logs:/home/pi/pialert/front/log
    environment:
      - TZ=Europe/Berlin      
      - PORT=20211
```

###### New docker-compose.yml

```yaml
services:
  netalertx:                                  # ⚠  This has changed (🟡optional) 
    container_name: netalertx                 # ⚠  This has changed (🟡optional) 
    image: "ghcr.io/jokob-sk/netalertx:25.5.24"         # ⚠  This has changed (🟡optional/🔺required in future) 
    network_mode: "host"        
    restart: unless-stopped
    volumes:
      - local/path/config:/app/config         # ⚠  This has changed (🔺required) 
      - local/path/db:/app/db                 # ⚠  This has changed (🔺required) 
      # (optional) useful for debugging if you have issues setting up the container
      - local/path/logs:/app/log        # ⚠  This has changed (🟡optional) 
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
      - local/path/config/pialert.conf:/home/pi/pialert/config/pialert.conf  
      - local/path/db/pialert.db:/home/pi/pialert/db/pialert.db         
      # (optional) useful for debugging if you have issues setting up the container
      - local/path/logs:/home/pi/pialert/front/log
    environment:
      - TZ=Europe/Berlin      
      - PORT=20211
```

###### New docker-compose.yml

```yaml
services:
  netalertx:                                  # ⚠  This has changed (🟡optional) 
    container_name: netalertx                 # ⚠  This has changed (🟡optional) 
    image: "ghcr.io/jokob-sk/netalertx:25.5.24"         # ⚠  This has changed (🟡optional/🔺required in future) 
    network_mode: "host"        
    restart: unless-stopped
    volumes:
      - local/path/config/app.conf:/app/config/app.conf # ⚠  This has changed (🔺required) 
      - local/path/db/app.db:/app/db/app.db             # ⚠  This has changed (🔺required) 
      # (optional) useful for debugging if you have issues setting up the container
      - local/path/logs:/app/log                  # ⚠  This has changed (🟡optional) 
    environment:
      - TZ=Europe/Berlin      
      - PORT=20211
```


### 1.2 Migration from NetAlertX `v25.5.24`

Versions before `v25.10.1` require an intermediate migration through `v25.5.24` to ensure database compatibility.

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
    image: "ghcr.io/jokob-sk/netalertx:25.5.24"         # ⚠  This is important (🔺required) 
    network_mode: "host"        
    restart: unless-stopped
    volumes:
      - local/path/config:/app/config         
      - local/path/db:/app/db                 
      # (optional) useful for debugging if you have issues setting up the container
      - local/path/logs:/app/log        
    environment:
      - TZ=Europe/Berlin      
      - PORT=20211
```

```yaml
services:
  netalertx:                                  
    container_name: netalertx                
    image: "ghcr.io/jokob-sk/netalertx:25.10.1"         # ⚠  This is important (🔺required) 
    network_mode: "host"        
    restart: unless-stopped
    volumes:
      - local/path/config:/app/config         
      - local/path/db:/app/db                 
      # (optional) useful for debugging if you have issues setting up the container
      - local/path/logs:/app/log        
    environment:
      - TZ=Europe/Berlin      
      - PORT=20211
```

### 1.3 Migration from NetAlertX `v25.10.1`

> [!WARNING]
> This section is under development. The migration path from `v25.10.1` to future versions (e.g., `v25.11.x` and newer) will be published soon.

#### STEPS: 

1. Stop the container 
2. [Back up your setup](./BACKUPS.md) 
3. Upgrade to `v25.10.1` by pinning the release version (See Examples below)
4. Start the container and verify everything works as expected.
5. Stop the container 
6. 🔻 TBC 🔺

##### Example 1: Mapping folders

###### docker-compose.yml changes

```yaml
services:
  netalertx:                                  
    container_name: netalertx                
    image: "ghcr.io/jokob-sk/netalertx:25.10.1"         # ⚠  This is important (🔺required) 
    network_mode: "host"        
    restart: unless-stopped
    volumes:
      - local/path/config:/app/config         
      - local/path/db:/app/db                 
      # (optional) useful for debugging if you have issues setting up the container
      - local/path/logs:/app/log        
    environment:
      - TZ=Europe/Berlin      
      - PORT=20211
```


🔻 TBC 🔺