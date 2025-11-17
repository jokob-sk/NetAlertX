#!/bin/bash

# If cron_restart_backend exists in the file LOG_EXECUTION_QUEUE, then
# call the restart backend script and remove the line from the file
# and remove the entry

if grep -q "cron_restart_backend" "${LOG_EXECUTION_QUEUE}"; then
  /services/start-backend.sh &
  sed -i '/cron_restart_backend/d' "${LOG_EXECUTION_QUEUE}"
fi
