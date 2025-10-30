#!/bin/bash
# read-only-mode.sh detects and warns if running read-write on the root filesystem.

# Check if the root filesystem is mounted as read-only
if ! awk '$2 == "/" && $4 ~ /ro/ {found=1} END {exit !found}' /proc/mounts; then
    cat <<EOF
══════════════════════════════════════════════════════════════════════════════
⚠️  Warning: Container is running as read-write, not in read-only mode.

    Please mount the root filesystem as --read-only or use read-only: true
    https://github.com/jokob-sk/NetAlertX/blob/main/docs/DOCKER_COMPOSE.md
══════════════════════════════════════════════════════════════════════════════
EOF

fi
