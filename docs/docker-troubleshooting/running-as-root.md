# Running as Root User

## Issue Description

NetAlertX has detected that the container is running with root privileges (UID 0). This configuration bypasses all built-in security hardening measures designed to protect your system.

## Security Ramifications

Running security-critical applications like network monitoring tools as root grants unrestricted access to your host system. A successful compromise here could jeopardize your entire infrastructure, including other containers, host services, and potentially your network.

## Why You're Seeing This Issue

This typically occurs when you've explicitly overridden the container's default user in your Docker configuration, such as using `user: root` or `--user 0:0` in docker-compose.yml or docker run commands. The application is designed to run under a dedicated, non-privileged service account for security.

## How to Correct the Issue

Switch to the dedicated 'netalertx' user by removing any custom user directives:

- Remove `user:` entries from your docker-compose.yml
- Avoid `--user` flags in docker run commands
- Ensure the container runs with the default UID 20211:20211

After making these changes, restart the container. The application will automatically adjust ownership of required directories.

## Additional Resources

Docker Compose setup can be complex. We recommend starting with the default docker-compose.yml as a base and modifying it incrementally.

For detailed Docker Compose configuration guidance, see: [DOCKER_COMPOSE.md](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DOCKER_COMPOSE.md)