#!/bin/sh
# check-storage-extra.sh - ensure additional NetAlertX directories are persistent mounts.

warn_if_not_persistent_mount() {
    path="$1"
    label="$2"
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

    ${label} relies on host storage to persist data across container restarts.
    Mount this directory from the host or a named volume before trusting the
    container's output.

    Example:
        --mount type=bind,src=/path/on/host,dst=${path}
══════════════════════════════════════════════════════════════════════════════
EOF
    >&2 printf "%s" "${RESET}"
}

failures=0
warn_if_not_persistent_mount "${NETALERTX_LOG}" "Logs"
warn_if_not_persistent_mount "${NETALERTX_API}" "API JSON cache"
warn_if_not_persistent_mount "${SYSTEM_SERVICES_RUN}" "Runtime work directory"

if [ "${failures}" -ne 0 ]; then
    sleep 5
    exit 1
fi

exit 0
