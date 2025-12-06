#!/bin/sh
# first-run-check.sh - Checks and initializes configuration files on first run

# Check for app.conf and deploy if required
if [ ! -f "${NETALERTX_CONFIG}/app.conf" ]; then
    mkdir -p "${NETALERTX_CONFIG}" || {
        >&2 echo "ERROR: Failed to create config directory ${NETALERTX_CONFIG}"
        exit 1
    }
    install -m 600 -o ${NETALERTX_USER} -g ${NETALERTX_GROUP} /app/back/app.conf "${NETALERTX_CONFIG}/app.conf" || {
        >&2 echo "ERROR: Failed to deploy default config to ${NETALERTX_CONFIG}/app.conf"
        exit 2
    }
    RESET=$(printf '\033[0m')
    >&2 cat <<EOF
══════════════════════════════════════════════════════════════════════════════
🆕  First run detected. Default configuration written to ${NETALERTX_CONFIG}/app.conf.

    Review your settings in the UI or edit the file directly before trusting
    this instance in production.
══════════════════════════════════════════════════════════════════════════════
EOF

	>&2 printf "%s" "${RESET}"
fi

