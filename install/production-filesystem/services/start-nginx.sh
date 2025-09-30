#!/bin/bash
LOG_DIR=${NETALERTX_APP}
RUN_DIR=${SYSTEM_SERVICES_RUN}
TMP_DIR=${SYSTEM_SERVICES_RUN_TMP}
NGINX_CONFIG_FILE=${NGINX_CONFIG_FILE}

# Create directories if they don't exist
mkdir -p "${LOG_DIR}" "${RUN_DIR}" "${TMP_DIR}"

# Execute nginx with overrides
exec nginx \
    -p "${RUN_DIR}/" \
    -c "${NGINX_CONFIG_FILE}" \
    -g "error_log ${LOG_DIR}/nginx.error.log; pid ${RUN_DIR}/nginx.pid; daemon off;"