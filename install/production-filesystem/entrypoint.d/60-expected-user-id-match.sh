#!/bin/sh
# expected-user-id-match.sh - ensure the container is running as the intended runtime UID/GID.

EXPECTED_USER="${NETALERTX_USER:-netalertx}"
CURRENT_UID="$(id -u)"
CURRENT_GID="$(id -g)"

# If PUID/PGID explicitly set, require that we are running as them.
if [ -n "${PUID:-}" ] || [ -n "${PGID:-}" ]; then
    TARGET_UID="${PUID:-${CURRENT_UID}}"
    TARGET_GID="${PGID:-${CURRENT_GID}}"

    if [ "${CURRENT_UID}" -ne "${TARGET_UID}" ] || [ "${CURRENT_GID}" -ne "${TARGET_GID}" ]; then
        if [ "${NETALERTX_PRIVDROP_FAILED:-0}" -ne 0 ]; then
            >&2 printf 'Note: PUID/PGID=%s:%s requested but privilege drop failed; continuing as UID %s GID %s. See docs/docker-troubleshooting/missing-capabilities.md\n' \
                "${TARGET_UID}" "${TARGET_GID}" "${CURRENT_UID}" "${CURRENT_GID}"
            exit 0
        fi
        if [ "${CURRENT_UID}" -ne 0 ]; then
            >&2 printf 'Note: PUID/PGID=%s:%s requested but container is running as fixed UID %s GID %s; PUID/PGID will not be applied.\n' \
                "${TARGET_UID}" "${TARGET_GID}" "${CURRENT_UID}" "${CURRENT_GID}"
            exit 0
        fi

        >&2 printf 'FATAL: NetAlertX running as UID %s GID %s, expected PUID/PGID %s:%s\n' \
            "${CURRENT_UID}" "${CURRENT_GID}" "${TARGET_UID}" "${TARGET_GID}"
        exit 1
    fi
    exit 0
fi

EXPECTED_UID="$(getent passwd "${EXPECTED_USER}" 2>/dev/null | cut -d: -f3)"
EXPECTED_GID="$(getent passwd "${EXPECTED_USER}" 2>/dev/null | cut -d: -f4)"

# Fallback to known defaults when lookups fail
if [ -z "${EXPECTED_UID}" ]; then
    EXPECTED_UID="${CURRENT_UID}"
fi
if [ -z "${EXPECTED_GID}" ]; then
    EXPECTED_GID="${CURRENT_GID}"
fi

if [ "${CURRENT_UID}" -eq "${EXPECTED_UID}" ] && [ "${CURRENT_GID}" -eq "${EXPECTED_GID}" ]; then
    exit 0
fi
>&2 printf '\nNetAlertX note: current UID %s GID %s, expected UID %s GID %s\n' \
    "${CURRENT_UID}" "${CURRENT_GID}" "${EXPECTED_UID}" "${EXPECTED_GID}"
exit 0
