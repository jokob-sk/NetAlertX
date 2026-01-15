# Read-Only Filesystem Mode

## Issue Description

The container is running as read-write instead of read-only mode. This reduces the security hardening of the appliance.

## Security Ramifications

Read-only root filesystem is a security best practice that prevents malicious modifications to the container's filesystem. Running read-write allows potential attackers to modify system files or persist malware within the container.

## Why You're Seeing This Issue

This occurs when the Docker configuration doesn't mount the root filesystem as read-only. The application is designed as a security appliance that should prevent filesystem modifications.

## How to Correct the Issue

Enable read-only mode:

- In docker-compose.yml, add: `read_only: true`
- For docker run, use: `--read-only`
- Ensure necessary directories are mounted as writable volumes (tmp, logs, etc.)

## Additional Resources

Docker Compose setup can be complex. We recommend starting with the default docker-compose.yml as a base and modifying it incrementally.

For detailed Docker Compose configuration guidance, see: [DOCKER_COMPOSE.md](https://docs.netalertx.com/DOCKER_COMPOSE)