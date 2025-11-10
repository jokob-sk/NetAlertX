# The NetAlertX Container Operator's Guide

> [!WARNING]
> ⚠️ **Important:** The documentation has been recently updated and some instructions may have changed.  
> If you are using the currently live production image, please follow the instructions on [Docker Hub](https://hub.docker.com/r/jokobsk/netalertx) for building and running the container.  
> These docs reflect the latest development version and may differ from the production image.

This guide assumes you are starting with the official `docker-compose.yml` file provided with the project. We strongly recommend you start with or migrate to this file as your baseline and modify it to suit your specific needs (e.g., changing file paths). While there are many ways to configure NetAlertX, the default file is designed to meet the mandatory security baseline with layer-2 networking capabilities while operating securely and without startup warnings.

This guide provides direct, concise solutions for common NetAlertX administrative tasks. It is structured to help you identify a problem, implement the solution, and understand the details.

## Guide Contents
 
- Using a Local Folder for Configuration  
- Migrating from a Local Folder to a Docker Volume  
- Applying a Custom Nginx Configuration  
- Mounting Additional Files for Plugins  


> [!NOTE]
>
>  Other relevant resources
>  - [Fixing Permission Issues](./FILE_PERMISSIONS.md)
>  - [Handling Backups](./BACKUPS.md)
>  - [Accessing Application Logs](./LOGGING.md)

---

## Task: Using a Local Folder for Configuration

### Problem

You want to edit your `app.conf` and other configuration files directly from your host machine, instead of using a Docker-managed volume.

### Solution

1. Stop the container:

   ```bash
   docker-compose down
   ```
2. (Optional but Recommended) Back up your data using the method in Part 1.
3. Create a local folder on your host machine (e.g., `/data/netalertx_config`).
4. Edit `docker-compose.yml`:

   * **Comment out** the `netalertx_config` volume entry.
   * **Uncomment** and **set the path** for the "Example custom local folder" bind mount entry.

   ```yaml
   ...
       volumes:
         # - type: volume
         #   source: netalertx_config
         #   target: /data/config
         #   read_only: false
   ...
       # Example custom local folder called /data/netalertx_config
       - type: bind
         source: /data/netalertx_config
         target: /data/config
         read_only: false
   ...
   ```
5. (Optional) Restore your backup.
6. Restart the container:

   ```bash
   docker-compose up -d
   ```

### About This Method

This replaces the Docker-managed volume with a "bind mount." This is a direct mapping between a folder on your host computer (`/data/netalertx_config`) and a folder inside the container (`/data/config`), allowing you to edit the files directly.

---

## Task: Migrating from a Local Folder to a Docker Volume

### Problem

You are currently using a local folder (bind mount) for your configuration (e.g., `/data/netalertx_config`) and want to switch to the recommended Docker-managed volume (`netalertx_config`).

### Solution

1. Stop the container:

   ```bash
   docker-compose down
   ```
2. Edit `docker-compose.yml`:

   * **Comment out** the bind mount entry for your local folder.
   * **Uncomment** the `netalertx_config` volume entry.

   ```yaml
   ...
       volumes:
         - type: volume
           source: netalertx_config
           target: /data/config
           read_only: false
   ...
       # Example custom local folder called /data/netalertx_config
       # - type: bind
       #   source: /data/netalertx_config
       #   target: /data/config
       #   read_only: false
   ...
   ```
3. (Optional) Initialize the volume:

   ```bash
   docker-compose up -d && docker-compose down
   ```
4. Run the migration command (**replace `/data/netalertx_config` with your actual path**):

   ```bash
   docker run --rm -v netalertx_config:/config -v /data/netalertx_config:/local-config alpine \
     sh -c "tar -C /local-config -c . | tar -C /config -x"
   ```
5. Restart the container:

   ```bash
   docker-compose up -d
   ```

### About This Method

This uses a temporary `alpine` container that mounts *both* your source folder (`/local-config`) and destination volume (`/config`). The `tar ... | tar ...` command safely copies all files, including hidden ones, preserving structure.

---

## Task: Applying a Custom Nginx Configuration

### Problem

You need to override the default Nginx configuration to add features like LDAP, SSO, or custom SSL settings.

### Solution

1. Stop the container:

   ```bash
   docker-compose down
   ```
2. Create your custom config file on your host (e.g., `/data/my-netalertx.conf`).
3. Edit `docker-compose.yml`:

   ```yaml
   ...
       # Use a custom Enterprise-configured nginx config for ldap or other settings
       - /data/my-netalertx.conf:/tmp/nginx/active-config/netalertx.conf:ro
   ...
   ```
4. Restart the container:

   ```bash
   docker-compose up -d
   ```

### About This Method

Docker’s bind mount overlays your host file (`my-netalertx.conf`) on top of the default file inside the container. The container remains read-only, but Nginx reads your file as if it were the default.

---

## Task: Mounting Additional Files for Plugins

### Problem

A plugin (like `DHCPLSS`) needs to read a file from your host machine (e.g., `/var/lib/dhcp/dhcpd.leases`).

### Solution

1. Stop the container:

   ```bash
   docker-compose down
   ```
2. Edit `docker-compose.yml` and add a new line under the `volumes:` section:

   ```yaml
   ...
       volumes:
   ...
         # Mount for DHCPLSS plugin
         - /var/lib/dhcp/dhcpd.leases:/mnt/dhcpd.leases:ro
   ...
   ```
3. Restart the container:

   ```bash
   docker-compose up -d
   ```
4. In the NetAlertX web UI, configure the plugin to read from:

   ```
   /mnt/dhcpd.leases
   ```

### About This Method

This maps your host file to a new, read-only (`:ro`) location inside the container. The plugin can then safely read this file without exposing anything else on your host filesystem.


