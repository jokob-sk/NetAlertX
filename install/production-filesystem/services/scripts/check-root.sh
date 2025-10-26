#!/bin/sh
# check-root.sh - ensure the container is not running as root.

CURRENT_UID="$(id -u)"

if [ "${CURRENT_UID}" -eq 0 ]; then
    YELLOW=$(printf '\033[1;33m')
    RESET=$(printf '\033[0m')
    >&2 printf "%s" "${YELLOW}"
    >&2 cat <<'EOF'
══════════════════════════════════════════════════════════════════════════════
⚠️  ATTENTION: NetAlertX is running as root (UID 0).

    This defeats every hardening safeguard built into the image. You just
    handed a high-value network monitoring appliance full control over your
    host. If an attacker compromises NetAlertX now, the entire machine goes
    with it.

    Run the container as the dedicated 'netalertx' user instead:
      * Keep the default USER in the image (20211:20211), or
      * In docker-compose.yml, remove any 'user:' override that sets UID 0.

	Note: As a courtesy, this special mode is only used to set the permissions
	of /app/db and /app/config to be owned by the netalertx user so future 
	runs work correctly.

    Bottom line: never run security tooling as root unless you are actively
    trying to get pwned.
══════════════════════════════════════════════════════════════════════════════
EOF
    >&2 printf "%s" "${RESET}"
    exit 1
fi

exit 0
