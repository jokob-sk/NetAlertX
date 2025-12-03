#!/bin/sh
# override-config.sh - Handles APP_CONF_OVERRIDE environment variable

OVERRIDE_FILE="${NETALERTX_CONFIG}/app_conf_override.json"

# Ensure config directory exists
mkdir -p "$(dirname "$NETALERTX_CONFIG")" || {
    >&2 echo "ERROR: Failed to create config directory $(dirname "$NETALERTX_CONFIG")"
    exit 1
}

# Remove old override file if it exists
rm -f "$OVERRIDE_FILE"

# Check if APP_CONF_OVERRIDE is set
if [ -z "$APP_CONF_OVERRIDE" ]; then
    >&2 echo "APP_CONF_OVERRIDE is not set. Skipping override config file creation."
else
    # Save the APP_CONF_OVERRIDE env variable as a JSON file
    echo "$APP_CONF_OVERRIDE" > "$OVERRIDE_FILE" || {
        >&2 echo "ERROR: Failed to write override config to $OVERRIDE_FILE"
        exit 2
    }

    RESET=$(printf '\033[0m')
    >&2 cat <<EOF
══════════════════════════════════════════════════════════════════════════════
📝  APP_CONF_OVERRIDE detected. Configuration written to $OVERRIDE_FILE.

    Make sure the JSON content is correct before starting the application.
══════════════════════════════════════════════════════════════════════════════
EOF

    >&2 printf "%s" "${RESET}"
fi
