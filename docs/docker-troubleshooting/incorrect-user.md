# Incorrect Container User

## Issue Description

NetAlertX is running as a UID:GID that does not match the runtime service user configured for this container (default 20211:20211). Hardened ownership on writable paths may block writes if the UID/GID do not align with mounted volumes and tmpfs settings.

## Security Ramifications

The image uses a dedicated service user for writes and a readonly lock owner (UID 20211) for code/venv with 004/005 permissions. Running as an arbitrary UID is supported, but only when writable mounts (`/data`, `/tmp/*`) are owned by that UID. Misalignment can cause startup failures or unexpected permission escalation attempts.

## Why You're Seeing This Issue

- A `user:` override in docker-compose.yml or `--user` flag on `docker run` changes the runtime UID/GID without updating mount ownership.
- Tmpfs mounts still use `uid=20211,gid=20211` while the container runs as another UID.
- Host bind mounts (e.g., `/data`) are owned by a different UID.

## How to Correct the Issue

Option A: Use defaults (recommended)
- Remove custom `user:` overrides and `--user` flags.
- Let the container run as the built-in service user (UID/GID 20211) and keep tmpfs at `uid=20211,gid=20211`.

Option B: Run with a custom UID/GID
- Set `user:` (or `NETALERTX_UID/NETALERTX_GID`) to your desired UID/GID.
- Align mounts: ensure `/data` (and any `/tmp/*` tmpfs) use the same `uid=`/`gid=` and that host bind mounts are chowned to that UID/GID.
- Recreate the container so ownership is consistent.

## Additional Resources

- Default compose and tmpfs guidance: [DOCKER_COMPOSE.md](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DOCKER_COMPOSE.md)
- General Docker install and runtime notes: [DOCKER_INSTALLATION.md](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DOCKER_INSTALLATION.md)