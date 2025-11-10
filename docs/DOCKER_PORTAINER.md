# Deploying NetAlertX in Portainer (via Stacks)

This guide shows you how to set up **NetAlertX** using Portainer’s **Stacks** feature.

![Portainer > Stacks](./img/DOCKER/DOCKER_PORTAINER.png)

---

## 1. Prepare Your Host

Before deploying, make sure you have a folder on your Docker host for NetAlertX data. Replace `APP_FOLDER` with your preferred location, for example `/opt` here:

```bash
mkdir -p /opt/netalertx/config
mkdir -p /opt/netalertx/db
mkdir -p /opt/netalertx/log
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

    volumes:
      - ${APP_FOLDER}/netalertx/config:/data/config
      - ${APP_FOLDER}/netalertx/db:/data/db
      # Optional: logs (useful for debugging setup issues, comment out for performance)
      - ${APP_FOLDER}/netalertx/log:/tmp/log

      # API storage options:
      # (Option 1) tmpfs (default, best performance)
      - type: tmpfs
        target: /tmp/api

      # (Option 2) bind mount (useful for debugging)
      # - ${APP_FOLDER}/netalertx/api:/tmp/api

    environment:
      - TZ=${TZ}
      - PORT=${PORT}
      - APP_CONF_OVERRIDE=${APP_CONF_OVERRIDE}
```

---

## 4. Configure Environment Variables

In the **Environment variables** section of Portainer, add the following:

* `APP_FOLDER=/opt` (or wherever you created the directories in step 1)
* `TZ=Europe/Berlin` (replace with your timezone)
* `PORT=22022` (or another port if needed)
* `APP_CONF_OVERRIDE={"GRAPHQL_PORT":"22023"}` (optional advanced settings)

---

## 5. Deploy the Stack

1. Scroll down and click **Deploy the stack**.
2. Portainer will pull the image and start NetAlertX.
3. Once running, access the app at:

```
http://<your-docker-host-ip>:22022
```

---

## 6. Verify and Troubleshoot

* Check logs via Portainer → **Containers** → `netalertx` → **Logs**.
* Logs are stored under `${APP_FOLDER}/netalertx/log` if you enabled that volume.

Once the application is running, configure it by reading the [initial setup](INITIAL_SETUP.md) guide, or [troubleshoot common issues](COMMON_ISSUES.md). 
