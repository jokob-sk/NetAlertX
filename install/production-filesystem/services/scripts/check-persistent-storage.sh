#!/bin/sh
# check-storage.sh - Verify critical paths are persistent mounts.

# Define non-persistent filesystem types to check against
# NOTE: 'overlay' and 'aufs' are the primary non-persistent types for container roots.
# 'tmpfs' and 'ramfs' are for specific non-persistent mounts.
NON_PERSISTENT_FSTYPES="tmpfs|ramfs|overlay|aufs"
MANDATORY_PERSISTENT_PATHS="/app/db /app/config"

# This function is now the robust persistence checker.
is_persistent_mount() {
    target_path="$1"

    mount_entry=$(awk -v path="${target_path}" '$2 == path { print $0 }' /proc/mounts)

    if [ -z "${mount_entry}" ]; then
        # CRITICAL FIX: If the mount entry is empty, check if it's one of the mandatory paths.
        if echo "${MANDATORY_PERSISTENT_PATHS}" | grep -w -q "${target_path}"; then
            # The path is mandatory but not mounted: FAIL (Not persistent)
            return 1
        else
            # Not mandatory and not a mount point: Assume persistence is inherited from parent (pass)
            return 0 
        fi
    fi

    # ... (rest of the original logic remains the same for explicit mounts)
    fs_type=$(echo "${mount_entry}" | awk '{print $3}')
    
    # Check if the filesystem type matches any non-persistent types
    if echo "${fs_type}" | grep -E -q "^(${NON_PERSISTENT_FSTYPES})$"; then
        return 1 # Not persistent (matched a non-persistent type)
    else
        return 0 # Persistent
    fi
}

warn_if_not_persistent_mount() {
    path="$1"

    if is_persistent_mount "${path}"; then
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
    upgrades. The filesystem type for this path is identified as non-persistent.

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
    sleep 1 # Give user time to read the message
fi