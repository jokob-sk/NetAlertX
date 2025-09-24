#!/bin/bash
echo "Starting backend..."
cd "${NETALERTX_APP}" || exit
export PYTHONPATH="${NETALERTX_SERVER}"
# Start the backend in the foreground, output will be handled by the container's logging driver
python3 -m server
