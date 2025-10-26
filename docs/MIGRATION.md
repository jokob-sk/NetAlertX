# Migration form PiAlert to NetAlertX

> [!WARNING] 
> Follow this guide only after you you downloaded and started a version of NetAlertX prior to v25.6.7 (e.g. `docker pull ghcr.io/jokob-sk/netalertx:25.5.24`) at least once after previously using the PiAlert image. Later versions don't support migration and devices and settings will have to migrated manually, e.g. via [CSV import](./DEVICES_BULK_EDITING.md).

## STEPS: 

> [!TIP] 
> In short: The application will auto-migrate the database, config, and all device information. A ticker message on top will be displayed until you update your docker mount points. It's always good to have a [backup strategy](./BACKUPS.md) in place.

1. Backup your current config and database (optional `devices.csv` to have a backup) (See bellow tip if facing issues)
2. Stop the container 
2. Update the Docker file mount locations in your `docker-compose.yml` or docker run command (See bellow **New Docker mount locations**). 
3. Rename the DB and conf files to `app.db` and `app.conf` and place them in the appropriate location.
4. Start the Container


> [!TIP] 
> If you have troubles accessing past backups, config or database files you can copy them into the newly mapped directories, for example by running this command in the container:  `cp -r /app/config /home/pi/pialert/config/old_backup_files`. This should create a folder in the `config` directory called `old_backup_files` conatining all the files in that location. Another approach is to map the old location and the new one at the same time to copy things over. 


### New Docker mount locations

The application installation folder in the docker container has changed from `/home/pi/pialert` to `/app`. That means the new mount points are:

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


# Examples

Examples of docker files with the new mount points.

## Example 1: Mapping folders

### Old docker-compose.yml

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

### New docker-compose.yml

```yaml
services:
  netalertx:                                  # ⚠  This has changed (🟡optional) 
    container_name: netalertx                 # ⚠  This has changed (🟡optional) 
    # use the below line if you want to test the latest dev image
    # image: "ghcr.io/jokob-sk/netalertx-dev:latest" 
    image: "ghcr.io/jokob-sk/netalertx:latest"         # ⚠  This has changed (🟡optional/🔺required in future) 
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


## Example 2: Mapping files

> [!NOTE] 
> The recommendation is to map folders as in Example 1, map files directly only when needed. 

### Old docker-compose.yml

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

### New docker-compose.yml

```yaml
services:
  netalertx:                                  # ⚠  This has changed (🟡optional) 
    container_name: netalertx                 # ⚠  This has changed (🟡optional) 
    # use the below line if you want to test the latest dev image
    # image: "ghcr.io/jokob-sk/netalertx-dev:latest" 
    image: "ghcr.io/jokob-sk/netalertx:latest"         # ⚠  This has changed (🟡optional/🔺required in future) 
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
