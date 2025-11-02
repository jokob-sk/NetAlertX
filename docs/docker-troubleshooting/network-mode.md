# Network Mode Configuration

## Issue Description

NetAlertX is not running with `--network=host`. Bridge networking blocks passive discovery (ARP, NBNS, mDNS) and active scanning accuracy.

## Security Ramifications

Host networking is required for comprehensive network monitoring. Bridge mode isolates the container from raw network access needed for ARP scanning, passive discovery protocols, and accurate device detection. Without host networking, the application cannot fully monitor your network.

## Why You're Seeing This Issue

This occurs when your Docker configuration uses bridge networking instead of host networking. Network monitoring requires direct access to the host's network interfaces to perform passive discovery and active scanning.

## How to Correct the Issue

Enable host networking mode:

- In docker-compose.yml, add: `network_mode: host`
- For docker run, use: `--network=host`
- Ensure the container has required capabilities: `--cap-add=NET_RAW --cap-add=NET_ADMIN --cap-add=NET_BIND_SERVICE`

## Additional Resources

Docker Compose setup can be complex. We recommend starting with the default docker-compose.yml as a base and modifying it incrementally.

For detailed Docker Compose configuration guidance, see: [DOCKER_COMPOSE.md](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DOCKER_COMPOSE.md)