#!/bin/sh
# check-storage.sh - Verify critical paths are persistent mounts.

# Get the Device ID of the root filesystem (overlayfs/tmpfs)
# The default, non-persistent container root will have a unique Device ID.
# Persistent mounts will have a different Device ID (unless it's a bind mount
# from the host's root, which is a rare and unusual setup for a single volume check).
ROOT_DEV_ID=$(stat -c '%d' /)

is_persistent_mount() {
    target_path="$1"

    # Stat the path and get its Device ID
    current_dev_id=$(stat -c '%d' "${target_path}")

    # If the Device ID of the target is *different* from the root's Device ID,
    # it means it resides on a separate filesystem, implying a mount.
    if [ "${current_dev_id}" != "${ROOT_DEV_ID}" ]; then
        return 0 # Persistent (different filesystem/device ID)
    fi

    # Fallback to check if it's the root directory itself (which is always mounted)
    if [ "${target_path}" = "/" ]; then
        return 0
    fi

    # Check parent directory recursively
    parent_dir=$(dirname "${target_path}")
    if [ "${parent_dir}" != "${target_path}" ]; then
        is_persistent_mount "${parent_dir}"
        return $?
    fi

    return 1 # Not persistent
}

warn_if_not_persistent_mount() {
    path="$1"

    if is_persistent_mount "${path}"; then
        return 0
    fi

    # ... (Your existing warning message block remains unchanged) ...

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