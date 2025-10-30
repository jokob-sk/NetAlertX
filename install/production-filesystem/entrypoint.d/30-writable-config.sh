#!/bin/sh

# 30-writable-config.sh: Verify read/write permissions for config and database files.
#
# This script ensures that the application can read from and write to the
# critical configuration and database files after startup.

# --- Color Codes ---
RED='\033[1;31m'
YELLOW='\033[1;33m'
RESET='\033[0m'

# --- Main Logic ---

# Define paths that need read-write access
READ_WRITE_PATHS="
${NETALERTX_CONFIG_FILE}
${NETALERTX_DB_FILE}
"

# --- Permission Validation ---

failures=0

# Check read-write paths for existence, read, and write access
for path in $READ_WRITE_PATHS; do
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
    elif [ ! -w "$path" ]; then
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