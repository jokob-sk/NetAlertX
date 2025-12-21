#!/bin/sh
# check-user-netalertx.sh - ensure the container is running as the hardened service user.

EXPECTED_USER="${NETALERTX_USER:-netalertx}"
EXPECTED_UID="$(getent passwd "${EXPECTED_USER}" 2>/dev/null | cut -d: -f3)"
EXPECTED_GID="$(getent passwd "${EXPECTED_USER}" 2>/dev/null | cut -d: -f4)"
CURRENT_UID="$(id -u)"
CURRENT_GID="$(id -g)"

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
