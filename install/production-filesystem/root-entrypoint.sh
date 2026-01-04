#!/bin/bash
# NetAlertX Root-Priming Entrypoint — best-effort permission priming 🔧
#
# Purpose:
# - Provide a runtime, best-effort remedy for host volume ownership/mode issues
#   (common on appliances like Synology where Docker volume copy‑up is limited).
# - Ensure writable paths exist, attempt to `chown`/`chmod` to a runtime `PUID`/`PGID`
#   (defaults to 20211), then drop privileges via `su-exec` if possible.
#
# Design & behavior notes:
# - This script is intentionally *non-fatal* for chown/chmod failures; operations are
#   best-effort so we avoid blocking container startup on imperfect hosts.
# - Runtime defaults are used so the image works without requiring build-time args.
# - If the container is started as non-root (`user:`), priming is skipped and it's the
#   operator's responsibility to ensure matching ownership on the host.
# - If `su-exec` cannot drop privileges, we log a note and continue as the current user
#   rather than aborting (keeps first-run resilient).
#
# Operational recommendation:
# - For deterministic ownership, explicitly set `PUID`/`PGID` (or pre-chown host volumes),
#   and when hardening capabilities add `cap_add: [CHOWN]` so priming can succeed.

PUID="${PUID:-${NETALERTX_UID:-20211}}"
PGID="${PGID:-${NETALERTX_GID:-20211}}"

# Pretty terminal colors used for fatal messages (kept minimal + POSIX printf)
RED=$(printf '\033[1;31m')
RESET=$(printf '\033[0m')


_validate_id() {
    value="$1"
    name="$2"

    if ! printf '%s' "${value}" | grep -qxE '[0-9]+'; then
        >&2 printf "%s" "${RED}"
        >&2 cat <<EOF
══════════════════════════════════════════════════════════════════════════════
🔒 SECURITY - FATAL: invalid ${name} value (non-numeric)

    Startup halted because the provided ${name} environmental variable 
	contains non-digit characters. This is a deliberate security measure to
	prevent environment-variable command injection while the container runs as
	root during initial startup.

    Action: set a numeric ${name} (for example: PUID=1000) in your environment 
	or docker-compose file and restart the container. Default: 20211.

    For more information and troubleshooting, see:
    https://github.com/jokob-sk/NetAlertX/blob/main/docs/docker-troubleshooting/PUID_PGID_SECURITY.md
══════════════════════════════════════════════════════════════════════════════
EOF
        >&2 printf "%s" "${RESET}"
        exit 1
    fi
}

_validate_id "${PUID}" "PUID"
_validate_id "${PGID}" "PGID"

_cap_bits_warn_missing_setid() {
    cap_hex=$(awk '/CapEff/ {print $2}' /proc/self/status 2>/dev/null || echo "")
    [ -n "${cap_hex}" ] || return

    # POSIX compliant base16 on permissions
    cap_dec=$(awk 'BEGIN { h = "0x'"${cap_hex}"'"; if (h ~ /^0x[0-9A-Fa-f]+$/) { printf "%d", h } else { print 0 } }')

    has_setgid=0
    has_setuid=0
    has_net_caps=0

    if [ $((cap_dec & (1 << 6))) -ne 0 ]; then
        has_setgid=1
    fi
    if [ $((cap_dec & (1 << 7))) -ne 0 ]; then
        has_setuid=1
    fi
    if [ $((cap_dec & (1 << 10))) -ne 0 ] || [ $((cap_dec & (1 << 12))) -ne 0 ] || [ $((cap_dec & (1 << 13))) -ne 0 ]; then
        has_net_caps=1
    fi

    if [ "${has_net_caps}" -eq 1 ] && { [ "${has_setgid}" -eq 0 ] || [ "${has_setuid}" -eq 0 ]; }; then
        >&2 echo "Note: CAP_SETUID/CAP_SETGID unavailable alongside NET_* caps; continuing as current user."
    fi
}

_cap_bits_warn_missing_setid

if [ "$(id -u)" -ne 0 ]; then
    if [ -n "${PUID:-}" ] || [ -n "${PGID:-}" ]; then
        >&2 printf 'Note: container running as UID %s GID %s; requested PUID/PGID=%s:%s will not be applied.\n' \
            "$(id -u)" "$(id -g)" "${PUID}" "${PGID}"
    fi
    exec /entrypoint.sh "$@"
fi

if [ "${PUID}" -eq 0 ]; then
    >&2 echo "WARNING: Running as root (PUID=0). Prefer a non-root PUID. See https://github.com/jokob-sk/NetAlertX/blob/main/docs/docker-troubleshooting/file-permissions.md"
    exec /entrypoint.sh "$@"
fi

_prime_paths() {
    runtime_root="${NETALERTX_RUNTIME_BASE:-/tmp}"
    paths="/tmp ${NETALERTX_DATA:-/data} ${NETALERTX_CONFIG:-/data/config} ${NETALERTX_DB:-/data/db} ${NETALERTX_LOG:-${runtime_root}/log} ${NETALERTX_PLUGINS_LOG:-${runtime_root}/log/plugins} ${NETALERTX_API:-${runtime_root}/api} ${SYSTEM_SERVICES_RUN:-${runtime_root}/run} ${SYSTEM_SERVICES_RUN_TMP:-${runtime_root}/run/tmp} ${SYSTEM_SERVICES_RUN_LOG:-${runtime_root}/run/logs} ${SYSTEM_SERVICES_ACTIVE_CONFIG:-${runtime_root}/nginx/active-config} ${runtime_root}/nginx"

    chmod 1777 /tmp 2>/dev/null || true

    for path in ${paths}; do
        [ -n "${path}" ] || continue
        if [ "${path}" = "/tmp" ]; then
            continue
        fi
        install -d -o "${PUID}" -g "${PGID}" -m 700 "${path}" 2>/dev/null || true
        chown -R "${PUID}:${PGID}" "${path}" 2>/dev/null || true
        chmod -R u+rwX "${path}" 2>/dev/null || true
    done

    >&2 echo "Permissions prepared for PUID=${PUID}."
}

_prime_paths

unset NETALERTX_PRIVDROP_FAILED
if ! su-exec "${PUID}:${PGID}" /entrypoint.sh "$@"; then
    rc=$?
    export NETALERTX_PRIVDROP_FAILED=1
    export NETALERTX_CHECK_ONLY="${NETALERTX_CHECK_ONLY:-1}"
    >&2 echo "Note: su-exec failed (exit ${rc}); continuing as current user without privilege drop."
    exec /entrypoint.sh "$@"
fi