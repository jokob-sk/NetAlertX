# Installation on a Synology NAS

There are different ways to install NetAlertX on a Synology, including SSH-ing into the machine and using the command line. For this guide, we will use the Project option in Container manager.

## Create the folder structure

The folders you are creating below will contain the configuration and the database. Back them up regularly.

1. Create a parent folder named `netalertx`
2. Create a `db` sub-folder

![Folder structure](./img/SYNOLOGY/01_Create_folder_structure.png)
![Folder structure](./img/SYNOLOGY/02_Create_folder_structure_db.png)
![Folder structure](./img/SYNOLOGY/03_Create_folder_structure_db.png)

3. Create a `config` sub-folder

![Folder structure](./img/SYNOLOGY/04_Create_folder_structure_config.png)

4. Note down the folders Locations:

![Getting the location](./img/SYNOLOGY/05_Access_folder_properties.png)
![Getting the location](./img/SYNOLOGY/06_Note_location.png)

5. Open **Container manager** -> **Project** and click **Create**.
6. Fill in the details:

- Project name: `netalertx`
- Path: `/app_storage/netalertx` (will differ from yours)
- Paste in the following template:


```yaml
version: "3"
services:
  netalertx:
    container_name: netalertx
    # use the below line if you want to test the latest dev image
    # image: "ghcr.io/jokob-sk/netalertx-dev:latest"
    image: "ghcr.io/jokob-sk/netalertx:latest"
    network_mode: "host"
    restart: unless-stopped
    cap_drop:       # Drop all capabilities for enhanced security
      - ALL
    cap_add:        # Re-add necessary capabilities
      - NET_RAW
      - NET_ADMIN
      - NET_BIND_SERVICE
    volumes:
      - /app_storage/netalertx/config:/data/config
      - /app_storage/netalertx/db:/data/db
      # to sync with system time
      - /etc/localtime:/etc/localtime:ro
    tmpfs:
      # All writable runtime state resides under /tmp; comment out to persist logs between restarts
      - "/tmp:uid=20211,gid=20211,mode=1700,rw,noexec,nosuid,nodev,async,noatime,nodiratime"
    environment:
      - PORT=20211
```

![Project settings](./img/SYNOLOGY/07_Create_project.png)

7. Replace the paths to your volume and comment out unnecessary line(s):

- This is only an example, your paths will differ.

```yaml
 volumes:
      - /volume1/app_storage/netalertx/config:/data/config
      - /volume1/app_storage/netalertx/db:/data/db
      # (optional) useful for debugging if you have issues setting up the container
      # - local/path/logs:/tmp/log <- commented out with # ⚠
```

![Adjusting docker-compose](./img/SYNOLOGY/08_Adjust_docker_compose_volumes.png)

8. (optional) Change the port number from `20211` to an unused port if this port is already used.
9. Build the project:

![Build](./img/SYNOLOGY/09_Run_and_build.png)

10. Navigate to `<Synology URL>:20211` (or your custom port).
11. Read the [Subnets](./SUBNETS.md) and [Plugins](/docs/PLUGINS.md) docs to complete your setup.


> [!TIP]
> If you are facing permissions issues run the following commands on your server. This will change the owner and assure sufficient access to the database and config files that are stored in the `/local_data_dir/db` and `/local_data_dir/config` folders (replace `local_data_dir` with the location where your `/db` and `/config` folders are located).
>
>  `sudo chown -R 20211:20211 /local_data_dir`
>
>  `sudo chmod -R a+rwx  /local_data_dir1`
>
