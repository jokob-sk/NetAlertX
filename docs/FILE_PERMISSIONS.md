# Managing File Permissions for NetAlertX on Nginx with Docker

> [!TIP]
> If you are facing permission issues, try to start the container without mapping your volumes. If that works, then the issue is permission related. You can try e.g., the following command: 
>  ``` 
>  docker run -d --rm --network=host \
>  -e TZ=Europe/Berlin \
>  -e PORT=20211 \
>  jokobsk/netalertx:latest
> ```
NetAlertX runs on an Nginx web server. On Alpine Linux, Nginx operates as the `nginx` user (user ID 101, group ID 82 - `www-data`). Consequently, files accessed or written by the NetAlertX application are owned by `nginx:www-data`.

Upon starting, NetAlertX changes the ownership of files on the host system mapped to `/app/config` and `/app/db` in the container to `nginx:www-data`. This ensures that Nginx can access and write to these files. Since the user in the Docker container is mapped to a user on the host system by ID:GID, the files in `/app/config` and `/app/db` on the host system are owned by a user with the same ID and GID (ID 101 and GID 82). On different systems, this ID:GID may belong to different users (on Debian, the user with ID 82 is `uuidd`), or there may not be a user with ID 82 at all.

While this generally isn't problematic, it can cause issues for host system users needing to access these files (e.g., backup scripts). If users other than root need access to these files, it is recommended to add those users to the group with GID 82. If that group doesn't exist, it should be created.

### Permissions Table for Individual Folders

| Folder         | User   | User ID | Group     | Group ID | Permissions | Notes                                                               |
|----------------|--------|---------|-----------|----------|-------------|---------------------------------------------------------------------|
| `/app/config`  | nginx  | 101     | www-data  | 82       | rwxr-xr-x   | Ensure `nginx` can read/write; other users can read if in `www-data` |
| `/app/db`      | nginx  | 101     | www-data  | 82       | rwxr-xr-x   | Same as above                                                       |

### Steps to Add Users to Group

1. **Check if group exists:**
    ```sh
    getent group www-data
    ```

2. **Create group if it does not exist:**
    ```sh
    sudo groupadd -g 82 www-data
    ```

3. **Add user to group:**
    ```sh
    sudo usermod -aG www-data <username>
    ```

Replace `<username>` with the actual username that requires access.
