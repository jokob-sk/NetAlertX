#!/bin/sh
# layer-2-network.sh - Uses a real nmap command to detect missing container
# privileges and warns the user. It is silent on success.

# Run a fast nmap command that requires raw sockets, capturing only stderr.
ERROR_OUTPUT=$(nmap --privileged -sS -p 20211 127.0.0.1 2>&1)
EXIT_CODE=$?

# Flag common capability errors regardless of exact exit code.
if [ "$EXIT_CODE" -ne 0 ] && \
    echo "$ERROR_OUTPUT" | grep -q -e "Operation not permitted" -e "requires root privileges"
then
    YELLOW=$(printf '\033[1;33m')
    RESET=$(printf '\033[0m')
    >&2 printf "%s" "${YELLOW}"
    >&2 cat <<'EOF'
══════════════════════════════════════════════════════════════════════════════
⚠️  ATTENTION: Raw network capabilities are missing.

    Tools that rely on NET_RAW/NET_ADMIN/NET_BIND_SERVICE (e.g. nmap -sS,
    arp-scan, nbtscan) will not function. Restart the container with:

        --cap-add=NET_RAW --cap-add=NET_ADMIN --cap-add=NET_BIND_SERVICE

    Without those caps, NetAlertX cannot inspect your network. Fix it before
    trusting any results.

    https://github.com/jokob-sk/NetAlertX/blob/main/docs/docker-troubleshooting/missing-capabilities.md
══════════════════════════════════════════════════════════════════════════════
EOF
    >&2 printf "%s" "${RESET}"
fi
exit 0  # Always exit success even after warnings