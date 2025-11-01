#!/bin/sh
# Initialize required directories and log files
# These must exist before services start to avoid permission/write errors

check_mandatory_folders() {
    # Check and create plugins log directory
    if [ ! -d "${NETALERTX_PLUGINS_LOG}" ]; then
        echo "    * Creating Plugins log."
        if ! mkdir -p "${NETALERTX_PLUGINS_LOG}"; then
            echo "Error: Failed to create plugins log directory: ${NETALERTX_PLUGINS_LOG}"
            return 1
        fi
    fi

    # Check and create system services run log directory
    if [ ! -d "${SYSTEM_SERVICES_RUN_LOG}" ]; then
        echo "    * Creating System services run log."
        if ! mkdir -p "${SYSTEM_SERVICES_RUN_LOG}"; then
            echo "Error: Failed to create system services run log directory: ${SYSTEM_SERVICES_RUN_LOG}"
            return 1
        fi
    fi

    # Check and create system services run tmp directory
    if [ ! -d "${SYSTEM_SERVICES_RUN_TMP}" ]; then
        echo "    * Creating System services run tmp."
        if ! mkdir -p "${SYSTEM_SERVICES_RUN_TMP}"; then
            echo "Error: Failed to create system services run tmp directory: ${SYSTEM_SERVICES_RUN_TMP}"
            return 1
        fi
    fi

    # Check and create DB locked log file
    if [ ! -f "${LOG_DB_IS_LOCKED}" ]; then
        echo "    * Creating DB locked log."
        if ! touch "${LOG_DB_IS_LOCKED}"; then
            echo "Error: Failed to create DB locked log file: ${LOG_DB_IS_LOCKED}"
            return 1
        fi
    fi

    # Check and create execution queue log file
    if [ ! -f "${LOG_EXECUTION_QUEUE}" ]; then
        echo "    * Creating Execution queue log."
        if ! touch "${LOG_EXECUTION_QUEUE}"; then
            echo "Error: Failed to create execution queue log file: ${LOG_EXECUTION_QUEUE}"
            return 1
        fi
    fi
}

# Run the function
check_mandatory_folders