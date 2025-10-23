#!/bin/sh

# check-0-permissions.sh: Verify file system permissions for critical paths.
#
# This script ensures that the application has the necessary read and write
# permissions for its operational directories. It distinguishes between running
# as root (user 0) and a non-privileged user.
#
# As root, it will proactively fix ownership and permissions.
# As a non-root user, it will only warn about issues.

# --- Color Codes ---
RED='\033[1;31m'
YELLOW='\033[1;33m'
RESET='\033[0m'

# --- Main Logic ---

# Define paths that need read-only access
READ_ONLY_PATHS="
${NETALERTX_APP}
${NETALERTX_SERVER}
${NETALERTX_FRONT}
${SYSTEM_SERVICES_CONFIG}
${VIRTUAL_ENV}
"

# Define paths that need read-write access
READ_WRITE_PATHS="
${NETALERTX_API}
${NETALERTX_LOG}
${SYSTEM_SERVICES_RUN}
${NETALERTX_CONFIG}
$(dirname "${NETALERTX_DB_FILE}")
"

# If running as root, fix permissions first
if [ "$(id -u)" -eq 0 ]; then
    echo "Running as root. Ensuring correct ownership and permissions..."

    # Set ownership to netalertx user and group for all read-write paths
    chown -R netalertx:netalertx ${READ_WRITE_PATHS}

    # Set directory and file permissions for all read-write paths
    find ${READ_WRITE_PATHS} -type d -exec chmod 700 {} +
    find ${READ_WRITE_PATHS} -type f -exec chmod 600 {} +
fi

# --- Permission Validation ---

failures=0

# Check all paths
ALL_PATHS="${READ_ONLY_PATHS} ${READ_WRITE_PATHS}"
for path in $ALL_PATHS; do
    if [ ! -e "$path" ]; then
        failures=1
        >&2 printf "%s" "${RED}"
        >&2 cat <<EOF
══════════════════════════════════════════════════════════════════════════════
❌ CRITICAL: Path does not exist.

   The required path "${path}" could not be found. The application
   cannot start without its complete directory structure.
══════════════════════════════════════════════════════════════════════════════
EOF
        >&2 printf "%s" "${RESET}"
    elif [ ! -r "$path" ]; then
        failures=1
        >&2 printf "%s" "${YELLOW}"
        >&2 cat <<EOF
══════════════════════════════════════════════════════════════════════════════
⚠️  ATTENTION: Read permission denied.

    The application cannot read from "${path}". This will cause
    unpredictable errors. Please correct the file system permissions.
══════════════════════════════════════════════════════════════════════════════
EOF
        >&2 printf "%s" "${RESET}"
    fi
done

# Check read-write paths specifically for write access
for path in $READ_WRITE_PATHS; do
    if [ -e "$path" ] && [ ! -w "$path" ]; then
        failures=1
        >&2 printf "%s" "${YELLOW}"
        >&2 cat <<EOF
══════════════════════════════════════════════════════════════════════════════
⚠️  ATTENTION: Write permission denied.

    The application cannot write to "${path}". This will prevent it from
    saving data, logs, or configuration.

    To fix this automatically, restart the container with root privileges
    (e.g., remove the "user:" directive in your Docker Compose file).
══════════════════════════════════════════════════════════════════════════════
EOF
        >&2 printf "%s" "${RESET}"
    fi
done

# If there were any failures, exit
if [ "$failures" -ne 0 ]; then
    exit 1
fi



