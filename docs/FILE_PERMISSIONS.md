# Managing File Permissions for NetAlertX on a Read-Only Container

> [!TIP]
> NetAlertX runs in a **secure, read-only Alpine-based container** under a dedicated `netalertx` user (UID 20211, GID 20211). All writable paths are either mounted as **persistent volumes** or **`tmpfs` filesystems**. This ensures consistent file ownership and prevents privilege escalation.

---

## Writable Paths

NetAlertX requires certain paths to be writable at runtime. These paths should be mounted either as **host volumes** or **`tmpfs`** in your `docker-compose.yml` or `docker run` command:

| Path                                 | Purpose                             | Notes                                                  |
| ------------------------------------ | ----------------------------------- | ------------------------------------------------------ |
| `/app/config`                        | Application configuration           | Persistent volume recommended                          |
| `/app/db`                            | Database files                      | Persistent volume recommended                          |
| `/app/log`                           | Logs                                | Can be `tmpfs` for speed or host volume to retain logs |
| `/app/api`                           | API cache                           | Use `tmpfs` for faster access                          |
| `/services/config/nginx/conf.active` | Active nginx configuration override | `tmpfs` recommended or customized file mounted        |
| `/services/run`                      | Runtime directories for nginx & PHP | `tmpfs` required                                       |
| `/tmp`                               | PHP session save directory          | `tmpfs` required                                       |

> All these paths will have **UID 20211 / GID 20211** inside the container. Files on the host will appear owned by `20211:20211`.

---

## Fixing Permission Problems

Sometimes, permission issues arise if your existing host directories were created by a previous container running as root or another UID. The container will fail to start with "Permission Denied" errors.

### Solution

1. **Run the container once as root** (`--user "0"`) to allow it to correct permissions automatically:

```bash
docker run -it --rm --name netalertx --user "0" \
  -v local/path/config:/app/config \
  -v local/path/db:/app/db \
  ghcr.io/jokob-sk/netalertx:latest
```

2. Wait for logs showing **permissions being fixed**. The container will then **hang intentionally**.
3. Press **Ctrl+C** to stop the container.
4. Start the container normally with your `docker-compose.yml` or `docker run` command.

> The container startup script detects `root` and runs `chown -R 20211:20211` on all volumes, fixing ownership for the secure `netalertx` user.

---

## Example: docker-compose.yml with `tmpfs`

```yaml
services:
  netalertx:                                  
    container_name: netalertx                
    image: "ghcr.io/jokob-sk/netalertx"  
    network_mode: "host"       
    cap_add:
      - NET_RAW
      - NET_ADMIN
      - NET_BIND_SERVICE
    restart: unless-stopped
    volumes:
      - local/path/config:/app/config         
      - local/path/db:/app/db                 
    environment:
      - TZ=Europe/Berlin      
      - PORT=20211
    tmpfs: 
      - "/app/log:uid=20211,gid=20211,mode=1700,rw,noexec,nosuid,nodev,async,noatime,nodiratime"
      - "/app/api:uid=20211,gid=20211,mode=1700,rw,noexec,nosuid,nodev,sync,noatime,nodiratime"  
      - "/services/config/nginx/conf.active:uid=20211,gid=20211,mode=1700,rw,noexec,nosuid,nodev,async,noatime,nodiratime"
      - "/services/run:uid=20211,gid=20211,mode=1700,rw,noexec,nosuid,nodev,async,noatime,nodiratime"
      - "/tmp:uid=20211,gid=20211,mode=1700,rw,noexec,nosuid,nodev,async,noatime,nodiratime"
```

> This setup ensures all writable paths are either in `tmpfs` or host-mounted, and the container never writes outside of controlled volumes.


