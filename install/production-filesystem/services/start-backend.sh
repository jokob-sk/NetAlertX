#!/bin/bash
set -euo pipefail

echo "Starting backend..."
cd "${NETALERTX_APP}" || exit 1
# Change user to netalertx
export PYTHONPATH="${NETALERTX_SERVER}:${NETALERTX_APP}"

EXTRA_PARAMS=""
if [ -f /services/config/python/backend-extra-launch-parameters ]; then
    EXTRA_PARAMS=$(cat /services/config/python/backend-extra-launch-parameters)
fi

backend_pid=""

cleanup() {
    status=$?
    echo "Backend stopped! (exit ${status})"
}

forward_signal() {
    if [[ -n "${backend_pid}" ]]; then
        kill -TERM "${backend_pid}" 2>/dev/null || true
    fi
}

trap cleanup EXIT
trap forward_signal INT TERM

# Start the backend, teeing stdout and stderr to log files and the container's console
python3 ${EXTRA_PARAMS} -m server > >(tee /app/log/stdout.log) 2> >(tee /app/log/stderr.log >&2) &
backend_pid=$!

wait "${backend_pid}"
exit $?
