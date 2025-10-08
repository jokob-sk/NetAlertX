#!/bin/bash
export INSTALL_DIR=/app



# Check if there are any entries with cron_restart_backend
if grep -q "cron_restart_backend" "${LOG_EXECUTION_QUEUE}"; then
  # Restart python application using s6
  killall python3
  /services/start-backend.sh &
  echo 'done'

  # Remove all lines containing cron_restart_backend from the log file
  sed -i '/cron_restart_backend/d' "${LOG_EXECUTION_QUEUE}"
fi
