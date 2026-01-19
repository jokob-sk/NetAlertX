#!/bin/sh
# 10-capabilities-audit.sh - Inspects the container bounding set for required privileges.
#
# This script runs early to detect missing capabilities that would cause later
# scripts (like Python-based checks) to fail with "Operation not permitted".
# This is not for checking excessive capabilities, which is handled in another
# startup script.


RED=$(printf '\033[1;31m')
YELLOW=$(printf '\033[1;33m')
GREY=$(printf '\033[90m')
RESET=$(printf '\033[0m')

_detect_storage_driver() {
    mounts_path="/proc/mounts"

    if [ -n "${NETALERTX_PROC_MOUNTS_B64:-}" ]; then
        mounts_override="/tmp/netalertx_proc_mounts_inline_capcheck"
        if printf '%s' "${NETALERTX_PROC_MOUNTS_B64}" | base64 -d > "${mounts_override}" 2>/dev/null; then
            chmod 600 "${mounts_override}" 2>/dev/null || true
            mounts_path="${mounts_override}"
        fi
    elif [ -n "${NETALERTX_PROC_MOUNTS_OVERRIDE:-}" ]; then
        mounts_path="${NETALERTX_PROC_MOUNTS_OVERRIDE}"
    fi

    if [ ! -r "${mounts_path}" ]; then
        echo "other"
        return
    fi

    if grep -qE '^[^ ]+ / aufs ' "${mounts_path}" 2>/dev/null; then
        echo "aufs"
    else
        echo "other"
    fi
}

# Parse Bounding Set from /proc/self/status
cap_bnd_hex=$(awk '/CapBnd/ {print $2}' /proc/self/status 2>/dev/null || echo "0")
# Convert hex to dec (POSIX compliant)
cap_bnd_dec=$(awk -v hex="$cap_bnd_hex" 'BEGIN { h = "0x" hex; if (h ~ /^0x[0-9A-Fa-f]+$/) { printf "%d", h } else { print 0 } }')

has_cap() {
    bit=$1
    # Check if bit is set in cap_bnd_dec
    [ $(( (cap_bnd_dec >> bit) & 1 )) -eq 1 ]
}

# 1. ALERT: Python Requirements (NET_RAW=13, NET_ADMIN=12)
if ! has_cap 13 || ! has_cap 12; then
    printf "%s" "${RED}"
    cat <<'EOF'
══════════════════════════════════════════════════════════════════════════════
🚨 ALERT: Python execution capabilities (NET_RAW/NET_ADMIN) are missing.

    The Python binary in this image has file capabilities (+eip) that
    require these bits in the container's bounding set. Without them,
    the binary will fail to execute (Operation not permitted).

    Restart with: --cap-add=NET_RAW --cap-add=NET_ADMIN
══════════════════════════════════════════════════════════════════════════════
EOF
    printf "%s" "${RESET}"
fi

# 2. WARNING: NET_BIND_SERVICE (10)
if ! has_cap 10; then
    printf "%s" "${YELLOW}"
    cat <<'EOF'
══════════════════════════════════════════════════════════════════════════════
⚠️  WARNING: Reduced functionality (NET_BIND_SERVICE missing).

    Tools like nbtscan cannot bind to privileged ports (UDP 137).
    This will reduce discovery accuracy for legacy devices.

    Consider adding: --cap-add=NET_BIND_SERVICE
══════════════════════════════════════════════════════════════════════════════
EOF
    printf "%s" "${RESET}"
fi

# 3. NOTE: Security Context (CHOWN=0, SETGID=6, SETUID=7)
missing_admin=""
has_cap 0 || missing_admin="${missing_admin} CHOWN"
has_cap 6 || missing_admin="${missing_admin} SETGID"
has_cap 7 || missing_admin="${missing_admin} SETUID"

if [ -n "${missing_admin}" ]; then
    printf "%sSecurity context: Operational capabilities (%s) not granted.%s\n" "${GREY}" "${missing_admin# }" "${RESET}"
    if echo "${missing_admin}" | grep -q "CHOWN"; then
        printf "%sSee https://docs.netalertx.com/docker-troubleshooting/missing-capabilities%s\n" "${GREY}" "${RESET}"
    fi
fi

storage_driver=$(_detect_storage_driver)
runtime_uid=$(id -u 2>/dev/null || echo 0)

if [ "${storage_driver}" = "aufs" ] && [ "${runtime_uid}" -ne 0 ]; then
    printf "%s" "${YELLOW}"
    cat <<'EOF'
══════════════════════════════════════════════════════════════════════════════
⚠️  WARNING: Reduced functionality (AUFS + non-root user).

    AUFS strips Linux file capabilities, so tools like arp-scan, nmap, and
    nbtscan fail when NetAlertX runs as a non-root PUID.

    Set PUID=0 on AUFS hosts for full functionality:
    https://docs.netalertx.com/docker-troubleshooting/aufs-capabilities
══════════════════════════════════════════════════════════════════════════════
EOF
    printf "%s" "${RESET}"
fi

exit 0
