#!/bin/bash
# NetAlertX Root-Priming Entrypoint — best-effort permission priming 🔧
#
# Responsibilities:
# - Provide a runtime, best-effort remedy for host volume ownership/mode issues
#   (common on appliances like Synology where Docker volume copy‑up is limited).
# - Ensure writable paths exist, attempt to `chown` to a runtime `PUID`/`PGID`
#   (defaults to 20211), then drop privileges via `su-exec` if possible.
#
# Design & behavior notes:
# - This script is intentionally *non-fatal* for chown failures; operations are
#   best-effort so we avoid blocking container startup on imperfect hosts.
# - Runtime defaults are used so the image works without requiring build-time args.
# - If the container is started as non-root (`user:`), priming is skipped and it's the
#   operator's responsibility to ensure matching ownership on the host.
# - If `su-exec` cannot drop privileges, we log a note and continue as the current user
#   rather than aborting (keeps first-run resilient).
#
# Behavioral conditions:
# 1. RUNTIME: NON-ROOT (Container started as user: 1000)
#    - PUID/PGID env vars are ignored (cannot switch users).
#    - Write permissions check performed on /data and /tmp.
#    - EXEC: Direct entrypoint execution as current user.
#
# 2. RUNTIME: ROOT (Container started as user: 0)
#    - PRIMING: Always ensure paths exist and chown to requested PUID:PGID
#      (defaults to 20211). Failures are logged but non-fatal to support
#      NFS/ReadOnly mounts.
#    - EXEC: Attempt `su-exec PUID:PGID` (including 0:0) to keep a single
#      execution path. On failure (missing caps/tool), log and run as root.
#    - If PUID=0, warn operators that processes remain root-owned.

PROC_MOUNTS_PATH="/proc/mounts"
PROC_MOUNTS_OVERRIDE_REASON=""

if [ -n "${NETALERTX_PROC_MOUNTS_B64:-}" ]; then
    PROC_MOUNTS_INLINE_PATH="/tmp/netalertx_proc_mounts_inline"
    if printf '%s' "${NETALERTX_PROC_MOUNTS_B64}" | base64 -d > "${PROC_MOUNTS_INLINE_PATH}" 2>/dev/null; then
        chmod 600 "${PROC_MOUNTS_INLINE_PATH}" 2>/dev/null || true
        PROC_MOUNTS_PATH="${PROC_MOUNTS_INLINE_PATH}"
        PROC_MOUNTS_OVERRIDE_REASON="inline"
    else
        >&2 printf 'Warning: Failed to decode NETALERTX_PROC_MOUNTS_B64; continuing with %s.\n' "${PROC_MOUNTS_PATH}"
    fi
elif [ -n "${NETALERTX_PROC_MOUNTS_OVERRIDE:-}" ]; then
    PROC_MOUNTS_PATH="${NETALERTX_PROC_MOUNTS_OVERRIDE}"
    PROC_MOUNTS_OVERRIDE_REASON="file"
fi

if [ "${PROC_MOUNTS_OVERRIDE_REASON}" = "inline" ]; then
    >&2 echo "Note: Using inline /proc/mounts override for storage-driver detection."
elif [ "${PROC_MOUNTS_PATH}" != "/proc/mounts" ]; then
    >&2 printf 'Note: Using override for /proc/mounts at %s\n' "${PROC_MOUNTS_PATH}"
fi

# Detect AUFS storage driver; emit warnings so operators can take corrective action
_detect_storage_driver() {
    local mounts_path="${PROC_MOUNTS_PATH}"
    if [ ! -r "${mounts_path}" ]; then
        >&2 printf 'Note: Unable to read %s; assuming non-AUFS storage.\n' "${mounts_path}"
        echo "other"
        return
    fi
    # Check mounts file to detect if root filesystem uses aufs
    if grep -qE '^[^ ]+ / aufs ' "${mounts_path}" 2>/dev/null; then
        echo "aufs"
    else
        echo "other"
    fi
}

STORAGE_DRIVER="$(_detect_storage_driver)"
PUID="${PUID:-${NETALERTX_UID:-20211}}"
PGID="${PGID:-${NETALERTX_GID:-20211}}"

if [ "${STORAGE_DRIVER}" = "aufs" ]; then
    >&2 cat <<'EOF'
⚠️  WARNING: Legacy AUFS storage driver detected.
    AUFS strips file capabilities (setcap) during image extraction which breaks
    layer-2 scanners (arp-scan, etc.) when running as non-root.
    Action: set PUID=0 (root) on AUFS hosts or migrate to a supported driver.
    Details: https://docs.netalertx.com/docker-troubleshooting/aufs-capabilities
EOF
fi

RED=$(printf '\033[1;31m')
RESET=$(printf '\033[0m')

_error_msg() {
    title="$1"
    body="$2"
    >&2 printf "%s" "${RED}"
    >&2 cat <<EOF
══════════════════════════════════════════════════════════════════════════════
🔒 SECURITY - FATAL: ${title}

${body}

══════════════════════════════════════════════════════════════════════════════
EOF
    >&2 printf "%s" "${RESET}"

}

