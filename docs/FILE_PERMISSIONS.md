# Managing File Permissions for NetAlertX on a Read-Only Container

> [!TIP]
> NetAlertX runs in a **secure, read-only Alpine-based container** under a dedicated `netalertx` user (UID 20211, GID 20211). All writable paths are either mounted as **persistent volumes** or **`tmpfs` filesystems**. This ensures consistent file ownership and prevents privilege escalation.

---

## Writable Paths

NetAlertX requires certain paths to be writable at runtime. These paths should be mounted either as **host volumes** or **`tmpfs`** in your `docker-compose.yml` or `docker run` command:

| Path                                 | Purpose                             | Notes                                                  |
| ------------------------------------ | ----------------------------------- | ------------------------------------------------------ |
| `/data/config`                        | Application configuration           | Persistent volume recommended                          |
| `/data/db`                            | Database files                      | Persistent volume recommended                          |
| `/tmp/log`                           | Logs                                | Lives under `/tmp`; optional host bind to retain logs  |
| `/tmp/api`                           | API cache                           | Subdirectory of `/tmp`                                 |
| `/tmp/nginx/active-config` | Active nginx configuration override | Mount `/tmp` (or override specific file)               |
| `/tmp/run`                      | Runtime directories for nginx & PHP | Subdirectory of `/tmp`                                 |
| `/tmp`                               | PHP session save directory          | Backed by `tmpfs` for runtime writes                   |

> Mounting `/tmp` as `tmpfs` automatically covers all of its subdirectories (`log`, `api`, `run`, `nginx/active-config`, etc.).

> All these paths will have **UID 20211 / GID 20211** inside the container. Files on the host will appear owned by `20211:20211`.

---

## Fixing Permission Problems

Sometimes, permission issues arise if your existing host directories were created by a previous container running as root or another UID. The container will fail to start with "Permission Denied" errors.

### Solution

1. **Run the container once as root** (`--user "0"`) to allow it to correct permissions automatically:

```bash
docker run -it --rm --name netalertx --user "0" \
  -v /local_data_dir/config:/data/config \
  -v /local_data_dir/db:/data/db \
  --tmpfs /tmp:uid=20211,gid=20211,mode=1700 \
  ghcr.io/jokob-sk/netalertx:latest
```

2. Wait for logs showing **permissions being fixed**. The container will then **hang intentionally**.
3. Press **Ctrl+C** to stop the container.
4. Start the container normally with your `docker-compose.yml` or `docker run` command.

> The container startup script detects `root` and runs `chown -R 20211:20211` on all volumes, fixing ownership for the secure `netalertx` user.

> [!TIP]
> If you are facing permissions issues run the following commands on your server. This will change the owner and assure sufficient access to the database and config files that are stored in the `/local_data_dir/db` and `/local_data_dir/config` folders (replace `local_data_dir` with the location where your `/db` and `/config` folders are located).
>  ```bash
>  sudo chown -R 20211:20211 /local_data_dir
>  sudo chmod -R a+rwx  /local_data_dir
>  ```

---

## Example: docker-compose.yml with `tmpfs`

```yaml
services:
  netalertx:
    container_name: netalertx
    image: "ghcr.io/jokob-sk/netalertx"
    network_mode: "host"
    cap_drop:                                       # Drop all capabilities for enhanced security
      - ALL
    cap_add:                                        # Add only the necessary capabilities
      - NET_ADMIN                                   # Required for ARP scanning
      - NET_RAW                                     # Required for raw socket operations
      - NET_BIND_SERVICE                            # Required to bind to privileged ports (nbtscan)
    restart: unless-stopped
    volumes:
      - /local_data_dir/config:/data/config
      - /local_data_dir/db:/data/db
      - /etc/localtime:/etc/localtime
    environment:
      - PORT=20211
    tmpfs:
      - "/tmp:uid=20211,gid=20211,mode=1700,rw,noexec,nosuid,nodev,async,noatime,nodiratime"
```

> This setup ensures all writable paths are either in `tmpfs` or host-mounted, and the container never writes outside of controlled volumes.


