#!/bin/sh
# 01-data-migration.sh - consolidate legacy /app mounts into /data

set -eu

YELLOW=$(printf '\033[1;33m')
CYAN=$(printf '\033[1;36m')
RED=$(printf '\033[1;31m')
RESET=$(printf '\033[0m')

DATA_DIR=${NETALERTX_DATA:-/data}
TARGET_CONFIG=${NETALERTX_CONFIG:-${DATA_DIR}/config}
TARGET_DB=${NETALERTX_DB:-${DATA_DIR}/db}
LEGACY_CONFIG=/app/config
LEGACY_DB=/app/db
MARKER_NAME=.migration

is_mounted() {
    local path="$1"
    if [ ! -d "${path}" ]; then
        return 1
    fi
    mountpoint -q "${path}" 2>/dev/null
}

warn_unmount_legacy() {
    >&2 printf "%s" "${YELLOW}"
    >&2 cat <<EOF
══════════════════════════════════════════════════════════════════════════════
⚠️  ATTENTION: Legacy mounts detected at ${LEGACY_CONFIG} or ${LEGACY_DB}.

    Migration markers are present. Your data now lives under ${DATA_DIR}.
    Unmount the legacy /app/config and /app/db paths from your docker-compose
    file to avoid stale mounts on future starts.
══════════════════════════════════════════════════════════════════════════════
EOF
    >&2 printf "%s" "${RESET}"
}

fatal_missing_data_mount() {
    >&2 printf "%s" "${RED}"
    >&2 cat <<EOF
══════════════════════════════════════════════════════════════════════════════
❌ CRITICAL: /data is not mounted but legacy mounts are still present.

    Mount the new consolidated volume at ${DATA_DIR} so data can be migrated.
    Once mounted, restart the container to complete migration automatically.
══════════════════════════════════════════════════════════════════════════════
EOF
    >&2 printf "%s" "${RESET}"
}

migrate_legacy_mounts() {
    >&2 printf "%s" "${CYAN}"
    >&2 cat <<EOF
══════════════════════════════════════════════════════════════════════════════
🛠️  Migrating legacy /app mounts into ${DATA_DIR}.

    Existing configuration and database files will be copied into the new
    consolidated volume. This runs once per environment.
══════════════════════════════════════════════════════════════════════════════
EOF
    >&2 printf "%s" "${RESET}"

    mkdir -p "${TARGET_CONFIG}" "${TARGET_DB}" || return 1
    chmod 700 "${TARGET_CONFIG}" "${TARGET_DB}" 2>/dev/null || true

    if ! cp -a "${LEGACY_CONFIG}/." "${TARGET_CONFIG}/"; then
        >&2 printf "%s" "${RED}"
        >&2 echo "Migration failed while copying configuration files."
        >&2 printf "%s" "${RESET}"
        return 1
    fi

    if ! cp -a "${LEGACY_DB}/." "${TARGET_DB}/"; then
        >&2 printf "%s" "${RED}"
        >&2 echo "Migration failed while copying database files."
        >&2 printf "%s" "${RESET}"
        return 1
    fi

    touch "${LEGACY_CONFIG}/${MARKER_NAME}" "${LEGACY_DB}/${MARKER_NAME}" 2>/dev/null || true

    warn_unmount_legacy
    return 0
}

CONFIG_MARKED=false
DB_MARKED=false
[ -f "${LEGACY_CONFIG}/${MARKER_NAME}" ] && CONFIG_MARKED=true
[ -f "${LEGACY_DB}/${MARKER_NAME}" ] && DB_MARKED=true

if ${CONFIG_MARKED} || ${DB_MARKED}; then
    warn_unmount_legacy
    exit 0
fi

CONFIG_MOUNTED=false
DB_MOUNTED=false
DATA_MOUNTED=false
is_mounted "${LEGACY_CONFIG}" && CONFIG_MOUNTED=true
is_mounted "${LEGACY_DB}" && DB_MOUNTED=true
is_mounted "${DATA_DIR}" && DATA_MOUNTED=true

# Nothing to migrate if legacy mounts are absent
if ! ${CONFIG_MOUNTED} && ! ${DB_MOUNTED}; then
    exit 0
fi

# Partial legacy mount state, notify and exit
if ${CONFIG_MOUNTED} && ! ${DB_MOUNTED}; then
    >&2 printf "%s" "${YELLOW}"
    >&2 cat <<EOF
══════════════════════════════════════════════════════════════════════════════
⚠️  ATTENTION: /app/config is still mounted but /app/db is not.

    Mount both legacy paths alongside ${DATA_DIR} to migrate automatically,
    or unmount /app/config entirely.
══════════════════════════════════════════════════════════════════════════════
EOF
    >&2 printf "%s" "${RESET}"
    exit 0
fi

if ${DB_MOUNTED} && ! ${CONFIG_MOUNTED}; then
    >&2 printf "%s" "${YELLOW}"
    >&2 cat <<EOF
══════════════════════════════════════════════════════════════════════════════
⚠️  ATTENTION: /app/db is still mounted but /app/config is not.

    Mount both legacy paths alongside ${DATA_DIR} to migrate automatically,
    or unmount /app/db entirely.
══════════════════════════════════════════════════════════════════════════════
EOF
    >&2 printf "%s" "${RESET}"
    exit 0
fi

if ! ${DATA_MOUNTED}; then
    fatal_missing_data_mount
    exit 1
fi

migrate_legacy_mounts || exit 1
exit 0