_validate_id() {
    value="$1"
    name="$2"
    if ! printf '%s' "${value}" | grep -qxE '[0-9]+'; then
        _error_msg "INVALID ${name} VALUE (non-numeric)" \
    "    Startup halted because the provided ${name} environmental variable
    contains non-digit characters.

    Action: set a numeric ${name} (for example: ${name}=1000) in your environment
    or docker-compose file. Default: 20211."
	    exit 1
    fi
}

_validate_id "${PUID}" "PUID"
_validate_id "${PGID}" "PGID"

_cap_bits_warn_missing_setid() {
    cap_hex=$(awk '/CapEff/ {print $2}' /proc/self/status 2>/dev/null || echo "")
    [ -n "${cap_hex}" ] || return
    cap_dec=$((0x${cap_hex}))

    has_setgid=0; has_setuid=0; has_net_caps=0

    # Bit masks (use numeric constants to avoid editor/HL issues and improve clarity)
    # 1 << 6  = 64
    # 1 << 7  = 128
    # (1<<10)|(1<<12)|(1<<13) = 1024 + 4096 + 8192 = 13312
    SETGID_MASK=64
    SETUID_MASK=128
    NET_MASK=13312

    if (( cap_dec & SETGID_MASK )); then
        has_setgid=1
    fi
    if (( cap_dec & SETUID_MASK )); then
        has_setuid=1
    fi
    if (( cap_dec & NET_MASK )); then
        has_net_caps=1
    fi

    if (( has_net_caps == 1 && ( has_setgid == 0 || has_setuid == 0 ) )); then
        >&2 echo "Note: CAP_SETUID/CAP_SETGID unavailable alongside NET_* caps; continuing as current user."
    fi
}

_cap_bits_warn_missing_setid

if [ "$(id -u)" -ne 0 ]; then
    for path in "/tmp" "${NETALERTX_DATA:-/data}"; do
        if [ -n "$path" ] && [ ! -w "$path" ]; then
            _error_msg "FILESYSTEM PERMISSIONS ERROR" \
    "    Container is running as User $(id -u), but cannot write to:
    ${path}

    Because the container is not running as root, it cannot fix these
    permissions automatically.

    Action:
    1. Update Host Volume permissions (e.g. 'chmod 755 ${path}' on host).
    2. Or, run container as root (user: 0) and let PUID/PGID logic handle it."
        fi
    done

    if [ -n "${PUID:-}" ] && [ "${PUID}" != "$(id -u)" ]; then
        >&2 printf 'Note: container running as UID %s; requested PUID=%s ignored.\n' "$(id -u)" "${PUID}"
    fi
    exec /entrypoint.sh "$@"
fi

_prime_paths() {
    runtime_root="${NETALERTX_RUNTIME_BASE:-/tmp}"
    paths="/tmp ${NETALERTX_DATA:-/data} ${NETALERTX_CONFIG:-/data/config} ${NETALERTX_DB:-/data/db} ${NETALERTX_LOG:-${runtime_root}/log} ${NETALERTX_PLUGINS_LOG:-${runtime_root}/log/plugins} ${NETALERTX_API:-${runtime_root}/api} ${SYSTEM_SERVICES_RUN:-${runtime_root}/run} ${SYSTEM_SERVICES_RUN_TMP:-${runtime_root}/run/tmp} ${SYSTEM_SERVICES_RUN_LOG:-${runtime_root}/run/logs} ${SYSTEM_SERVICES_ACTIVE_CONFIG:-${runtime_root}/nginx/active-config} ${runtime_root}/nginx"

    # Always chown core roots up front so non-root runtime can chmod later.
    chown -R "${PUID}:${PGID}" /data 2>/dev/null || true
    chown -R "${PUID}:${PGID}" /tmp 2>/dev/null || true

    for path in ${paths}; do
        [ -n "${path}" ] || continue
        if [ "${path}" = "/tmp" ]; then continue; fi
        install -d -o "${PUID}" -g "${PGID}" "${path}" 2>/dev/null || true
        chown -R "${PUID}:${PGID}" "${path}" 2>/dev/null || true
        # Note: chown must be done by root, chmod can be done by non-root
        # (chmod removed as non-root runtime will handle modes after ownership is set)
    done
}
_prime_paths

if [ "${PUID}" -eq 0 ]; then
    >&2 echo "ℹ️  Running as root (PUID=0). Paths will be owned by root."
fi

unset NETALERTX_PRIVDROP_FAILED
if ! su-exec "${PUID}:${PGID}" /entrypoint.sh "$@"; then
    rc=$?
    export NETALERTX_PRIVDROP_FAILED=1
    export NETALERTX_CHECK_ONLY="${NETALERTX_CHECK_ONLY:-0}"
    >&2 echo "Note: su-exec failed (exit ${rc}); continuing as current user without privilege drop."
    exec /entrypoint.sh "$@"
fi