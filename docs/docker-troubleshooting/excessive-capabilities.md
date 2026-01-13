# Excessive Capabilities

## Issue Description

Excessive Linux capabilities are detected beyond the necessary NET_ADMIN, NET_BIND_SERVICE, and NET_RAW. This may indicate overly permissive container configuration.

## Security Ramifications

While the detected capabilities might not directly harm operation, running with more privileges than necessary increases the attack surface. If the container is compromised, additional capabilities could allow broader system access or privilege escalation.

## Why You're Seeing This Issue

This occurs when your Docker configuration grants more capabilities than required for network monitoring. The application only needs specific network-related capabilities for proper function.

## How to Correct the Issue

Limit capabilities to only those required:

- In docker-compose.yml, specify only needed caps:
  ```yaml
  cap_add:
    - NET_RAW
    - NET_ADMIN
    - NET_BIND_SERVICE
  ```
- Remove any unnecessary `--cap-add` or `--privileged` flags from docker run commands

## Additional Resources

Docker Compose setup can be complex. We recommend starting with the default docker-compose.yml as a base and modifying it incrementally.

For detailed Docker Compose configuration guidance, see: [DOCKER_COMPOSE.md](https://docs.netalertx.com/DOCKER_COMPOSE)