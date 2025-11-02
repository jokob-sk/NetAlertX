# Port Conflicts

## Issue Description

The configured application port (default 20211) or GraphQL API port (default 20212) is already in use by another service. This commonly occurs when you already have another NetAlertX instance running.

## Security Ramifications

Port conflicts prevent the application from starting properly, leaving network monitoring services unavailable. Running multiple instances on the same ports can also create configuration confusion and potential security issues if services are inadvertently exposed.

## Why You're Seeing This Issue

This error typically occurs when:

- **You already have NetAlertX running** - Another Docker container or devcontainer instance is using the default ports 20211 and 20212
- **Port conflicts with other services** - Other applications on your system are using these ports
- **Configuration error** - Both PORT and GRAPHQL_PORT environment variables are set to the same value

## How to Correct the Issue

### Check for Existing NetAlertX Instances

First, check if you already have NetAlertX running:

```bash
# Check for running NetAlertX containers
docker ps | grep netalertx

# Check for devcontainer processes
ps aux | grep netalertx

# Check what services are using the ports
netstat -tlnp | grep :20211
netstat -tlnp | grep :20212
```

### Stop Conflicting Instances

If you find another NetAlertX instance:

```bash
# Stop specific container
docker stop <container_name>

# Stop all NetAlertX containers
docker stop $(docker ps -q --filter ancestor=jokob-sk/netalertx)

# Stop devcontainer services
# Use VS Code command palette: "Dev Containers: Rebuild Container"
```

### Configure Different Ports

If you need multiple instances, configure unique ports:

```yaml
environment:
  - PORT=20211          # Main application port
  - GRAPHQL_PORT=20212  # GraphQL API port
```

For a second instance, use different ports:

```yaml
environment:
  - PORT=20213          # Different main port
  - GRAPHQL_PORT=20214  # Different API port
```

### Alternative: Use Different Container Names

When running multiple instances, use unique container names:

```yaml
services:
  netalertx-primary:
    # ... existing config
  netalertx-secondary:
    # ... config with different ports
```

## Additional Resources

Docker Compose setup can be complex. We recommend starting with the default docker-compose.yml as a base and modifying it incrementally.

For detailed Docker Compose configuration guidance, see: [DOCKER_COMPOSE.md](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DOCKER_COMPOSE.md)