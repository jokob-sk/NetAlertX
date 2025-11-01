# File Permission Issues

## Issue Description

NetAlertX cannot read from or write to critical configuration and database files. This prevents the application from saving data, logs, or configuration changes.

## Security Ramifications

Incorrect file permissions can expose sensitive configuration data or database contents to unauthorized access. Network monitoring tools handle sensitive information about devices on your network, and improper permissions could lead to information disclosure.

## Why You're Seeing This Issue

This occurs when the mounted volumes for configuration and database files don't have proper ownership or permissions set for the netalertx user (UID 20211). The container expects these files to be accessible by the service account, not root or other users.

## How to Correct the Issue

Fix permissions on the host system for the mounted directories:

- Ensure the config and database directories are owned by the netalertx user: `chown -R 20211:20211 /path/to/config /path/to/db`
- Set appropriate permissions: `chmod -R 755 /path/to/config /path/to/db` for directories, `chmod 644` for files
- Alternatively, restart the container with root privileges temporarily to allow automatic permission fixing, then switch back to the default user

## Additional Resources

Docker Compose setup can be complex. We recommend starting with the default docker-compose.yml as a base and modifying it incrementally.

For detailed Docker Compose configuration guidance, see: [DOCKER_COMPOSE.md](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DOCKER_COMPOSE.md)