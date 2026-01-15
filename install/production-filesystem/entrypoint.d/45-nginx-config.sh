#!/bin/sh
# check-nginx-config.sh - verify nginx conf.active mount is writable when PORT != 20211.


# Only check nginx config writability if PORT is not the default 20211
if [ "${PORT:-20211}" = "20211" ]; then
    exit 0
fi

CONF_ACTIVE_DIR="${SYSTEM_SERVICES_ACTIVE_CONFIG}"
TARGET_FILE="${CONF_ACTIVE_DIR}/netalertx.conf"

# If the directory is missing entirely we warn and exit 0 to allow startup with defaults.
if [ ! -d "${CONF_ACTIVE_DIR}" ]; then
    YELLOW=$(printf '\033[1;33m')
    RESET=$(printf '\033[0m')
    >&2 printf "%s" "${YELLOW}"
    >&2 cat <<EOF
══════════════════════════════════════════════════════════════════════════════
⚠️  ATTENTION: Nginx configuration mount ${CONF_ACTIVE_DIR} is missing.

    Custom listen address or port changes require a writable nginx conf.active
    directory. Without it, the container falls back to defaults and ignores
    your overrides.

    Create a bind mount:
        --mount type=bind,src=/path/on/host,dst=${CONF_ACTIVE_DIR}
    and ensure it is owned by the netalertx user (20211:20211) with 700 perms.

    https://docs.netalertx.com/docker-troubleshooting/nginx-configuration-mount
══════════════════════════════════════════════════════════════════════════════
EOF
    >&2 printf "%s" "${RESET}"
    exit 0
fi

TMP_FILE="${CONF_ACTIVE_DIR}/.netalertx-write-test"
if ! ( : >"${TMP_FILE}" ) 2>/dev/null; then
    YELLOW=$(printf '\033[1;33m')
    RESET=$(printf '\033[0m')
    >&2 printf "%s" "${YELLOW}"
    >&2 cat <<EOF
══════════════════════════════════════════════════════════════════════════════
⚠️  ATTENTION: Unable to write to ${TARGET_FILE}.

    Ensure the conf.active mount is writable by the netalertx user before
    changing LISTEN_ADDR or PORT. Fix permissions:
        chown -R 20211:20211 ${CONF_ACTIVE_DIR}
        find ${CONF_ACTIVE_DIR} -type d -exec chmod 700 {} +
        find ${CONF_ACTIVE_DIR} -type f -exec chmod 600 {} +

    https://docs.netalertx.com/docker-troubleshooting/nginx-configuration-mount
══════════════════════════════════════════════════════════════════════════════
EOF
    >&2 printf "%s" "${RESET}"
    exit 0 # Nginx can continue using default config on port 20211
fi
rm -f "${TMP_FILE}"

exit 0
