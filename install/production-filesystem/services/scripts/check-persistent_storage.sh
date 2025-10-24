#!/bin/sh
# check-storage.sh - Verify critical paths are persistent mounts.

warn_if_not_persistent_mount() {
    path="$1"
    # Check if the path is a mount point by looking for it in /proc/self/mountinfo
    # We are looking for an exact match in the mount point column (field 5)
    if awk -v target="${path}" '$5 == target {found=1} END {exit found ? 0 : 1}' /proc/self/mountinfo; then
        return 0
    fi

    failures=1
    YELLOW=$(printf '\033[1;33m')
    RESET=$(printf '\033[0m')
    >&2 printf "%s" "${YELLOW}"
    >&2 cat <<EOF
══════════════════════════════════════════════════════════════════════════════
⚠️  ATTENTION: ${path} is not a persistent mount.

    Your data in this directory may not persist across container restarts or
    upgrades. To ensure your settings and history are saved, you must mount
    this directory as a persistent volume.

    Fix: mount ${path} explicitly as a bind mount or a named volume:
        # Bind mount
        --mount type=bind,src=/path/on/host,dst=${path}

        # Named volume
        --mount type=volume,src=netalertx-data,dst=${path}

    Apply one of these mount options and restart the container.
══════════════════════════════════════════════════════════════════════════════
EOF
    >&2 printf "%s" "${RESET}"
}

# If NETALERTX_DEBUG=1 then we will exit
if [ "${NETALERTX_DEBUG}" = "1" ]; then
	exit 0
fi

failures=0
# NETALERTX_DB is a file, so we check its directory
warn_if_not_persistent_mount "$(dirname "${NETALERTX_DB_FILE}")"
warn_if_not_persistent_mount "${NETALERTX_CONFIG}"


if [ "${failures}" -ne 0 ]; then
    # We only warn, not exit, as this is not a critical failure
    # but the user should be aware of the potential data loss.
    sleep 5 # Give user time to read the message
fi
