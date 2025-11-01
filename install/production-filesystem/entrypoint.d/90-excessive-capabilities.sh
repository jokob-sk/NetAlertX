#!/bin/bash
# excessive-capabilities.sh checks that no more than the necessary
# NET_ADMIN NET_BIND_SERVICE and NET_RAW capabilities are present.

# Get bounding capabilities from /proc/self/status (what can be acquired)
BND_HEX=$(grep '^CapBnd:' /proc/self/status | awk '{print $2}' | tr -d '\t')

# Convert hex to decimal
BND_DEC=$(( 16#$BND_HEX ))

# Allowed capabilities: NET_BIND_SERVICE (10), NET_ADMIN (12), NET_RAW (13)
ALLOWED_DEC=$(( ( 1 << 10 )  | ( 1 << 12 ) | ( 1 << 13 ) ))

# Check for excessive capabilities (any bits set outside allowed)
EXTRA=$(( BND_DEC & ~ALLOWED_DEC ))

if [ "$EXTRA" -ne 0 ]; then
    cat <<EOF
══════════════════════════════════════════════════════════════════════════════
⚠️  Warning: Excessive capabilities detected (bounding caps: 0x$BND_HEX).

    Only NET_ADMIN, NET_BIND_SERVICE, and NET_RAW are required in this container.
    Please remove unnecessary capabilities.

    https://github.com/jokob-sk/NetAlertX/blob/main/docs/docker-troubleshooting/excessive-capabilities.md
══════════════════════════════════════════════════════════════════════════════
EOF
fi
