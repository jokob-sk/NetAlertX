# Nginx Configuration Mount Issues

## Issue Description

You've configured a custom port for NetAlertX, but the required nginx configuration mount is missing or not writable. Without this mount, the container cannot apply your port changes and will fall back to the default port 20211.

## Security Ramifications

Running in read-only mode (as recommended) prevents the container from modifying its own nginx configuration. Without a writable mount, custom port configurations cannot be applied, potentially exposing the service on unintended ports or requiring fallback to defaults.

## Why You're Seeing This Issue

This occurs when you set a custom PORT environment variable (other than 20211) but haven't provided a writable mount for nginx configuration. The container needs to write custom nginx config files when running in read-only mode.

## How to Correct the Issue

If you want to use a custom port, create a bind mount for the nginx configuration:

- Create a directory on your host: `mkdir -p /path/to/nginx-config`
- Add to your docker-compose.yml:
  ```yaml
  volumes:
    - /path/to/nginx-config:/app/system/services/active/config
  environment:
    - PORT=your_custom_port
  ```
- Ensure it's owned by the netalertx user: `chown -R 20211:20211 /path/to/nginx-config`
- Set permissions: `chmod -R 700 /path/to/nginx-config`

If you don't need a custom port, simply omit the PORT environment variable and the container will use 20211 by default.

## Additional Resources

Docker Compose setup can be complex. We recommend starting with the default docker-compose.yml as a base and modifying it incrementally.

For detailed Docker Compose configuration guidance, see: [DOCKER_COMPOSE.md](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DOCKER_COMPOSE.md)

For detailed Docker Compose configuration guidance, see: [DOCKER_COMPOSE.md](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DOCKER_COMPOSE.md)