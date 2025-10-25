#!/bin/sh
# check-user-netalertx.sh - ensure the container is running as the hardened service user.

EXPECTED_USER="${NETALERTX_USER:-netalertx}"
EXPECTED_UID="$(getent passwd "${EXPECTED_USER}" 2>/dev/null | cut -d: -f3)"
EXPECTED_GID="$(getent passwd "${EXPECTED_USER}" 2>/dev/null | cut -d: -f4)"
CURRENT_UID="$(id -u)"
CURRENT_GID="$(id -g)"

# Fallback to known defaults when lookups fail
if [ -z "${EXPECTED_UID}" ]; then
    EXPECTED_UID="20211"
fi
if [ -z "${EXPECTED_GID}" ]; then
    EXPECTED_GID="20211"
fi

if [ "${CURRENT_UID}" -eq "${EXPECTED_UID}" ] && [ "${CURRENT_GID}" -eq "${EXPECTED_GID}" ]; then
    exit 0
fi

YELLOW=$(printf '\033[1;33m')
RESET=$(printf '\033[0m')
>&2 printf "%s" "${YELLOW}"
>&2 cat <<EOF
══════════════════════════════════════════════════════════════════════════════
⚠️  ATTENTION: NetAlertX is running as UID ${CURRENT_UID}:${CURRENT_GID}.

    Hardened permissions, file ownership, and runtime isolation expect the
    dedicated service account (${EXPECTED_USER} -> ${EXPECTED_UID}:${EXPECTED_GID}).
    When you override the container user (for example, docker run --user 1000:1000
    or a Compose "user:" directive), NetAlertX loses crucial safeguards and
    future upgrades may silently fail.

    Restore the container to the default user:
      * Remove any custom --user flag
      * Delete "user:" overrides in compose files
      * Recreate the container so volume ownership is reset
══════════════════════════════════════════════════════════════════════════════
EOF
>&2 printf "%s" "${RESET}"
sleep 5 # Give user time to read the message
exit 0
