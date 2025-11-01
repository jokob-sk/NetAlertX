#!/bin/sh

# 0-storage-permission.sh: Fix permissions if running as root.
#
# This script checks if running as root and fixes ownership and permissions
# for read-write paths to ensure proper operation.

# --- Color Codes ---
MAGENTA=$(printf '\033[1;35m')
RESET=$(printf '\033[0m')

# --- Main Logic ---

# Define paths that need read-write access
READ_WRITE_PATHS="
${NETALERTX_API}
${NETALERTX_LOG}
${SYSTEM_SERVICES_RUN}
${NETALERTX_CONFIG}
${NETALERTX_CONFIG_FILE}
${NETALERTX_DB}
${NETALERTX_DB_FILE}
"

# If running as root, fix permissions first
if [ "$(id -u)" -eq 0 ]; then
    >&2 printf "%s" "${MAGENTA}"
    >&2 cat <<'EOF'
══════════════════════════════════════════════════════════════════════════════
🚨 CRITICAL SECURITY ALERT: NetAlertX is running as ROOT (UID 0)! 🚨

    This configuration bypasses all built-in security hardening measures.
    You've granted a network monitoring application unrestricted access to
    your host system. A successful compromise here could jeopardize your
    entire infrastructure.

    IMMEDIATE ACTION REQUIRED: Switch to the dedicated 'netalertx' user:
      * Remove any 'user:' directive specifying UID 0 from docker-compose.yml or
      * switch to the default USER in the image (20211:20211)

    IMPORTANT: This corrective mode automatically adjusts ownership of
    /app/db and /app/config directories to the netalertx user, ensuring
    proper operation in subsequent runs.

    Remember: Never operate security-critical tools as root unless you're 
    actively trying to get pwned.

    https://github.com/jokob-sk/NetAlertX/blob/main/docs/docker-troubleshooting/running-as-root.md
══════════════════════════════════════════════════════════════════════════════
EOF
    >&2 printf "%s" "${RESET}"

    # Set ownership to netalertx user for all read-write paths
    chown -R netalertx ${READ_WRITE_PATHS}

    # Set directory and file permissions for all read-write paths
    find ${READ_WRITE_PATHS} -type d -exec chmod u+rwx {} + 2>/dev/null
    find ${READ_WRITE_PATHS} -type f -exec chmod u+rw {} + 2>/dev/null
    echo Permissions fixed for read-write paths. Please restart the container as user 20211.
    sleep infinity & wait $!; exit 211
fi



