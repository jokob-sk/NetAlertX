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
        printf "%sSee https://github.com/jokob-sk/NetAlertX/blob/main/docs/docker-troubleshooting/missing-capabilities.md%s\n" "${GREY}" "${RESET}"
    fi
fi

exit 0
