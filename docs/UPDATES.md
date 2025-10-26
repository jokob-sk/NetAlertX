# Docker Update Strategies to upgrade NetAlertX

> [!WARNING] 
> For versions prior to `v25.6.7` upgrade to version `v25.5.24` first (`docker pull ghcr.io/jokob-sk/netalertx:25.5.24`) as later versions don't support a full upgrade. Alternatively, devices and settings can be migrated manually, e.g. via [CSV import](./DEVICES_BULK_EDITING.md).

This guide outlines approaches for updating Docker containers, usually when upgrading to a newer version of NetAlertX. Each method offers different benefits depending on the situation. Here are the methods:

- Manual: Direct commands to stop, remove, and rebuild containers.
- Dockcheck: Semi-automated with more control, suited for bulk updates.
- Watchtower: Fully automated, runs continuously to check and update containers.
- Portainer: Manual with UI.

You can choose any approach that fits your workflow.

> In the examples I assume that the container name is `netalertx` and the image name is `netalertx` as well.

> [!NOTE]
> See also [Backup strategies](./BACKUPS.md) to be on the safe side.  

## 1. Manual Updates

Use this method when you need precise control over a single container or when dealing with a broken container that needs immediate attention.
Example Commands

To manually update the `netalertx` container, stop it, delete it, remove the old image, and start a fresh one with `docker-compose`.

```bash
# Stop the container
sudo docker container stop netalertx

# Remove the container
sudo docker container rm netalertx

# Remove the old image
sudo docker image rm netalertx

# Pull and start a new container
sudo docker-compose up -d
```

### Alternative: Force Pull with Docker Compose

You can also use `--pull always` to ensure Docker pulls the latest image before starting the container:

```bash
sudo docker-compose up --pull always -d
```

## 2. Dockcheck for Bulk Container Updates

Always check the [Dockcheck](https://github.com/mag37/dockcheck) docs if encountering issues with the guide below. 

Dockcheck is a useful tool if you have multiple containers to update and some flexibility for handling potential issues that might arise during mass updates. Dockcheck allows you to inspect each container and decide when to update.

### Example Workflow with Dockcheck

You might use Dockcheck to:

- Inspect container versions.
- Pull the latest images in bulk.
- Apply updates selectively.

Dockcheck can help streamline bulk updates, especially if you’re managing multiple containers.

Below is a script I use to run an update of the Dockcheck script and start a check for new containers:

```bash
cd /path/to/Docker &&
rm dockcheck.sh &&
wget https://raw.githubusercontent.com/mag37/dockcheck/main/dockcheck.sh &&
sudo chmod +x dockcheck.sh &&
sudo ./dockcheck.sh
```

## 3. Automated Updates with Watchtower

Always check the [watchtower](https://github.com/containrrr/watchtower) docs if encountering issues with the guide below. 

Watchtower monitors your Docker containers and automatically updates them when new images are available. This is ideal for ongoing updates without manual intervention.

### Setting Up Watchtower

#### 1. Pull the Watchtower Image:

```bash
docker pull containrrr/watchtower
```

#### 2. Run Watchtower to update all images:

```bash
docker run -d \
  --name watchtower \
  -v /var/run/docker.sock:/var/run/docker.sock \
  containrrr/watchtower \
  --interval 300 # Check for updates every 5 minutes
```

#### 3. Run Watchtower to update only NetAlertX: 

You can specify which containers to monitor by listing them. For example, to monitor netalertx only:

```bash
docker run -d \
  --name watchtower \
  -v /var/run/docker.sock:/var/run/docker.sock \
  containrrr/watchtower netalertx

```

## 4. Portainer controlled image

This assumes you're using Portainer to manage Docker (or Docker Swarm) and want to pull the latest version of an image and redeploy the container.

> [!NOTE]
> * Portainer does **not auto-update** containers. For automation, use **Watchtower** or similar tools.
> * Make sure you have the [persistent volumes mounted or backups ready](BACKUPS.md) before recreating.

### 4.1 Steps to Update an Image in Portainer (Standalone Docker)

1. **Login to Portainer.**
2. Go to **"Containers"** in the left sidebar.
3. Find the container you want to update, click its name.
4. Click **"Recreate"** (top right).
5. **Tick**: _Pull latest image_ (this ensures Portainer fetches the newest version from Docker Hub or your registry).
6. Click **"Recreate"** again.
7. Wait for the container to be stopped, removed, and recreated with the updated image.

### 4.2 For Docker Swarm Services

If you're using Docker Swarm (under **"Stacks"** or **"Services"**):

1. Go to **"Stacks"**.
2. Select the stack managing the container.
3. Click **"Editor"** (or "Update the Stack").
4. Add a version tag or use `:latest` if your image tag is `latest` (not recommended for production).
5. Click **"Update the Stack"**. ⚠ Portainer will not pull the new image unless the tag changes OR the stack is forced to recreate.
6. If image tag hasn't changed, go to **"Services"**, find the service, and click **"Force Update"**.

## Summary

| Method     | Type         | Pros                            | Cons                         |
|------------|--------------|----------------------------------|------------------------------|
| Manual     | CLI          | Full control, no dependencies   | Tedious for many containers |
| Dockcheck  | CLI Script   | Great for batch updates         | Needs setup, semi-automated |
| Watchtower | Daemonized   | Fully automated updates         | Less control, version drift |
| Portainer  | UI           | Easy via web interface          | No auto-updates             |

These approaches allow you to maintain flexibility in how you update Docker containers, depending on the urgency and scale of the update.
