#!/bin/sh
# 02-ensure-folders.sh - ensure /config and /db exist under /data

set -eu

YELLOW=$(printf '\033[1;33m')
CYAN=$(printf '\033[1;36m')
RED=$(printf '\033[1;31m')
RESET=$(printf '\033[0m')

DATA_DIR=${NETALERTX_DATA:-/data}
TARGET_CONFIG=${NETALERTX_CONFIG:-${DATA_DIR}/config}
TARGET_DB=${NETALERTX_DB:-${DATA_DIR}/db}

ensure_folder() {
    my_path="$1"
    if [ ! -d "${my_path}" ]; then
        >&2 printf "%s" "${CYAN}"
        >&2 echo "Creating missing folder: ${my_path}"
        >&2 printf "%s" "${RESET}"
        mkdir -p "${my_path}" || {
            >&2 printf "%s" "${RED}"
            >&2 echo "❌ Failed to create folder: ${my_path}"
            >&2 printf "%s" "${RESET}"
            exit 1
        }
        chmod 700 "${my_path}" 2>/dev/null || true
    fi
}

# Ensure subfolders exist
ensure_folder "${TARGET_CONFIG}"
ensure_folder "${TARGET_DB}"

>&2 printf "%s" "${CYAN}"
>&2 echo "✅ All required folders are present under ${DATA_DIR}."
>&2 printf "%s" "${RESET}"

exit 0
