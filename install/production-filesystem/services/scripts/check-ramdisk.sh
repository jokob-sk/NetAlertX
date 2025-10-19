#!/bin/sh
# storage-check.sh - Verify critical paths use dedicated mounts.

warn_if_not_dedicated_mount() {
    path="$1"
    if awk -v target="${path}" '$5 == target {found=1} END {exit found ? 0 : 1}' /proc/self/mountinfo; then
        return 0
    fi

    failures=1
    YELLOW=$(printf '\033[1;33m')
    RESET=$(printf '\033[0m')
    >&2 printf "%s" "${YELLOW}"
    >&2 cat <<EOF
══════════════════════════════════════════════════════════════════════════════
⚠️  ATTENTION: ${path} is not mounted separately inside this container.

    NetAlertX runs as a single unprivileged process and pounds this directory
    with writes. Leaving it on the container overlay will thrash storage and
    slow the stack.

    Fix: mount ${path} explicitly — tmpfs for ephemeral data, or bind/volume if
    you want to preserve history:
        --mount type=tmpfs,destination=${path}
        # or
        --mount type=bind,src=/path/on/host,dst=${path}

    Apply the mount and restart the container.
══════════════════════════════════════════════════════════════════════════════
EOF
    >&2 printf "%s" "${RESET}"
}


# If NETALERTX_DEBUG=1 then we will exit
if [ "${NETALERTX_DEBUG}" = "1" ]; then
	exit 0
fi

failures=0
warn_if_not_dedicated_mount "${NETALERTX_API}"
warn_if_not_dedicated_mount "${NETALERTX_LOG}"

if [ "${failures}" -ne 0 ]; then
    exit 1
fi

if [ ! -f "${SYSTEM_NGINX_CONFIG}/conf.active" ]; then
    echo "Note: Using default listen address ${LISTEN_ADDR}:${PORT} (no ${SYSTEM_NGINX_CONFIG}/conf.active override)."
fi
