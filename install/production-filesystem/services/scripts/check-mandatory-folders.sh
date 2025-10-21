#!/bin/sh
# Initialize required directories and log files
# These must exist before services start to avoid permission/write errors
# TODO - improve with per-directory warning if creation fails
[ ! -d "${NETALERTX_PLUGINS_LOG}" ] && mkdir -p "${NETALERTX_PLUGINS_LOG}"
[ ! -d "${SYSTEM_SERVICES_RUN_LOG}" ] && mkdir -p "${SYSTEM_SERVICES_RUN_LOG}"
[ ! -d "${SYSTEM_SERVICES_RUN_TMP}" ] && mkdir -p "${SYSTEM_SERVICES_RUN_TMP}"
[ ! -f "${LOG_DB_IS_LOCKED}" ] && touch "${LOG_DB_IS_LOCKED}"
[ ! -f "${LOG_EXECUTION_QUEUE}" ] && touch "${LOG_EXECUTION_QUEUE}"