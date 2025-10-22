#!/bin/sh
# check-network-mode.sh - detect when the container is not using host networking.

DEFAULT_IF="$(ip route show default 0.0.0.0/0 2>/dev/null | awk 'NR==1 {print $5}')"
if [ -z "${DEFAULT_IF}" ]; then
    # No default route; nothing to validate.
    exit 0
fi

IF_LINK_INFO="$(ip link show "${DEFAULT_IF}" 2>/dev/null)"
IF_IP="$(ip -4 addr show "${DEFAULT_IF}" 2>/dev/null | awk '/inet / {print $2}' | head -n1)"
IF_MAC=""
if [ -r "/sys/class/net/${DEFAULT_IF}/address" ]; then
    IF_MAC="$(cat "/sys/class/net/${DEFAULT_IF}/address")"
fi

looks_like_bridge="0"

case "${IF_MAC}" in
    02:42:*) looks_like_bridge="1" ;;
    00:00:00:00:00:00) looks_like_bridge="1" ;;
    "") ;; # leave as is
esac

case "${IF_IP}" in
    172.1[6-9].*|172.2[0-9].*|172.3[0-1].*) looks_like_bridge="1" ;;
    192.168.65.*) looks_like_bridge="1" ;;
esac

if echo "${IF_LINK_INFO}" | grep -q "@if"; then
    looks_like_bridge="1"
fi

if [ "${looks_like_bridge}" -ne 1 ]; then
    exit 0
fi

YELLOW=$(printf '\033[1;33m')
RESET=$(printf '\033[0m')
>&2 printf "%s" "${YELLOW}"
>&2 cat <<EOF
══════════════════════════════════════════════════════════════════════════════
⚠️  ATTENTION: NetAlertX is not running with --network=host.

    Bridge networking blocks passive discovery (ARP, NBNS, mDNS) and active
    scanning accuracy. Most plugins expect raw access to the LAN through host
    networking and CAP_NET_RAW capabilities.

    Restart the container with:
        docker run --network=host --cap-add=NET_RAW --cap-add=NET_ADMIN --cap-add=NET_BIND_SERVICE
    or set "network_mode: host" in docker-compose.yml.
══════════════════════════════════════════════════════════════════════════════
EOF
>&2 printf "%s" "${RESET}"
exit 1
