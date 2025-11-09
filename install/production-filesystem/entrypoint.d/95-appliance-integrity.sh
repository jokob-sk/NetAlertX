#!/bin/bash
# read-only-mode.sh detects and warns if running read-write on the root filesystem.

# This check is skipped in devcontainer mode as the devcontainer is not set up to run
# read-only and this would always trigger a warning. RW is required for development
# in the devcontainer.
if [ "${NETALERTX_DEBUG}" == "1" ]; then
    exit 0
fi

# Check if the root filesystem is mounted as read-only
if ! awk '$2 == "/" && $4 ~ /ro/ {found=1} END {exit !found}' /proc/mounts; then
    cat <<EOF
══════════════════════════════════════════════════════════════════════════════
⚠️  Warning: Container is running as read-write, not in read-only mode.

    Please mount the root filesystem as --read-only or use read-only: true
    https://github.com/jokob-sk/NetAlertX/blob/main/docs/docker-troubleshooting/read-only-filesystem.md
══════════════════════════════════════════════════════════════════════════════
EOF

fi
