#!/bin/sh
# first-run-check.sh - Checks and initializes configuration files on first run

# Check for app.conf and deploy if required
if [ ! -f ${NETALERTX_CONFIG}/app.conf ]; then
    mkdir -p ${NETALERTX_CONFIG}
    cp /app/back/app.conf ${NETALERTX_CONFIG}/app.conf
    CYAN='\033[1;36m'
    RESET='\033[0m'
    >&2 printf "%s" "${CYAN}"
    >&2 cat <<'EOF'
══════════════════════════════════════════════════════════════════════════════
🆕  First run detected. Default configuration written to /app/config/app.conf.

    Review your settings in the UI or edit the file directly before trusting
    this instance in production.
══════════════════════════════════════════════════════════════════════════════
EOF
    >&2 printf "%s" "${RESET}"
fi

