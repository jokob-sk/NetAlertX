#!/bin/bash
echo "Starting backend..."
cd "${NETALERTX_APP}" || exit
# Clear previous logs
echo '' > "${LOG_STDOUT}"
echo '' > "${LOG_STDERR}"
# Start the backend and redirect output
exec python3 -m server >> "${LOG_STDOUT}" 2>> "${LOG_STDERR}"
