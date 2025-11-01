# Incorrect Container User

## Issue Description

NetAlertX is running as UID:GID other than the expected 20211:20211. This bypasses hardened permissions, file ownership, and runtime isolation safeguards.

## Security Ramifications

The application is designed with security hardening that depends on running under a dedicated, non-privileged service account. Using a different user account can silently fail future upgrades and removes crucial isolation between the container and host system.

## Why You're Seeing This Issue

This occurs when you override the container's default user with custom `user:` directives in docker-compose.yml or `--user` flags in docker run commands. The container expects to run as the netalertx user for proper security isolation.

## How to Correct the Issue

Restore the container to the default user:

- Remove any `user:` overrides from docker-compose.yml
- Avoid `--user` flags in docker run commands
- Allow the container to run with its default UID:GID 20211:20211
- Recreate the container so volume ownership is reset automatically

## Additional Resources

Docker Compose setup can be complex. We recommend starting with the default docker-compose.yml as a base and modifying it incrementally.

For detailed Docker Compose configuration guidance, see: [DOCKER_COMPOSE.md](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DOCKER_COMPOSE.md)