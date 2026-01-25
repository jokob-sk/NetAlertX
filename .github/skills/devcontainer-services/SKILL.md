---
name: restarting-netalertx-services
description: Control NetAlertX services inside the devcontainer. Use this when asked to start backend, start frontend, start nginx, start php-fpm, start crond, stop services, restart services, or check if services are running.
---

# Devcontainer Services

You operate inside the devcontainer. Do not use `docker exec`.

## Start Backend (Python)

```bash
/services/start-backend.sh
```

Backend runs with debugpy on port 5678 for debugging. Takes ~5 seconds to be ready.

## Start Frontend (nginx + PHP-FPM)

```bash
/services/start-php-fpm.sh &
/services/start-nginx.sh &
```

Launches almost instantly.

## Start Scheduler (CronD)

```bash
/services/start-crond.sh
```

## Stop All Services

```bash
pkill -f 'php-fpm83|nginx|crond|python3' || true
```

## Check Running Services

```bash
pgrep -a 'python3|nginx|php-fpm|crond'
```

## Service Ports

- Frontend (nginx): 20211
- Backend API: 20212
- GraphQL: 20212
- Debugpy: 5678
