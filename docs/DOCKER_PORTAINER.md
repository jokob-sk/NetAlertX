# Deploying NetAlertX in Portainer (via Stacks)

This guide shows you how to set up **NetAlertX** using Portainer’s **Stacks** feature.

![Portainer > Stacks](./img/DOCKER/DOCKER_PORTAINER.png)

---

## 1. Prepare Your Host

Before deploying, make sure you have a folder on your Docker host for NetAlertX data. Replace `APP_FOLDER` with your preferred location, for example `/local_data_dir` here:

```bash
mkdir -p /local_data_dir/netalertx/config
mkdir -p /local_data_dir/netalertx/db
mkdir -p /local_data_dir/netalertx/log
```

---

## 2. Open Portainer Stacks

1. Log in to your **Portainer UI**.
2. Navigate to **Stacks** → **Add stack**.
3. Give your stack a name (e.g., `netalertx`).

---

## 3. Paste the Stack Configuration

Copy and paste the following YAML into the **Web editor**:

```yaml
services:
  netalertx:
    container_name: netalertx
    # Use this line for stable release
    image: "ghcr.io/jokob-sk/netalertx:latest"
    # Or, use this for the latest development build
    # image: "ghcr.io/jokob-sk/netalertx-dev:latest"
    network_mode: "host"
    restart: unless-stopped
    cap_drop:       # Drop all capabilities for enhanced security
      - ALL
    cap_add:        # Re-add necessary capabilities
      - NET_RAW
      - NET_ADMIN
      - NET_BIND_SERVICE
    volumes:
      - ${APP_FOLDER}/netalertx/config:/data/config
      - ${APP_FOLDER}/netalertx/db:/data/db
      # to sync with system time
      - /etc/localtime:/etc/localtime:ro
    tmpfs:
      # All writable runtime state resides under /tmp; comment out to persist logs between restarts
      - "/tmp:uid=20211,gid=20211,mode=1700,rw,noexec,nosuid,nodev,async,noatime,nodiratime"
    environment:
      - PORT=${PORT}
      - APP_CONF_OVERRIDE=${APP_CONF_OVERRIDE}
```

---

## 4. Configure Environment Variables

In the **Environment variables** section of Portainer, add the following:

* `APP_FOLDER=/local_data_dir` (or wherever you created the directories in step 1)
* `PORT=22022` (or another port if needed)
* `APP_CONF_OVERRIDE={"GRAPHQL_PORT":"22023"}` (optional advanced settings, otherwise the backend API server PORT defaults to `20212`)

---

## 5. Ensure permissions

> [!TIP]
> If you are facing permissions issues run the following commands on your server. This will change the owner and assure sufficient access to the database and config files that are stored in the `/local_data_dir/db` and `/local_data_dir/config` folders (replace `local_data_dir` with the location where your `/db` and `/config` folders are located).
>
>  `sudo chown -R 20211:20211 /local_data_dir`
>
>  `sudo chmod -R a+rwx  /local_data_dir`
>


---

## 6. Deploy the Stack

1. Scroll down and click **Deploy the stack**.
2. Portainer will pull the image and start NetAlertX.
3. Once running, access the app at:

```
http://<your-docker-host-ip>:22022
```

---

## 7. Verify and Troubleshoot

* Check logs via Portainer → **Containers** → `netalertx` → **Logs**.
* Logs are stored under `${APP_FOLDER}/netalertx/log` if you enabled that volume.

Once the application is running, configure it by reading the [initial setup](INITIAL_SETUP.md) guide, or [troubleshoot common issues](COMMON_ISSUES.md).
