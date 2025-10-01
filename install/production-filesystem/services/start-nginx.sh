#!/bin/bash
set -euo pipefail

LOG_DIR=${NETALERTX_APP}
RUN_DIR=${SYSTEM_SERVICES_RUN}
TMP_DIR=${SYSTEM_SERVICES_RUN_TMP}

# Create directories if they don't exist
mkdir -p "${LOG_DIR}" "${RUN_DIR}" "${TMP_DIR}"

echo "Starting nginx..."

nginx_pid=""

cleanup() {
    status=$?
    echo "nginx stopped! (exit ${status})"
}

forward_signal() {
    if [[ -n "${nginx_pid}" ]]; then
        kill -TERM "${nginx_pid}" 2>/dev/null || true
    fi
}

trap cleanup EXIT
trap forward_signal INT TERM

# Execute nginx with overrides
nginx \
    -p "${RUN_DIR}/" \
    -c "${SYSTEM_NGINX_CONFIG_FILE}" \
    -g "error_log ${NETALERTX_LOG}/nginx-error.log; pid ${RUN_DIR}/nginx.pid; daemon off;" &
nginx_pid=$!

wait "${nginx_pid}"
exit $?