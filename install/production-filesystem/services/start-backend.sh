#!/bin/bash
echo "Starting backend..."
cd "${NETALERTX_APP}" || exit
# Change user to netalertx
export PYTHONPATH="${NETALERTX_SERVER}:${NETALERTX_APP}"

EXTRA_PARAMS=""
if [ -f /services/config/python/backend-extra-launch-parameters ]; then
    EXTRA_PARAMS=$(cat /services/config/python-backend-extra-launch-parameters)
fi

# Start the backend, teeing stdout and stderr to log files and the container's console
python3 ${EXTRA_PARAMS} -m server > >(tee /app/log/stdout.log) 2> >(tee /app/log/stderr.log >&2)
