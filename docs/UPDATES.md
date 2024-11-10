# Docker Update Strategies for NetAlertX

This guide outlines several approaches for updating Docker containers, specifically using NetAlertX. Each method offers different benefits depending on the situation. Here are the methods:

- Manual: Direct commands to stop, remove, and rebuild containers.
- Dockcheck: Semi-automated with more control, suited for bulk updates.
- Watchtower: Fully automated, runs continuously to check and update containers.

You can choose any approach that fits your workflow.

> In the examples I assume that the container name is `netalertx` and the image name is `netalertx` as well.

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

## Summary

- Manual: Ideal for individual or critical updates.
- Dockcheck: Suitable for controlled, mass updates.
- Watchtower: Fully automated, best for continuous deployment setups.

These approaches allow you to maintain flexibility in how you update Docker containers, depending on the urgency and scale of the update.
