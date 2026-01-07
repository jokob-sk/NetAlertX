#!/bin/sh
# POSIX-compliant shell script for capability checking.
# excessive-capabilities.sh checks that no more than the necessary
# CHOWN SETGID SETUID NET_ADMIN NET_BIND_SERVICE and NET_RAW capabilities are present.


# if we are running in devcontainer then we should exit immediately without checking
# The devcontainer is set up to have additional permissions which are not granted
# in production so this check would always fail there.
if [ "${NETALERTX_DEBUG}" = "1" ]; then
    exit 0
fi

# Get bounding capabilities from /proc/self/status (what can be acquired)
BND_HEX=$(grep '^CapBnd:' /proc/self/status 2>/dev/null | awk '{print $2}' | tr -d '\t')  

if [ -z "$BND_HEX" ]; then
    exit 0
fi

#POSIX compliant base16 on permissions
BND_DEC=$(awk 'BEGIN { h = "0x'"$BND_HEX"'"; if (h ~ /^0x[0-9A-Fa-f]+$/) { printf "%d", h; exit 0 } else { exit 1 } }') || exit 0

# Allowed capabilities: CHOWN (0), SETGID (6), SETUID (7), NET_BIND_SERVICE (10), NET_ADMIN (12), NET_RAW (13)
ALLOWED_DEC=$(( ( 1 << 0 ) | ( 1 << 6 ) | ( 1 << 7 ) | ( 1 << 10 ) | ( 1 << 12 ) | ( 1 << 13 ) ))

# Check for excessive capabilities (any bits set outside allowed)
EXTRA=$(( BND_DEC & ~ALLOWED_DEC ))

if [ "$EXTRA" -ne 0 ]; then
    cat <<EOF
══════════════════════════════════════════════════════════════════════════════
⚠️  Warning: Excessive capabilities detected (bounding caps: 0x$BND_HEX).

    Only CHOWN, SETGID, SETUID, NET_ADMIN, NET_BIND_SERVICE, and NET_RAW are 
    required in this container. Please remove unnecessary capabilities.

    https://github.com/jokob-sk/NetAlertX/blob/main/docs/docker-troubleshooting/excessive-capabilities.md
══════════════════════════════════════════════════════════════════════════════
EOF
fi
