# Missing Network Capabilities

## Issue Description

Raw network capabilities (NET_RAW, NET_ADMIN, NET_BIND_SERVICE) are missing. Tools that rely on these capabilities (e.g., nmap -sS, arp-scan, nbtscan) will not function.

## Security Ramifications

Network scanning and monitoring requires low-level network access that these capabilities provide. Without them, the application cannot perform essential functions like ARP scanning, port scanning, or passive network discovery, severely limiting its effectiveness.

## Why You're Seeing This Issue

This occurs when the container doesn't have the necessary Linux capabilities granted. Docker containers run with limited capabilities by default, and network monitoring tools need elevated network privileges.

## How to Correct the Issue

Add the required capabilities to your container:

- In docker-compose.yml:
  ```yaml
  cap_add:
    - NET_RAW
    - NET_ADMIN
    - NET_BIND_SERVICE
  ```
- For docker run: `--cap-add=NET_RAW --cap-add=NET_ADMIN --cap-add=NET_BIND_SERVICE`

## Additional Resources

Docker Compose setup can be complex. We recommend starting with the default docker-compose.yml as a base and modifying it incrementally.

For detailed Docker Compose configuration guidance, see: [DOCKER_COMPOSE.md](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DOCKER_COMPOSE.md)

## CAP_CHOWN required when cap_drop: [ALL]

When you start NetAlertX with `cap_drop: [ALL]`, the container loses `CAP_CHOWN`. The root priming step needs `CAP_CHOWN` to adjust ownership of `/data` and `/tmp` before dropping privileges to `PUID:PGID`. Without it, startup fails with a fatal `failed to chown` message and exits.

To fix:
- Add `CHOWN` back in `cap_add` when you also set `cap_drop: [ALL]`:

  ```yaml
  cap_drop:
    - ALL
  cap_add:
    - CHOWN
  ```

- Or pre-chown the mounted host paths to your target `PUID:PGID` so the priming step does not need the capability.

If you harden capabilities further, expect priming to fail until you restore the minimum set needed for ownership changes.