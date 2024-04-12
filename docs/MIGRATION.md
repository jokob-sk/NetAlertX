# Migration form PiAlert to NetAlertX

The migration should be pretty straightforward. The application installation folder in the docker container has changed from `/home/pi/pialert` to `/app`. That means the new mount points are:

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
> The application uses symlinks linking the old locations to the new ones, so data loss should not occur. [Backup strategies](https://github.com/jokob-sk/NetAlertX/blob/main/docs/BACKUPS.md) are still recommended to backup your setup.

In summary, docker file mount locations in your `docker-compose.yml` or docker run command have changed. Examples follow.


## Example 1: Mapping folders

### Old docker-compose.yml

```yaml
version: "3"
services:
  pialert:
    container_name: pialert
    # use the below line if you want to test the latest dev image
    # image: "jokobsk/netalertx-dev:latest" 
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
version: "3"
services:
  netalertx:                                  # ⚠🟡  This has changed (optional) 🟡⚠
    container_name: netalertx                 # ⚠🟡  This has changed (optional) 🟡⚠
    # use the below line if you want to test the latest dev image
    # image: "jokobsk/netalertx-dev:latest" 
    image: "jokobsk/netalertx:latest"         # ⚠🔺🟡  This has changed (optional/required in future) 🟡🔺⚠
    network_mode: "host"        
    restart: unless-stopped
    volumes:
      - local/path/config:/app/config         # ⚠🔺  This has changed (required) 🔺⚠
      - local/path/db:/app/db                 # ⚠🔺  This has changed (required) 🔺⚠
      # (optional) useful for debugging if you have issues setting up the container
      - local/path/logs:/app/front/log        # ⚠🟡  This has changed (optional) 🟡⚠
    environment:
      - TZ=Europe/Berlin      
      - PORT=20211
```


## Example 2: Mapping files

> [!NOTE] 
> The recommendation is to map folders as in Example 1, map files directly only when needed. 

### Old docker-compose.yml

```yaml
version: "3"
services:
  pialert:
    container_name: pialert
    # use the below line if you want to test the latest dev image
    # image: "jokobsk/netalertx-dev:latest" 
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
version: "3"
services:
  netalertx:                                  # ⚠🟡  This has changed (optional) 🟡⚠
    container_name: netalertx                 # ⚠🟡  This has changed (optional) 🟡⚠
    # use the below line if you want to test the latest dev image
    # image: "jokobsk/netalertx-dev:latest" 
    image: "jokobsk/netalertx:latest"         # ⚠🔺🟡  This has changed (optional/required in future) 🟡🔺⚠
    network_mode: "host"        
    restart: unless-stopped
    volumes:
      - local/path/config/app.conf:/app/config/app.conf # ⚠🔺  This has changed (required) 🔺⚠
      - local/path/db/app.db:/app/db/app.db             # ⚠🔺  This has changed (required) 🔺⚠
      # (optional) useful for debugging if you have issues setting up the container
      - local/path/logs:/app/front/log                  # ⚠🟡  This has changed (optional) 🟡⚠
    environment:
      - TZ=Europe/Berlin      
      - PORT=20211
```
