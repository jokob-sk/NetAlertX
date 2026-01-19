#!/bin/sh
# Initialize required directories and log files
# These must exist before services start to avoid permission/write errors
# This script is intended to enhance observability of system startup issues.



is_tmp_path() {
    case "$1" in
        /tmp/*|/tmp) return 0 ;;
        *) return 1 ;;
    esac
}

warn_tmp_skip() {
    echo "Warning: Unable to create $2 at $1 (tmpfs not writable with current capabilities)."
}

ensure_dir() {
	# When creating as the user running the services, we ensure correct ownership and access
    path="$1"
    label="$2"
    # Fix permissions if directory exists but is unreadable/unwritable
	# It's expected chown is done as root during root-entrypoint, and now we own the files
	# here we will set correct access.
    if [ -d "${path}" ]; then
        chmod u+rwX "${path}" 2>/dev/null || true
    fi
    if ! mkdir -p "${path}" 2>/dev/null; then
        if is_tmp_path "${path}"; then
            warn_tmp_skip "${path}" "${label}"
            return 0
        fi
        echo "Error: Failed to create ${label}: ${path}"
        return 1
    fi
    chmod 700 "${path}" 2>/dev/null || true
}

ensure_file() {
    path="$1"
    label="$2"
	# When we touch as the user running the services, we ensure correct ownership
    if ! touch "${path}" 2>/dev/null; then
        if is_tmp_path "${path}"; then
            warn_tmp_skip "${path}" "${label}"
            return 0
        fi
        echo "Error: Failed to create ${label}: ${path}"
        return 1
    fi
}

check_mandatory_folders() {
    # Base volatile directories live on /tmp mounts and must always exist
    if [ ! -d "${NETALERTX_LOG}" ]; then
        echo "    * Creating NetAlertX log directory."
        ensure_dir "${NETALERTX_LOG}" "log directory" || return 1
    fi

    if [ ! -d "${NETALERTX_API}" ]; then
        echo "    * Creating NetAlertX API cache."
        ensure_dir "${NETALERTX_API}" "API cache directory" || return 1
    fi

    if [ ! -d "${SYSTEM_SERVICES_RUN}" ]; then
        echo "    * Creating System services runtime directory."
        ensure_dir "${SYSTEM_SERVICES_RUN}" "System services runtime directory" || return 1
    fi

    if [ ! -d "${SYSTEM_SERVICES_ACTIVE_CONFIG}" ]; then
        echo "    * Creating nginx active configuration directory."
        ensure_dir "${SYSTEM_SERVICES_ACTIVE_CONFIG}" "nginx active configuration directory" || return 1
    fi

    # Check and create plugins log directory
    if [ ! -d "${NETALERTX_PLUGINS_LOG}" ]; then
        echo "    * Creating Plugins log."
        ensure_dir "${NETALERTX_PLUGINS_LOG}" "plugins log directory" || return 1
    fi

    # Check and create system services run log directory
    if [ ! -d "${SYSTEM_SERVICES_RUN_LOG}" ]; then
        echo "    * Creating System services run log."
        ensure_dir "${SYSTEM_SERVICES_RUN_LOG}" "system services run log directory" || return 1
    fi

    # Check and create system services run tmp directory
    if [ ! -d "${SYSTEM_SERVICES_RUN_TMP}" ]; then
        echo "    * Creating System services run tmp."
        ensure_dir "${SYSTEM_SERVICES_RUN_TMP}" "system services run tmp directory" || return 1
    fi

    # Check and create DB locked log file
    if [ ! -f "${LOG_DB_IS_LOCKED}" ]; then
        echo "    * Creating DB locked log."
        ensure_file "${LOG_DB_IS_LOCKED}" "DB locked log file" || return 1
    fi

    # Check and create execution queue log file
    if [ ! -f "${LOG_EXECUTION_QUEUE}" ]; then
        echo "    * Creating Execution queue log."
        ensure_file "${LOG_EXECUTION_QUEUE}" "execution queue log file" || return 1
    fi
}

# Create the folders and files.
# Create a log message for observability if any fail.
check_mandatory_folders