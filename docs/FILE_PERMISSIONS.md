# Managing File Permissions for NetAlertX on Nginx with Docker

> [!TIP]
> If you are facing permission issues, try to start the container without mapping your volumes. If that works, then the issue is permission related. You can try e.g., the following command: 
>  ``` 
>  docker run -d --rm --network=host \
>  -e TZ=Europe/Berlin \
>  -e PUID=200 -e PGID=200 \
>  -e PORT=20211 \
>  ghcr.io/jokob-sk/netalertx:latest
> ```
NetAlertX runs on an Nginx web server. On Alpine Linux, Nginx operates as the `nginx` user (if PUID and GID environment variables are not specified, nginx user UID will be set to 102, and its supplementary group `www-data` ID to 82). Consequently, files accessed or written by the NetAlertX application are owned by `nginx:www-data`.

Upon starting, NetAlertX changes nginx user UID and www-data GID to specified values (or defaults), and the ownership of files on the host system mapped to `/app/config` and `/app/db` in the container to `nginx:www-data`. This ensures that Nginx can access and write to these files. Since the user in the Docker container is mapped to a user on the host system by ID:GID, the files in `/app/config` and `/app/db` on the host system are owned by a user with the same ID and GID (defaults are ID 102 and GID 82). On different systems, this ID:GID may belong to different users, or there may not be a group with ID 82 at all.

Option to set specific user UID and GID can be useful for host system users needing to access these files (e.g., backup scripts).

### Permissions Table for Individual Folders

| Folder         | User   | User ID | Group     | Group ID | Permissions | Notes                                                               |
|----------------|--------|---------|-----------|----------|-------------|---------------------------------------------------------------------|
| `/app/config`  | nginx  | PUID (default 102)     | www-data  | PGID (default 82)       | rwxr-xr-x   | Ensure `nginx` can read/write; other users can read if in `www-data` |
| `/app/db`      | nginx  | PUID (default 102)     | www-data  | PGID (default 82)       | rwxr-xr-x   | Same as above                                                       |
