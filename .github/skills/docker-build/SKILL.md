---
name: netalertx-docker-build
description: Build Docker images for testing or production. Use this when asked to build container, build image, docker build, build test image, or launch production container.
---

# Docker Build

## Build Unit Test Image

Required after container/Dockerfile changes. Tests won't see changes until image is rebuilt.

```bash
docker buildx build -t netalertx-test .
```

Build time: ~30 seconds (or ~90s if venv stage changes)

## Build and Launch Production Container

Before launching, stop devcontainer services first to free ports.

```bash
cd /workspaces/NetAlertX
docker compose up -d --build --force-recreate
```

## Pre-Launch Checklist

1. Stop devcontainer services: `pkill -f 'php-fpm83|nginx|crond|python3'`
2. Close VS Code forwarded ports
3. Run the build command

## Production Container Details

- Image: `netalertx:latest`
- Container name: `netalertx`
- Network mode: host
- Ports: 20211 (UI), 20212 (API/GraphQL)
